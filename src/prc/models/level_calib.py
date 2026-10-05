"""Level calibration to the EUROCONTROL monthly mean taxi-out (M-029).

A model trained on 2025 cannot see month-level shifts of the taxi-out level in 2026. EUROCONTROL publishes the monthly
mean taxi-out per airport (feat_dep_ec.ec_m_taxi_mean_s, M-017), which tracks our target mean closely except where it
excludes de-icing (gap grows with snow). Per airport, on training months:
    gap(m) = mean(y | y ≤ 2 h)(m) − EC(m)  ≈  c + s · snow_share(m)        (OLS; intercept only if snow never > 1 %)
For a target airport-month: level = EC + ĝ; Δ = level − mean(pred | pred ≤ 2 h); rows with pred ≤ 2 h get pred + w·Δ.
w = least-squares shrink of (y − pred) on Δ over the other hold-out month (cross-fit), clipped to [0, 1]; final w from
both months. Snow share = share of departures with snow or freezing precipitation in the last 3 h (M-012).

  python -m prc.models.level_calib eval --base EXP-051 --exp-id EXP-052
  python -m prc.models.level_calib final --base EXP-051 --pred models/EXP-051/pred_rank.parquet --out models/EXP-052/pred_rank.parquet
"""
import argparse
import json

import numpy as np
import pandas as pd

from prc import db, validate as V
from prc.paths import MODELS

CAP_S = 7200
SNOW_MIN = 0.01


def _frame() -> pd.DataFrame:
    con = db.connect(read_only=True)
    f = con.sql("""SELECT d.mvt_id, d.ds, d.airport, d.month, d.y, e.ec_m_taxi_mean_s AS ec,
                          (coalesce(w.wx3h_snow, false) OR coalesce(w.wx3h_freezing, false))::INT AS snow
                   FROM feat_dep d LEFT JOIN feat_dep_ec e USING (mvt_id) LEFT JOIN feat_dep_wx w USING (mvt_id)""").df()
    con.close()
    f["month"] = pd.to_datetime(f.month)
    return f


def monthly(f: pd.DataFrame) -> pd.DataFrame:
    """Per airport-month: EC mean, snow share, mean y over y ≤ CAP_S (NaN in the ranking months)."""
    g = f.groupby(["airport", "month"])
    m = pd.DataFrame({"ec": g.ec.first(), "snow": g.snow.mean(),
                      "ybar": f[f.y <= CAP_S].groupby(["airport", "month"]).y.mean()}).reset_index()
    return m


def fit_gap(train_m: pd.DataFrame) -> dict:
    """airport -> (c, s) of gap = c + s·snow, from training airport-months."""
    out = {}
    for ap, g in train_m.dropna(subset=["ybar", "ec"]).groupby("airport"):
        gap = (g.ybar - g.ec).to_numpy()
        if g.snow.max() > SNOW_MIN and len(g) >= 3:
            s, c = np.polyfit(g.snow.to_numpy(), gap, 1)
        else:
            s, c = 0.0, float(gap.mean())
        out[ap] = (float(c), float(s))
    return out


def deltas(rows: pd.DataFrame, m_target: pd.DataFrame, gap: dict) -> pd.Series:
    """Δ per row (airport-month level − mean prediction over pred ≤ CAP_S); 0 where EC or the gap model is missing."""
    lvl = m_target.set_index(["airport", "month"])
    key = pd.MultiIndex.from_frame(rows[["airport", "month"]])
    ec, snow = lvl.ec.reindex(key).to_numpy(), lvl.snow.reindex(key).to_numpy()
    c = rows.airport.map({a: v[0] for a, v in gap.items()}).to_numpy(float)
    s = rows.airport.map({a: v[1] for a, v in gap.items()}).to_numpy(float)
    level = ec + c + s * snow
    pm = rows[rows.pred <= CAP_S].groupby(["airport", "month"]).pred.mean()
    d = level - pm.reindex(key).to_numpy()
    d = np.where(np.isfinite(d) & (rows.pred.to_numpy() <= CAP_S), d, 0.0)
    return pd.Series(d, index=rows.index)


def shrink(rows: pd.DataFrame, d: pd.Series) -> float:
    r = (rows.y - rows.pred).to_numpy(float)
    dd = d.to_numpy(float)
    return float(np.clip((dd * r).sum() / (dd ** 2).sum(), 0, 1)) if (dd ** 2).sum() > 0 else 0.0


def _fold(base, fold, f):
    va = pd.read_parquet(MODELS / "oof" / f"{base}_{fold}.parquet")
    va["month"] = pd.to_datetime(va.month)
    return va


def evaluate(base: str, exp_id: str):
    f = _frame()
    mm = monthly(f[f.ds == "train"])
    frames, dl, gaps = {}, {}, {}
    for fold, d in V.HOLDOUTS.items():
        hold = pd.Timestamp(d)
        gaps[fold] = fit_gap(mm[mm.month != hold])
        frames[fold] = _fold(base, fold, f)
        dl[fold] = deltas(frames[fold], mm[mm.month == hold], gaps[fold])
    names = list(frames)
    results, ws, per = {}, {}, []
    for i, fold in enumerate(names):
        other = names[1 - i]
        w = shrink(frames[other], dl[other])
        ws[fold] = w
        va = frames[fold].copy()
        va["pred"] = va.pred + w * dl[fold]
        results[fold] = va
        for ap, g in va.groupby("airport"):
            b = frames[fold].loc[g.index]
            dg = dl[fold].loc[g.index]
            per.append({"fold": fold, "airport": ap, "delta_s": round(float(dg[dg != 0].mean()) if (dg != 0).any() else 0.0, 1),
                        "rmse_before": round(V.rmse(b.y, b.pred), 2), "rmse_after": round(V.rmse(g.y, g.pred), 2)})
    meta = {"base": base, "data": V.data_version(), "git": V.git_sha(),
            "rule": f"M-029: gap = c + s·snow per airport on training months, rows pred ≤ {CAP_S}s, cross-fitted shrink",
            "shrink_w": json.dumps({k: round(v, 3) for k, v in ws.items()}),
            "gap_models": json.dumps({k: {a: [round(c, 1), round(s, 1)] for a, (c, s) in g.items()} for k, g in gaps.items()})}
    text = V.report_md(exp_id, f"EC monthly level calibration (M-029) on {base} hold-out predictions", results, meta)
    text += "\n## Per airport (Δ = level − mean prediction, before shrink)\n\n" + pd.DataFrame(per).to_markdown(index=False) + "\n"
    V.write_report(exp_id, text)
    for fold, va in results.items():
        va.to_parquet(MODELS / "oof" / f"{exp_id}_{fold}.parquet")
    r = {k: round(V.rmse(v.y, v.pred), 2) for k, v in results.items()}
    print(exp_id, r, "w", ws)
    print(pd.DataFrame(per).to_string())
    return r


def final(base: str, pred_path, out_path):
    f = _frame()
    mm_train = monthly(f[f.ds == "train"])
    gap = fit_gap(mm_train)
    # shrink from both hold-out months (each with its own leave-month-out gap model)
    num = den = 0.0
    for fold, d in V.HOLDOUTS.items():
        hold = pd.Timestamp(d)
        va = _fold(base, fold, f)
        dd = deltas(va, mm_train[mm_train.month == hold], fit_gap(mm_train[mm_train.month != hold]))
        num += float((dd * (va.y - va.pred)).sum()); den += float((dd ** 2).sum())
    w = float(np.clip(num / den, 0, 1)) if den > 0 else 0.0
    rk = f[f.ds == "rank"]
    mm_rank = monthly(rk)
    p = pd.read_parquet(pred_path).merge(rk[["mvt_id", "airport", "month"]], on="mvt_id")
    d = deltas(p, mm_rank, gap)
    p["pred"] = p.pred + w * d
    p[["mvt_id", "pred"]].to_parquet(out_path, index=False)
    lv = p.assign(d=d).groupby(["airport", "month"]).d.agg(lambda s: s[s != 0].mean() if (s != 0).any() else 0.0)
    print("w", round(w, 3)); print(lv.round(1).to_string())
    print(f"changed {int((d != 0).sum())} rows; wrote {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["eval", "final"])
    ap.add_argument("--base", required=True)
    ap.add_argument("--exp-id")
    ap.add_argument("--pred")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.cmd == "eval":
        evaluate(a.base, a.exp_id)
    else:
        final(a.base, a.pred, a.out)
