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
    text = (ROOT / path).read_text() if not str(path).startswith("/") else open(path).read()
    cfg = yaml.safe_load(text)
    cfg["config_hash"] = hashlib.sha256(text.encode()).hexdigest()[:12]
    return cfg


def load_frame() -> pd.DataFrame:
    con = db.connect(read_only=True)
    df = con.sql("SELECT * FROM feat_dep ORDER BY mvt_id").df()
    con.close()
    df["ap_runway"] = df.airport + "_" + df.runway.fillna("NA")
    df["ap_stand"] = df.airport + "_" + df.stand.fillna("NA")
    df["month"] = pd.to_datetime(df.month)
    return df


def target_encode(df: pd.DataFrame, fit_mask: np.ndarray, keys_list, group: pd.Series) -> pd.DataFrame:
    """Median y and count per key. Rows in fit_mask get leave-one-group(month)-out values; other rows
    get values from all fit rows. Groups are months, so no row ever sees its own month's targets."""
    out = pd.DataFrame(index=df.index)
    fit = df[fit_mask]
    for keys in keys_list:
        name = "te_" + "_".join(keys)
        med = np.full(len(df), np.nan)
        cnt = np.zeros(len(df))
        # rows outside the fit set: statistics from all fit rows
        g = fit.groupby(keys, dropna=False).y.agg(["median", "size"]).reset_index()
        m = df.loc[~fit_mask, keys].merge(g, on=keys, how="left")
        med[~fit_mask] = m["median"].to_numpy()
        cnt[~fit_mask] = m["size"].fillna(0).to_numpy()
        # fit rows: leave one month out
        for mo in group[fit_mask].unique():
            src = fit_mask & (group != mo).to_numpy()
            dst = fit_mask & (group == mo).to_numpy()
            g = df[src].groupby(keys, dropna=False).y.agg(["median", "size"]).reset_index()
            m = df.loc[dst, keys].merge(g, on=keys, how="left")
            med[dst] = m["median"].to_numpy()
            cnt[dst] = m["size"].fillna(0).to_numpy()
        out[name] = med
        out[name + "_n"] = cnt
    return out


def design(df, cfg, fit_mask):
    te = target_encode(df, fit_mask, cfg["target_encodings"], df.month)
    X = pd.concat([df[cfg["numeric"]].astype(float), te], axis=1)
    for c in cfg["categorical"]:
        X[c] = df[c].astype("category")
    return X


def fit(X, y, cfg, seed):
    params = dict(cfg["params"], seed=seed)
    ds = lgb.Dataset(X, y, categorical_feature=cfg["categorical"], free_raw_data=False)
    return lgb.train(params, ds, num_boost_round=cfg["num_boost_round"])


def validate(cfg, seeds=None):
    t0 = time.time()
    df = load_frame()
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
            b = fit(X[trm], df.y[trm].to_numpy(float), cfg, s)
            p = b.predict(X[vam])
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
    df = load_frame()
    tr = (df.ds == "train").to_numpy()
    rk = (df.ds == "rank").to_numpy()
    X = design(df, cfg, tr)
    out = MODELS / cfg["exp_id"]
    out.mkdir(parents=True, exist_ok=True)
    seeds = seeds or [cfg["seed"]]
    preds = []
    for s in seeds:
        t0 = time.time()
        b = fit(X[tr], df.y[tr].to_numpy(float), cfg, s)
        b.save_model(str(out / f"seed_{s}.txt"))
        preds.append(b.predict(X[rk]))
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
