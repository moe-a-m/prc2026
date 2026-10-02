"""LightGBM taxi-out model: month hold-out validation, final fit and prediction.

  python -m prc.models.gbm validate --config configs/gbm.yaml
  python -m prc.models.gbm train    --config configs/gbm.yaml   # fit on all 2025
  python -m prc.models.gbm predict  --config configs/gbm.yaml   # ranking predictions -> pred_ table + parquet
"""
import argparse
import hashlib
import json
import time

import lightgbm as lgb
import numpy as np
import pandas as pd
import yaml

from prc import db, validate as V
from prc.paths import MODELS, ROOT

EVAL_COLS = ["mvt_id", "ds", "month", "airport", "y", "runway", "stand"] + V.FLAG_COLS


def load_config(path):
    """YAML config. `base: <path>` inherits another config; `drop_numeric`, `drop_categorical` and
    `drop_te` (list of key lists) remove inputs from it (feature-family ablations); `add_numeric` adds inputs."""
    text = (ROOT / path).read_text() if not str(path).startswith("/") else open(path).read()
    cfg = yaml.safe_load(text)
    hashed = text
    if "base" in cfg:
        base = load_config(cfg.pop("base"))
        hashed = base.pop("config_hash") + text
        # the parent's add/drop lists are already applied to its numeric/categorical/TE lists: don't re-apply
        for k in ("add_numeric", "drop_numeric", "drop_categorical", "drop_te"):
            base.pop(k, None)
        extra = base.get("extra_tables", []) + [t for t in cfg.get("extra_tables", []) if t not in base.get("extra_tables", [])]
        cfg = {**base, **cfg, "extra_tables": extra}
    cfg["numeric"] = [c for c in cfg["numeric"] + cfg.get("add_numeric", []) if c not in cfg.get("drop_numeric", [])]
    cfg["categorical"] = [c for c in cfg["categorical"] if c not in cfg.get("drop_categorical", [])]
    cfg["target_encodings"] = [k for k in cfg["target_encodings"] if k not in cfg.get("drop_te", [])]
    cfg["config_hash"] = hashlib.sha256(hashed.encode()).hexdigest()[:12]
    return cfg


def load_frame(weather: bool = False, extra: tuple = ()) -> pd.DataFrame:
    """feat_dep joined with optional side tables (feat_dep_wx when weather, plus `extra` table names)."""
    con = db.connect(read_only=True)
    tables = (["feat_dep_wx"] if weather else []) + list(extra)
    sql = "SELECT * FROM feat_dep " + " ".join(f"LEFT JOIN {t} USING (mvt_id)" for t in tables) + " ORDER BY mvt_id"
    df = con.sql(sql).df()
    con.close()
    df["ap_runway"] = df.airport + "_" + df.runway.fillna("NA")
    df["ap_stand"] = df.airport + "_" + df.stand.fillna("NA")
    df["month"] = pd.to_datetime(df.month)
    return df


def target_encode(df: pd.DataFrame, fit_mask: np.ndarray, keys_list, group: pd.Series, q: float | None = None) -> pd.DataFrame:
    """Median y (or quantile q) and count per key. Rows in fit_mask get leave-one-group(month)-out values; other
    rows get values from all fit rows. Groups are months, so no row ever sees its own month's targets."""
    out = pd.DataFrame(index=df.index)
    fit = df[fit_mask]
    stat = "median" if q is None else (lambda s: s.quantile(q))
    for keys in keys_list:
        name = ("te_" if q is None else f"te_q{int(round(q * 100)):02d}_") + "_".join(keys)
        med = np.full(len(df), np.nan)
        cnt = np.zeros(len(df))
        # rows outside the fit set: statistics from all fit rows
        g = fit.groupby(keys, dropna=False).y.agg([stat, "size"]).reset_index()
        g.columns = keys + ["median", "size"]
        m = df.loc[~fit_mask, keys].merge(g, on=keys, how="left")
        med[~fit_mask] = m["median"].to_numpy()
        cnt[~fit_mask] = m["size"].fillna(0).to_numpy()
        # fit rows: leave one month out
        for mo in group[fit_mask].unique():
            src = fit_mask & (group != mo).to_numpy()
            dst = fit_mask & (group == mo).to_numpy()
            g = df[src].groupby(keys, dropna=False).y.agg([stat, "size"]).reset_index()
            g.columns = keys + ["median", "size"]
            m = df.loc[dst, keys].merge(g, on=keys, how="left")
            med[dst] = m["median"].to_numpy()
            cnt[dst] = m["size"].fillna(0).to_numpy()
        out[name] = med
        if q is None:
            out[name + "_n"] = cnt
    return out


def design(df, cfg, fit_mask):
    te = [target_encode(df, fit_mask, cfg["target_encodings"], df.month)]
    for q, keys_list in (cfg.get("te_quantiles") or {}).items():
        te.append(target_encode(df, fit_mask, keys_list, df.month, q=float(q)))
    X = pd.concat([df[cfg["numeric"]].astype(float)] + te, axis=1)
    for c in cfg["categorical"]:
        X[c] = df[c].astype("category")
    return X


class _CatModel:
    """Thin wrapper so CatBoost and LightGBM share fit/predict/importance/save calls."""

    def __init__(self, cfg, seed):
        from catboost import CatBoostRegressor
        self.cats = cfg["categorical"]
        self.m = CatBoostRegressor(iterations=cfg["num_boost_round"], random_seed=seed,
                                   allow_writing_files=False, **cfg["params"])

    def _prep(self, X):
        X = X.copy()
        for c in self.cats:
            X[c] = X[c].astype(str).replace({"nan": "NA"})
        return X

    def fit(self, X, y):
        from catboost import Pool
        self.cols = list(X.columns)
        self.m.fit(Pool(self._prep(X), y, cat_features=self.cats))
        return self

    def predict(self, X):
        return self.m.predict(self._prep(X))

    def feature_importance(self, kind="gain"):
        return self.m.get_feature_importance()

    def save_model(self, path):
        self.m.save_model(path.replace(".txt", ".cbm"))


def fit(X, y, cfg, seed):
    if cfg.get("model", "lightgbm") == "catboost":
        return _CatModel(cfg, seed).fit(X, y)
    params = dict(cfg["params"], seed=seed)
    ds = lgb.Dataset(X, y, categorical_feature=cfg["categorical"], free_raw_data=False)
    return lgb.train(params, ds, num_boost_round=cfg["num_boost_round"])


def fit_predict(df, X, fit_mask, pred_mask, cfg, seed):
    """One global model, or one model per airport when cfg['per_airport'] (stops patterns that only hold at one
    airport — e.g. LIRF schedule echoes — from leaking into others, EXP-022). Returns (pred, last_model)."""
    y = df.y.to_numpy(float)
    if not cfg.get("per_airport"):
        b = fit(X[fit_mask], y[fit_mask], cfg, seed)
        return b.predict(X[pred_mask]), b
    out = np.full(len(df), np.nan)
    for a in sorted(df.airport.unique()):
        am = (df.airport == a).to_numpy()
        if not (pred_mask & am).any():
            continue
        b = fit(X[fit_mask & am], y[fit_mask & am], cfg, seed)
        out[pred_mask & am] = b.predict(X[pred_mask & am])
    return out[pred_mask], b


def validate(cfg, seeds=None):
    t0 = time.time()
    df = load_frame(cfg.get("weather", False), tuple(cfg.get("extra_tables", [])))
    print(f"  loaded {len(df)} rows ({time.time() - t0:.0f}s)", flush=True)
    tr_all = (df.ds == "train").to_numpy()
    seeds = seeds or [cfg["seed"]]
    results, per_seed, importance = {}, {}, {}
    for fold, trm, vam in V.folds(df.month.where(tr_all)):
        trm, vam = trm & tr_all, vam & tr_all
        t0 = time.time()
        X = design(df, cfg, trm)
        print(f"  {fold} design ({time.time() - t0:.0f}s)", flush=True)
        preds = []
        for s in seeds:
            t0 = time.time()
            p, b = fit_predict(df, X, trm, vam, cfg, s)
            preds.append(p)
            per_seed.setdefault(fold, []).append(V.rmse(df.y[vam], p))
            print(f"  {fold} seed={s} rmse={per_seed[fold][-1]:.2f} ({time.time() - t0:.0f}s)", flush=True)
        va = df.loc[vam, EVAL_COLS].copy()
        va["pred"] = np.mean(preds, axis=0)
        results[fold] = va
        importance[fold] = pd.Series(b.feature_importance("gain"), index=X.columns).sort_values(ascending=False)
    meta = {"data": V.data_version(), "git": V.git_sha(), "config": cfg["config_hash"], "seeds": seeds,
            "per_seed_rmse": {k: [round(v, 2) for v in vs] for k, vs in per_seed.items()},
            "params": json.dumps(cfg["params"]), "num_boost_round": cfg["num_boost_round"]}
    text = V.report_md(cfg["exp_id"], cfg["title"], results, meta)
    imp = importance["jul"]
    text += "\n## Feature importance (gain, Jul fold, last seed)\n\n" + (imp / imp.sum()).round(4).to_frame("gain_share").to_markdown() + "\n"
    V.write_report(cfg["exp_id"], text)
    oof_dir = MODELS / "oof"  # row-level predictions stay out of git (models/ is ignored)
    oof_dir.mkdir(parents=True, exist_ok=True)
    for name, va in results.items():
        va.to_parquet(oof_dir / f"{cfg['exp_id']}_{name}.parquet")
    r = {k: V.rmse(v.y, v.pred) for k, v in results.items()}
    r["combined"] = V.rmse(pd.concat(results.values()).y, pd.concat(results.values()).pred)
    print(cfg["exp_id"], {k: round(v, 2) for k, v in r.items()})
    return r, results


def train_and_predict(cfg, seeds=None):
    """Fit on all 2025 (target encodings leave-one-month-out), predict the ranking set, save models + preds."""
    df = load_frame(cfg.get("weather", False), tuple(cfg.get("extra_tables", [])))
    tr = (df.ds == "train").to_numpy()
    rk = (df.ds == "rank").to_numpy()
    X = design(df, cfg, tr)
    out = MODELS / cfg["exp_id"]
    out.mkdir(parents=True, exist_ok=True)
    seeds = seeds or [cfg["seed"]]
    preds = []
    for s in seeds:
        t0 = time.time()
        p, b = fit_predict(df, X, tr, rk, cfg, s)
        if not cfg.get("per_airport"):
            b.save_model(str(out / f"seed_{s}.txt"))
        preds.append(p)
        print(f"  final seed={s} ({time.time() - t0:.0f}s)", flush=True)
    pred = pd.DataFrame({"mvt_id": df.mvt_id[rk].to_numpy(), "pred": np.mean(preds, axis=0)})
    pred.to_parquet(out / "pred_rank.parquet", index=False)
    (out / "meta.json").write_text(json.dumps({"data": V.data_version(), "git": V.git_sha(), "seeds": seeds,
                                               "config": cfg["config_hash"]}, indent=1))
    print(f"wrote {out / 'pred_rank.parquet'} ({len(pred)} rows)")
    return pred


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["validate", "train", "predict"])
    ap.add_argument("--config", default="configs/gbm.yaml")
    ap.add_argument("--seeds", type=int, nargs="*")
    ap.add_argument("--rounds", type=int, help="override num_boost_round (quick runs)")
    ap.add_argument("--exp-id", help="override exp_id")
    a = ap.parse_args()
    cfg = load_config(a.config)
    if a.rounds:
        cfg["num_boost_round"] = a.rounds
    if a.exp_id:
        cfg["exp_id"] = a.exp_id
    if a.cmd == "validate":
        validate(cfg, a.seeds)
    elif a.cmd == "train":
        train_and_predict(cfg, a.seeds)
    else:  # predictions are written by `train`; `predict` builds the submission file from them
        from prc import submit
        submit.build(MODELS / cfg["exp_id"] / "pred_rank.parquet")
