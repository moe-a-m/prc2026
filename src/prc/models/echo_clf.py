"""Schedule-echo classifier hedge for LIRF NM-unmatched departures 1–6 h late (M-032).

Population: airport LIRF, no NM match, take-off 1–6 h after schedule (below the M-026 bands). Label: echo =
|y − d_sched| ≤ ECHO_TOL_S (the airport off-block copies the schedule). A month-held-out gradient-boosting classifier on
label-free inputs gives p_echo; the hedge is the two-point conditional mean
    h = p_echo · d_sched + (1 − p_echo) · m_normal        m_normal = mean y of non-echo rows of the training months
and the final prediction moves toward it with one least-squares weight w ∈ [0, 1], cross-fitted between the hold-out
months (as M-019 / M-028):  pred' = pred + w · (h − pred).
Inputs (reports/references cleaning_investigation_2026-10-03.md §2): d_sched, take-off hour, schedule minute, take-off
on second 0, carrier prefix, flight-number class (null / mangled / normal), numeric stand, winter flag.

  python -m prc.models.echo_clf eval --base EXP-101 --exp-id EXP-102
  python -m prc.models.echo_clf final --pred models/EXP-101/pred_rank.parquet --out models/EXP-102/pred_rank.parquet --from-report EXP-102
"""
import argparse
import json
import re

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from prc import db, validate as V
from prc.paths import MODELS, REPORTS

AIRPORT = "LIRF"
LO_S, HI_S = 3600, 21600
ECHO_TOL_S = 120          # as M-026
MIN_CARRIER = 25
WINTER = {1, 2, 3, 11, 12}
FEATURES = ["d_sched", "hour", "sched_min", "mvt_sec0", "carrier", "fn_class", "stand_num", "winter"]
CATEGORICAL = ["carrier", "fn_class"]


def fn_class(flight) -> str:
    """'null', 'mangled' (ICAO prefix followed by a repeat of its last 1–2 letters, e.g. NOSOS739, WZZZ8068), 'normal'."""
    if flight is None or (isinstance(flight, float) and np.isnan(flight)) or not str(flight).strip():
        return "null"
    s = str(flight).strip().upper()
    p, rest = s[:3], s[3:]
    if re.fullmatch(r"[A-Z]{3}", p) and (re.match(rf"{p[1:]}\d", rest) or re.match(rf"{p[2:]}\d", rest)):
        return "mangled"
    return "normal"


def frame() -> pd.DataFrame:
    con = db.connect(read_only=True)
    d = con.sql(f"""
        SELECT mvt_id, ds, month, y, flight_mvt, stand, t_mvt, t_sched, epoch(t_mvt) - epoch(t_sched) AS d_sched
        FROM clean_dep
        WHERE airport = '{AIRPORT}' AND f_no_nm_match AND epoch(t_mvt) - epoch(t_sched) >= {LO_S}
          AND epoch(t_mvt) - epoch(t_sched) < {HI_S}""").df()
    con.close()
    t_mvt, t_sched = pd.to_datetime(d.t_mvt), pd.to_datetime(d.t_sched)
    d["month"] = pd.to_datetime(d.month)
    d["hour"] = t_mvt.dt.hour
    d["sched_min"] = t_sched.dt.minute
    d["mvt_sec0"] = (t_mvt.dt.second == 0).astype(int)
    d["carrier"] = d.flight_mvt.fillna("").str.upper().str.extract(r"^([A-Z]{3})", expand=False).fillna("?")
    d["fn_class"] = d.flight_mvt.map(fn_class)
    d["stand_num"] = pd.to_numeric(d.stand, errors="coerce")
    d["winter"] = d.month.dt.month.isin(WINTER).astype(int)
    d["echo"] = (d.y - d.d_sched).abs() <= ECHO_TOL_S
    return d


def _design(train: pd.DataFrame, rows: pd.DataFrame) -> pd.DataFrame:
    """Integer codes for categoricals from the training rows (rare carriers → 'other'; unseen → NaN = missing)."""
    X = rows[FEATURES].copy()
    keep = train.carrier.value_counts()
    keep = set(keep[keep >= MIN_CARRIER].index)
    for c in CATEGORICAL:
        tr_vals = train[c].where(train[c].isin(keep), "other") if c == "carrier" else train[c]
        codes = {v: i for i, v in enumerate(sorted(tr_vals.unique()))}
        vals = X[c].where(X[c].isin(keep), "other") if c == "carrier" else X[c]
        X[c] = vals.map(codes).astype(float)
    return X


def fit_predict(train: pd.DataFrame, rows: pd.DataFrame):
    """Classifier and normal-regime mean from `train` (labelled rows); returns (p_echo, hedge) for `rows`."""
    clf = HistGradientBoostingClassifier(max_depth=3, max_iter=100, learning_rate=0.05, random_state=0,
                                         categorical_features=[FEATURES.index(c) for c in CATEGORICAL])
    clf.fit(_design(train, train), train.echo.astype(int))
    p = clf.predict_proba(_design(train, rows))[:, 1]
    m_normal = float(train.y[~train.echo].mean())
    return p, p * rows.d_sched.to_numpy(float) + (1 - p) * m_normal


def _weight(y, pred, h) -> float:
    d, r = h - pred, y - pred
    return float(np.clip((d * r).sum() / (d * d).sum(), 0, 1)) if (d * d).sum() > 0 else 0.0


def evaluate(base: str, exp_id: str):
    d = frame()
    tr = d[d.ds == "train"]
    parts, folds = {}, {}
    for fold, m in V.HOLDOUTS.items():
        va = pd.read_parquet(MODELS / "oof" / f"{base}_{fold}.parquet")
        pop = tr[tr.month == pd.Timestamp(m)].merge(va[["mvt_id", "pred"]], on="mvt_id")
        pop["p_echo"], pop["hedge"] = fit_predict(tr[tr.month != pd.Timestamp(m)], pop)
        parts[fold], folds[fold] = pop, va
    names = list(parts)
    assert len(names) == 2, "rejected method, cross-fit written for two hold-outs only (PRC_HOLDOUTS=jan,jul)"
    results, rows, ws = {}, [], {}
    for i, fold in enumerate(names):
        other = parts[names[1 - i]]
        w = _weight(other.y.to_numpy(float), other.pred.to_numpy(float), other.hedge.to_numpy(float))
        ws[fold] = w
        pop = parts[fold]
        new = pop.pred + w * (pop.hedge - pop.pred)
        va = folds[fold].copy()
        before = va.pred.to_numpy().copy()
        va = va.merge(pd.DataFrame({"mvt_id": pop.mvt_id, "new": new}), on="mvt_id", how="left")
        va["pred"] = va.new.fillna(va.pred)
        results[fold] = va.drop(columns="new")
        ch = va.pred.to_numpy() != before
        auc = None
        if pop.echo.nunique() == 2:
            from sklearn.metrics import roc_auc_score
            auc = round(float(roc_auc_score(pop.echo.astype(int), pop.p_echo)), 3)
        rows.append({"fold": fold, "n_pop": len(pop), "echo_rate": round(float(pop.echo.mean()), 3), "auc": auc,
                     "w (fit on other month)": round(w, 3), "n_changed": int(ch.sum()),
                     "rmse_pop_before": round(V.rmse(pop.y, pop.pred), 1), "rmse_pop_after": round(V.rmse(pop.y, new), 1),
                     "rmse_before": round(V.rmse(va.y, before), 2), "rmse_after": round(V.rmse(va.y, va.pred), 2)})
    allp = pd.concat(parts.values())
    w_final = _weight(allp.y.to_numpy(float), allp.pred.to_numpy(float), allp.hedge.to_numpy(float))
    meta = {"base": base, "data": V.data_version(), "git": V.git_sha(),
            "rule": f"M-032: {AIRPORT} NM-unmatched, d_sched in [{LO_S}, {HI_S}) s, echo tol {ECHO_TOL_S} s, "
                    f"HistGradientBoostingClassifier(depth 3, 100 iter, lr 0.05, seed 0) month-held-out, cross-fitted weight",
            "final_model": json.dumps({"w": w_final})}
    text = V.report_md(exp_id, f"Schedule-echo classifier hedge (M-032) on {base} hold-out predictions", results, meta)
    text += "\n## Population\n\n" + pd.DataFrame(rows).to_markdown(index=False) + "\n"
    V.write_report(exp_id, text)
    for fold, va in results.items():
        va.to_parquet(MODELS / "oof" / f"{exp_id}_{fold}.parquet")
    print(pd.DataFrame(rows).to_string(), "\nfinal w", round(w_final, 3))


def final(pred_path, out_path, from_report: str):
    rep = (REPORTS / "experiments" / f"{from_report}.md").read_text()
    w = json.loads(re.search(r"^- final_model: (\{.*\})$", rep, re.M).group(1))["w"]
    d = frame()
    pop = d[d.ds == "rank"].copy()
    _, pop["hedge"] = fit_predict(d[d.ds == "train"], pop)
    p = pd.read_parquet(pred_path).merge(pop[["mvt_id", "hedge"]], on="mvt_id", how="left")
    before = p.pred.to_numpy().copy()
    p["pred"] = np.where(p.hedge.notna(), p.pred + w * (p.hedge - p.pred), p.pred)
    p[["mvt_id", "pred"]].to_parquet(out_path, index=False)
    print(f"w {w:.3f}; changed {int((p.pred != before).sum())} rows; wrote {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["eval", "final"])
    ap.add_argument("--base")
    ap.add_argument("--exp-id")
    ap.add_argument("--pred")
    ap.add_argument("--out")
    ap.add_argument("--from-report")
    a = ap.parse_args()
    if a.cmd == "eval":
        evaluate(a.base, a.exp_id)
    else:
        final(a.pred, a.out, a.from_report)
