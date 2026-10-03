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


# --- M-026: three-regime mixture for very late schedule-echo-prone flights ------------------------------------------
BANDS = [(6 * 3600, 14 * 3600), (14 * 3600, None)]     # lateness bands (post-hoc choice, see METHODS M-026)
DM_MIN_S = 72000                                        # "day-minus": real off-block written ~24 h early
MIN_CELL = 5


def _band(ds):
    out = np.full(len(ds), -1)
    for i, (lo, hi) in enumerate(BANDS):
        out[(ds >= lo) & ((ds < hi) if hi else True)] = i
    return out


def fit_regimes(train: pd.DataFrame) -> pd.DataFrame:
    """Per (airport, band, later_day) for NM-unmatched rows at airports qualifying under M-014: regime shares and
    means. Echo: |y − d_sched| ≤ ECHO_TOL_S; day-minus: not echo and y ≥ DM_MIN_S; normal: the rest."""
    airports = fit(train).airport.tolist()
    t = train[train.airport.isin(airports) & train.nm_unmatched].copy()
    t["band"] = _band(t.d_sched.to_numpy(float))
    t = t[t.band >= 0]
    t["later_day"] = t.day_shift.fillna(0) >= 1
    t["echo"] = (t.y - t.d_sched).abs() <= ECHO_TOL_S
    t["dm"] = ~t.echo & (t.y >= DM_MIN_S)
    rows = []
    for keys, g in list(t.groupby(["airport", "band", "later_day"])) + [((a, b, None), g) for (a, b), g in t.groupby(["airport", "band"])]:
        n = (~g.echo & ~g.dm)
        rows.append({"airport": keys[0], "band": keys[1], "later_day": keys[2], "n": len(g), "p_echo": g.echo.mean(),
                     "p_dm": g.dm.mean(), "p_normal": n.mean(), "mean_dm": g.y[g.dm].mean() if g.dm.any() else np.nan,
                     "mean_normal": g.y[n].mean() if n.any() else np.nan})
    return pd.DataFrame(rows)


def apply_regimes(df: pd.DataFrame, pred: np.ndarray, table: pd.DataFrame) -> np.ndarray:
    out = np.asarray(pred, float).copy()
    band = _band(df.d_sched.to_numpy(float))
    later = (df.day_shift.fillna(0) >= 1).to_numpy()
    for i in np.flatnonzero((band >= 0) & df.nm_unmatched.to_numpy() & df.airport.isin(table.airport).to_numpy()):
        ap = df.airport.iat[i]
        cell = table[(table.airport == ap) & (table.band == band[i]) & (table.later_day == later[i])]
        if cell.empty or cell.n.iat[0] < MIN_CELL:
            cell = table[(table.airport == ap) & (table.band == band[i]) & table.later_day.isna()]
        if cell.empty or cell.n.iat[0] < MIN_CELL:
            continue
        c = cell.iloc[0]
        parts = [(c.p_echo, df.d_sched.iat[i]), (c.p_dm, c.mean_dm), (c.p_normal, c.mean_normal)]
        out[i] = sum(p * v for p, v in parts if p > 0)
    return out


def evaluate_regimes(base: str, exp_id: str):
    f = _frame()
    tr_all = f[f.ds == "train"]
    results, tables = {}, []
    for fold, d in V.HOLDOUTS.items():
        va = pd.read_parquet(MODELS / "oof" / f"{base}_{fold}.parquet").merge(
            f[["mvt_id", "d_sched", "nm_unmatched", "day_shift"]], on="mvt_id")
        table = fit_regimes(tr_all[tr_all.month != pd.Timestamp(d)])
        tables.append(table.assign(fold=fold))
        va["pred"] = apply_regimes(va, va.pred.to_numpy(), table)
        results[fold] = va
    meta = {"base": base, "data": V.data_version(), "git": V.git_sha(),
            "rule": f"M-026: NM-unmatched at M-014 airports, bands {BANDS}, later-day split, echo tol {ECHO_TOL_S}s, day-minus y≥{DM_MIN_S}s, min cell {MIN_CELL}"}
    text = V.report_md(exp_id, f"Three-regime hedge (M-026) on {base} hold-out predictions", results, meta)
    text += "\n## Regime table (fit on training months)\n\n" + pd.concat(tables).round(3).to_markdown(index=False) + "\n"
    V.write_report(exp_id, text)
    for fold, va in results.items():
        va.to_parquet(MODELS / "oof" / f"{exp_id}_{fold}.parquet")
    r = {k: round(V.rmse(v.y, v.pred), 2) for k, v in results.items()}
    print(exp_id, r)
    return r


def _frame():
    con = db.connect(read_only=True)
    f = con.sql("SELECT mvt_id, ds, month, airport, y, d_sched, nm_unmatched, day_shift FROM feat_dep").df()
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


def final_regimes(pred_path, out_path):
    """Fit the M-026 regime table on all 2025 training rows and apply it to ranking predictions."""
    f = _frame()
    table = fit_regimes(f[f.ds == "train"])
    p = pd.read_parquet(pred_path).merge(f[["mvt_id", "airport", "d_sched", "nm_unmatched", "day_shift"]], on="mvt_id")
    before = p.pred.to_numpy().copy()
    p["pred"] = apply_regimes(p, p.pred.to_numpy(), table)
    p[["mvt_id", "pred"]].to_parquet(out_path, index=False)
    print(table.round(3).to_string())
    print(f"changed {int((p.pred != before).sum())} rows; wrote {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["eval", "final", "eval3", "final3"])
    ap.add_argument("--base")
    ap.add_argument("--exp-id")
    ap.add_argument("--pred", help="final: ranking predictions parquet")
    ap.add_argument("--out", help="final: output parquet")
    a = ap.parse_args()
    if a.cmd == "eval":
        evaluate(a.base, a.exp_id)
    elif a.cmd == "eval3":
        evaluate_regimes(a.base, a.exp_id)
    elif a.cmd == "final3":
        final_regimes(a.pred, a.out)
    else:
        final(a.pred, a.out)
