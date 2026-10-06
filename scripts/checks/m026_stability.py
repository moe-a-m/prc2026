"""M-026 robustness: regime shares per 2025 month, 95% Wilson intervals on the pooled shares, and the board-RMSE cost on
the ranking rows if 2026 shares sat at the interval ends.

  python scripts/checks/m026_stability.py [BOARD_RMSE]     (default 278.54 = v8)
"""
import sys

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from prc.models import hedge as H
from prc.paths import CHECKS

BOARD = float(sys.argv[1]) if len(sys.argv) > 1 else 278.54
f = H._frame()
tr = f[f.ds == "train"]
airports = H.fit(tr).airport.tolist()


def regimes(d):
    d = d[d.airport.isin(airports) & d.nm_unmatched.fillna(False)].copy()
    d["band"] = H._band(d.d_sched.to_numpy(float))
    d = d[d.band >= 0]
    d["later_day"] = d.day_shift.fillna(0) >= 1
    if d.y.notna().any():
        d["echo"] = (d.y - d.d_sched).abs() <= H.ECHO_TOL_S
        d["dm"] = ~d.echo & (d.y >= H.DM_MIN_S)
    return d


t = regimes(tr)
monthly = (t.assign(ym=t.month.dt.strftime("%Y-%m"), normal=~t.echo & ~t.dm)
           .groupby(["airport", "band", "ym"]).agg(n=("y", "size"), echo=("echo", "sum"), dm=("dm", "sum"),
                                                   normal=("normal", "sum")).reset_index())

pooled = []
for (ap, b), g in t.groupby(["airport", "band"]):
    n = len(g)
    for name, k in [("echo", int(g.echo.sum())), ("day_minus", int(g.dm.sum())), ("normal", int((~g.echo & ~g.dm).sum()))]:
        ci = binomtest(k, n).proportion_ci(confidence_level=0.95, method="wilson")
        pooled.append({"airport": ap, "band": b, "regime": name, "n": n, "k": k, "share": round(k / n, 3),
                       "ci_low": round(ci.low, 3), "ci_high": round(ci.high, 3)})
pooled = pd.DataFrame(pooled)

# ranking rows the hedge changes, and the expected squared error under shifted shares
table = H.fit_regimes(tr)
rk = regimes(f[f.ds == "rank"].assign(y=np.nan))
rows = []
for r in rk.itertuples():
    cell = table[(table.airport == r.airport) & (table.band == r.band) & (table.later_day == r.later_day)]
    if cell.empty or cell.n.iat[0] < H.MIN_CELL:
        cell = table[(table.airport == r.airport) & (table.band == r.band) & table.later_day.isna()]
    if cell.empty or cell.n.iat[0] < H.MIN_CELL:
        continue
    c = cell.iloc[0]
    v = np.array([r.d_sched, c.mean_dm if c.p_dm > 0 else 0.0, c.mean_normal if c.p_normal > 0 else 0.0], float)
    q = np.array([c.p_echo, c.p_dm, c.p_normal], float)
    rows.append({"mvt_id": r.mvt_id, "band": r.band, "v": v, "q": q, "pred": float(q @ v)})


def sse(shift):
    """Expected squared error of the hedged predictions if the true echo share moved by `shift` (a number, or a dict
    band → shift; others rescaled)."""
    tot = 0.0
    for r in rows:
        q = r["q"].copy()
        s = shift.get(r["band"], 0.0) if isinstance(shift, dict) else shift
        q0 = np.clip(q[0] + s, 0, 1)
        rest = q[1:].sum()
        q[1:] = q[1:] / rest * (1 - q0) if rest > 0 else np.r_[1 - q0, 0.0]
        q[0] = q0
        tot += float(q @ (r["v"] - r["pred"]) ** 2)
    return tot


N = 344841
base = sse(0.0)
cost = []
for s in (-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3):
    d = sse(s) - base
    cost.append({"echo_share_shift": s, "delta_sse": round(d), "board_rmse_delta": round(np.sqrt(BOARD ** 2 + d / N) - BOARD, 3)})
ci = pooled[pooled.regime == "echo"].set_index("band")
for label, end in [("both bands at the Wilson lower end", "ci_low"), ("both bands at the Wilson upper end", "ci_high")]:
    sh = {b: float(ci.loc[b, end] - ci.loc[b, "share"]) for b in ci.index}
    d = sse(sh) - base
    cost.append({"echo_share_shift": label + " " + str({b: round(v, 3) for b, v in sh.items()}), "delta_sse": round(d),
                 "board_rmse_delta": round(np.sqrt(BOARD ** 2 + d / N) - BOARD, 3)})
cost = pd.DataFrame(cost)

CHECKS.mkdir(parents=True, exist_ok=True)
text = ["# Check: m026_stability", "", f"M-026 regime shares (airports {airports}, NM-unmatched, bands {H.BANDS}).",
        "", "## Pooled 2025 shares with 95% Wilson intervals", "", pooled.to_markdown(index=False), "",
        "## Per month", "", monthly.to_markdown(index=False), "",
        f"## Ranking rows hedged: {len(rows)} (bands: {pd.Series([r['band'] for r in rows]).value_counts().to_dict()})", "",
        "Expected extra squared error on these rows if the 2026 echo share differs from 2025 by the shift (other regimes "
        f"rescaled), and the implied board RMSE change at board {BOARD} over {N} rows:", "", cost.to_markdown(index=False), ""]
(CHECKS / "m026_stability.md").write_text("\n".join(text))
print("\n".join(text))
