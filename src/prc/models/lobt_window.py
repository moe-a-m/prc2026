"""Feasible-interval projection (M-031): the airport off-block of an NM-matched departure lies within ±WINDOW_S of the
NM last known off-block time (LOBT), so taxi-out = take-off − off-block lies in [d_lobt − WINDOW_S, d_lobt + WINDOW_S]
(d_lobt = take-off − LOBT). Predictions are clipped to that interval and floored at 0; rows without LOBT are unchanged.
WINDOW_S is the bound measured on 2025 (reports/checks/lobt_window_train.md), not a fitted parameter.

  python -m prc.models.lobt_window eval --base EXP-100 --exp-id EXP-101
  python -m prc.models.lobt_window final --pred models/EXP-100/pred_rank.parquet --out models/EXP-101/pred_rank.parquet
"""
import argparse

import numpy as np
import pandas as pd

from prc import db, validate as V
from prc.paths import MODELS

WINDOW_S = 3606


def project(pred, d_lobt) -> np.ndarray:
    """Clip each prediction to [d_lobt − WINDOW_S, d_lobt + WINDOW_S] where d_lobt is known, then floor at 0."""
    p = np.asarray(pred, float).copy()
    d = np.asarray(d_lobt, float)
    ok = np.isfinite(d)
    p[ok] = np.clip(p[ok], d[ok] - WINDOW_S, d[ok] + WINDOW_S)
    return np.maximum(p, 0.0)


def _d_lobt() -> pd.DataFrame:
    con = db.connect(read_only=True)
    d = con.sql("SELECT mvt_id, d_lobt FROM feat_dep").df()
    con.close()
    return d


def evaluate(base: str, exp_id: str):
    d = _d_lobt()
    results, rows = {}, []
    for fold in V.HOLDOUTS:
        va = pd.read_parquet(MODELS / "oof" / f"{base}_{fold}.parquet").merge(d, on="mvt_id", how="left")
        before = va.pred.to_numpy().copy()
        va["pred"] = project(before, va.d_lobt)
        ch = va.pred.to_numpy() != before
        results[fold] = va.drop(columns="d_lobt")
        rows.append({"fold": fold, "n_rows": len(va), "n_changed": int(ch.sum()),
                     "rmse_changed_before": round(V.rmse(va.y[ch], before[ch]), 1) if ch.any() else None,
                     "rmse_changed_after": round(V.rmse(va.y[ch], va.pred[ch]), 1) if ch.any() else None,
                     "rmse_before": round(V.rmse(va.y, before), 2), "rmse_after": round(V.rmse(va.y, va.pred), 2),
                     "n_y_outside_window": int((np.isfinite(va.d_lobt) & ((va.y - va.d_lobt).abs() > WINDOW_S)).sum())})
        for ap, g in va[ch].groupby("airport"):
            b = before[ch][(va.airport[ch] == ap).to_numpy()]
            rows.append({"fold": fold, "airport": ap, "n_changed": len(g),
                         "rmse_changed_before": round(V.rmse(g.y, b), 1), "rmse_changed_after": round(V.rmse(g.y, g.pred), 1)})
    meta = {"base": base, "data": V.data_version(), "git": V.git_sha(),
            "rule": f"M-031: clip to take-off − LOBT ± {WINDOW_S}s where LOBT exists, floor 0 (no fitted parameters)"}
    text = V.report_md(exp_id, f"LOBT feasible-interval projection (M-031) on {base} hold-out predictions", results, meta)
    text += "\n## Changed rows\n\n" + pd.DataFrame(rows).to_markdown(index=False) + "\n"
    V.write_report(exp_id, text)
    for fold, va in results.items():
        va.to_parquet(MODELS / "oof" / f"{exp_id}_{fold}.parquet")
    print(pd.DataFrame(rows).to_string())


def final(pred_path, out_path):
    p = pd.read_parquet(pred_path).merge(_d_lobt(), on="mvt_id", how="left")
    before = p.pred.to_numpy().copy()
    p["pred"] = project(before, p.d_lobt)
    p[["mvt_id", "pred"]].to_parquet(out_path, index=False)
    ch = p.pred.to_numpy() != before
    print(f"changed {int(ch.sum())} rows (mean |shift| {np.abs(p.pred - before)[ch].mean():.0f} s); wrote {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["eval", "final"])
    ap.add_argument("--base")
    ap.add_argument("--exp-id")
    ap.add_argument("--pred")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.cmd == "eval":
        evaluate(a.base, a.exp_id)
    else:
        final(a.pred, a.out)
