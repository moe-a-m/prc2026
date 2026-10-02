"""Calibrated hedge for schedule-echo rows (M-014).

When the airport block time echoes the schedule, the label is y ≈ d_sched (take-off − scheduled). For flights that
took off > 3 h after schedule, per (airport, NM-match) cell estimated on training months only:
    p     = share of rows with |y − d_sched| ≤ 120 s
    other = mean y of the remaining rows
and, in cells with p ≥ P_MIN (rule fixed before looking at validation results), the prediction is replaced by
    p · d_sched + (1 − p) · other          (the RMSE-optimal mixture under a two-point model)

  python -m prc.models.hedge eval --base EXP-012 --exp-id EXP-021
"""
import argparse

import numpy as np
import pandas as pd

from prc import db, validate as V
from prc.paths import MODELS

LATE_S = 3 * 3600
ECHO_TOL_S = 120
P_MIN = 0.2
N_MIN = 30


def fit(train: pd.DataFrame) -> pd.DataFrame:
    """train: y, d_sched, airport, nm_unmatched. Returns the hedge table (cells with p ≥ P_MIN)."""
    late = train[train.d_sched > LATE_S]
    rows = []
    for (ap, um), g in late.groupby(["airport", "nm_unmatched"]):
        echo = (g.y - g.d_sched).abs() <= ECHO_TOL_S
        if len(g) >= N_MIN and echo.mean() >= P_MIN:
            rows.append({"airport": ap, "nm_unmatched": um, "n": len(g), "p_echo": echo.mean(),
                         "other_mean": g.y[~echo].mean()})
    return pd.DataFrame(rows, columns=["airport", "nm_unmatched", "n", "p_echo", "other_mean"])


def apply(df: pd.DataFrame, pred: np.ndarray, table: pd.DataFrame) -> np.ndarray:
    out = np.asarray(pred, float).copy()
    for r in table.itertuples():
        m = ((df.airport == r.airport) & (df.nm_unmatched == r.nm_unmatched) & (df.d_sched > LATE_S)).to_numpy()
        out[m] = r.p_echo * df.d_sched.to_numpy(float)[m] + (1 - r.p_echo) * r.other_mean
    return out


def _frame():
    con = db.connect(read_only=True)
    f = con.sql("SELECT mvt_id, ds, month, airport, y, d_sched, nm_unmatched FROM feat_dep").df()
    con.close()
    f["month"] = pd.to_datetime(f.month)
    return f


def evaluate(base: str, exp_id: str):
    f = _frame()
    tr_all = f[f.ds == "train"]
    results, tables = {}, []
    for fold, d in V.HOLDOUTS.items():
        va = pd.read_parquet(MODELS / "oof" / f"{base}_{fold}.parquet")
        va = va.merge(f[["mvt_id", "d_sched", "nm_unmatched"]], on="mvt_id")
        table = fit(tr_all[tr_all.month != pd.Timestamp(d)])
        tables.append(table.assign(fold=fold))
        va["pred"] = apply(va, va.pred.to_numpy(), table)
        results[fold] = va
    meta = {"base": base, "data": V.data_version(), "git": V.git_sha(),
            "rule": f"cells d_sched>{LATE_S}s per (airport, nm_unmatched), n≥{N_MIN}, p_echo≥{P_MIN}, tol {ECHO_TOL_S}s"}
    text = V.report_md(exp_id, f"Calibrated echo hedge on {base} hold-out predictions", results, meta)
    text += "\n## Hedge cells (fit on training months)\n\n" + pd.concat(tables).round(3).to_markdown(index=False) + "\n"
    V.write_report(exp_id, text)
    for fold, va in results.items():
        va.to_parquet(MODELS / "oof" / f"{exp_id}_{fold}.parquet")
    r = {k: round(V.rmse(v.y, v.pred), 2) for k, v in results.items()}
    print(exp_id, r)
    return r


def final(pred_path, out_path):
    """Fit the hedge on all 2025 training rows and apply it to ranking predictions."""
    f = _frame()
    table = fit(f[f.ds == "train"])
    p = pd.read_parquet(pred_path).merge(f[["mvt_id", "airport", "d_sched", "nm_unmatched"]], on="mvt_id")
    p["pred"] = apply(p, p.pred.to_numpy(), table)
    p[["mvt_id", "pred"]].to_parquet(out_path, index=False)
    print(table.round(3).to_string())
    print(f"wrote {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["eval", "final"])
    ap.add_argument("--base")
    ap.add_argument("--exp-id")
    ap.add_argument("--pred", help="final: ranking predictions parquet")
    ap.add_argument("--out", help="final: output parquet")
    a = ap.parse_args()
    if a.cmd == "eval":
        evaluate(a.base, a.exp_id)
    else:
        final(a.pred, a.out)
