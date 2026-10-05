"""Shrink predictions toward the ADS-B off-block estimate where the aircraft was seen leaving its own stand (M-028).

Sources (--sources, priority order): `still` = take-off − first movement at the own OSM stand
(adsb_stand_move_s, M-021), rows seen stationary there; `moving` = take-off − first observation within 60 m of the
stand (adsb_stand_first_s), rows seen at the stand only while moving. Each source gets its own offsets and weights. Fitted on hold-out predictions of the other month (cross-fit, as M-019):
    est'  = est + b_airport           b = median(y − est) per airport (pooled median when n < N_MIN)
    gap   = |est' − pred|             rows with gap > GATE_S are left unchanged (estimate likely from another stop)
    pred' = pred + w_bin · (est' − pred),   w_bin = least-squares slope of (y − pred) on (est' − pred), clipped to [0, 1]
Bins and gate were fixed from reports/checks/p4_adsblol_vs_v4_holdout.md before fitting any weight.

  python -m prc.models.adsb_stack eval --base EXP-039 --exp-id EXP-042
  python -m prc.models.adsb_stack final --base EXP-039 --pred models/EXP-039/pred_rank.parquet --out models/EXP-042/pred_rank.parquet
"""
import argparse
import json

import numpy as np
import pandas as pd

from prc import db, validate as V
from prc.paths import MODELS

GATE_S = 600
BINS = [0, 60, 180, GATE_S]
N_MIN = 30


SOURCES = {  # one estimate per departure; a row belongs to the first source that applies
    "still": "s.adsb_still_at_stand AND s.adsb_stand_move_s IS NOT NULL",                      # M-021 first movement
    "moving": "s.adsb_seen_at_stand AND NOT s.adsb_still_at_stand AND s.adsb_stand_first_s IS NOT NULL",  # first sighting
}
EST_COL = {"still": "s.adsb_stand_move_s", "moving": "s.adsb_stand_first_s"}


def _est(sources=("still",)):
    con = db.connect(read_only=True)
    parts = [f"SELECT f.mvt_id, f.airport, {EST_COL[k]} AS est, '{k}' AS src FROM feat_dep f "
             f"JOIN feat_dep_adsb_stand s USING (mvt_id) WHERE {SOURCES[k]}" for k in sources]
    e = con.sql(" UNION ALL ".join(parts)).df()
    con.close()
    order = {k: i for i, k in enumerate(sources)}
    return e.assign(_o=e.src.map(order)).sort_values("_o").drop_duplicates("mvt_id").drop(columns="_o")


def _bin(gap):
    return np.digitize(gap, BINS[1:-1], right=True)  # 0: ≤60, 1: 60–180, 2: 180–600


def fit(df: pd.DataFrame) -> dict:
    """df: hold-out rows with y, pred, airport, est. Returns offsets per airport and weights per bin."""
    pooled = float(np.median(df.y - df.est))
    off = {ap: float(np.median(g.y - g.est)) if len(g) >= N_MIN else pooled for ap, g in df.groupby("airport")}
    e = df.est + df.airport.map(off).fillna(pooled)
    d, r = (e - df.pred).to_numpy(), (df.y - df.pred).to_numpy()
    keep = np.abs(d) <= GATE_S
    b = _bin(np.abs(d))
    w = {}
    for k in range(len(BINS) - 1):
        m = keep & (b == k)
        w[k] = float(np.clip((d[m] * r[m]).sum() / (d[m] ** 2).sum(), 0, 1)) if m.sum() >= N_MIN else 0.0
    return {"pooled_offset": pooled, "offset": off, "w": w, "n_fit": int(keep.sum())}


def apply(df: pd.DataFrame, pred: np.ndarray, model: dict) -> np.ndarray:
    """df: rows aligned with pred, with airport and est (NaN when no estimate)."""
    pred = np.asarray(pred, float)
    e = (df.est + df.airport.map(model["offset"]).fillna(model["pooled_offset"])).to_numpy(float)
    d = e - pred
    ok = np.isfinite(d) & (np.abs(d) <= GATE_S)
    w = np.zeros(len(pred))
    w[ok] = [model["w"][int(k)] for k in _bin(np.abs(d[ok]))]
    return pred + w * np.where(ok, d, 0.0)


def _fold_frame(base, fold, est):
    va = pd.read_parquet(MODELS / "oof" / f"{base}_{fold}.parquet")
    return va.merge(est[["mvt_id", "est", "src"]], on="mvt_id", how="left")


def fit_sources(df: pd.DataFrame) -> dict:
    """One offset/weight model per estimate source (rows with an estimate only)."""
    return {k: fit(g) for k, g in df[df.est.notna()].groupby("src")}


def apply_sources(df: pd.DataFrame, pred: np.ndarray, models: dict) -> np.ndarray:
    out = np.asarray(pred, float).copy()
    for k, m in models.items():
        mask = (df.src == k).to_numpy()
        out[mask] = apply(df[mask], out[mask], m)
    return out


def _round(models):
    return {k: {**m, "offset": {a: round(o, 1) for a, o in m["offset"].items()}} for k, m in models.items()}


def evaluate(base: str, exp_id: str, sources=("still",)):
    est = _est(sources)
    frames = {fold: _fold_frame(base, fold, est) for fold in V.HOLDOUTS}
    results, models = {}, {}
    names = list(frames)
    for i, fold in enumerate(names):
        model = fit_sources(frames[names[1 - i]])
        models[fold] = model
        va = frames[fold].copy()
        before = va.pred.to_numpy().copy()
        va["pred"] = apply_sources(va, before, model)
        va["adsb_changed"] = va.pred != before
        results[fold] = va
    meta = {"base": base, "data": V.data_version(), "git": V.git_sha(),
            "rule": f"M-028: sources {list(sources)}, per-(source, airport) median offset (n≥{N_MIN}), bins {BINS}, "
                    f"gate {GATE_S}s, cross-fit",
            "models": json.dumps({k: _round(m) for k, m in models.items()})}
    text = V.report_md(exp_id, f"ADS-B stand off-block shrinkage (M-028) on {base} hold-out predictions", results, meta)
    rows = []
    for fold, va in results.items():
        ch = va[va.adsb_changed]
        b = frames[fold].set_index("mvt_id").loc[ch.mvt_id, "pred"].to_numpy()
        rows.append({"fold": fold, "n_rows": len(va), "n_changed": len(ch),
                     "rmse_changed_before": round(V.rmse(ch.y, b), 1), "rmse_changed_after": round(V.rmse(ch.y, ch.pred), 1),
                     "rmse_before": round(V.rmse(va.y, frames[fold].pred), 2), "rmse_after": round(V.rmse(va.y, va.pred), 2)})
        for (sk, ap), g in ch.groupby(["src", "airport"]):
            gb = frames[fold].set_index("mvt_id").loc[g.mvt_id, "pred"].to_numpy()
            rows.append({"fold": fold, "source": sk, "airport": ap, "n_changed": len(g),
                         "rmse_changed_before": round(V.rmse(g.y, gb), 1), "rmse_changed_after": round(V.rmse(g.y, g.pred), 1)})
    text += "\n## Changed rows\n\n" + pd.DataFrame(rows).to_markdown(index=False) + "\n"
    V.write_report(exp_id, text)
    for fold, va in results.items():
        va.drop(columns=["est", "src", "adsb_changed"]).to_parquet(MODELS / "oof" / f"{exp_id}_{fold}.parquet")
    r = {k: round(V.rmse(v.y, v.pred), 2) for k, v in results.items()}
    print(exp_id, r)
    print(pd.DataFrame(rows).to_string())
    return r


def final(base: str, pred_path, out_path, sources=("still",)):
    """Fit on both hold-out months of `base` and apply to its ranking predictions."""
    est = _est(sources)
    fitdf = pd.concat([_fold_frame(base, fold, est) for fold in V.HOLDOUTS])
    model = fit_sources(fitdf)
    p = pd.read_parquet(pred_path).merge(est, on="mvt_id", how="left")
    before = p.pred.to_numpy().copy()
    p["pred"] = apply_sources(p, before, model)
    p[["mvt_id", "pred"]].to_parquet(out_path, index=False)
    print(json.dumps(_round(model), indent=1))
    print(f"changed {int((p.pred != before).sum())} rows; wrote {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["eval", "final"])
    ap.add_argument("--base", required=True)
    ap.add_argument("--exp-id")
    ap.add_argument("--pred")
    ap.add_argument("--out")
    ap.add_argument("--sources", default="still", help="comma list, priority order: still,moving")
    a = ap.parse_args()
    src = tuple(a.sources.split(","))
    if a.cmd == "eval":
        evaluate(a.base, a.exp_id, src)
    else:
        final(a.base, a.pred, a.out, src)
