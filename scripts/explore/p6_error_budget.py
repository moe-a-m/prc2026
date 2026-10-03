"""Squared-error budget of a model's hold-out predictions by data-quality category (cleaning investigation)."""
import sys

import numpy as np
import pandas as pd

from prc import db

EXP = sys.argv[1] if len(sys.argv) > 1 else "EXP-031"
con = db.connect(read_only=True)
ctx = con.sql("""SELECT f.mvt_id, f.d_sched, f.day_shift, f.d_aobt3, f.d_lobt, f.d_eobt1, f.nm_unmatched, f.type_mismatch,
  abs(epoch(c.t_block)-epoch(c.t_sched)) AS blk_sched_abs, c.ades_mvt <> c.ades_flt AS ades_mismatch,
  c.f_round_minute_block AS round_min_block
FROM feat_dep f JOIN clean_dep c USING (mvt_id) WHERE f.ds='train'""").df()
o = pd.concat([pd.read_parquet(f"models/oof/{EXP}_{k}.parquet")[["mvt_id", "airport", "y", "pred"]].assign(fold=k)
               for k in ["jan", "jul"]]).merge(ctx, on="mvt_id")
o["se"] = (o.pred - o.y) ** 2
tot = o.se.sum()
y, ds = o.y, o.d_sched
cats = {
    "A unmatched NM": o.nm_unmatched,
    "B echo: |BLOCK-SCHED|<=10s & late>1h": (o.blk_sched_abs <= 10) & (ds > 3600),
    "C day-shift: y>20h": y > 72000,
    "D y in (3h,20h]": (y > 10800) & (y <= 72000),
    "E matched, NM proxy off by >1h": (~o.nm_unmatched) & ((o.d_aobt3 - y).abs() > 3600),
    "F label <= 0": y <= 0,
    "G ADES mvt!=flt (wrong NM join?)": o.ades_mismatch,
    "H aircraft type mvt!=flt": o.type_mismatch,
    "I minute-rounded block": o.round_min_block,
}
cats = {k: v.fillna(False).astype(bool) for k, v in cats.items()}
rows = [dict(category=k, n=int(m.sum()), pct_rows=round(100 * m.mean(), 2), pct_sq_err=round(100 * o.se[m].sum() / tot, 1),
             rmse=round(float(np.sqrt(o.se[m].mean())), 0) if m.any() else None) for k, m in cats.items()]
none = ~np.column_stack([cats[k] for k in list(cats)[:6]]).any(1)
rows.append(dict(category="regular (none of A-F)", n=int(none.sum()), pct_rows=round(100 * none.mean(), 2),
                 pct_sq_err=round(100 * o.se[none].sum() / tot, 1), rmse=round(float(np.sqrt(o.se[none].mean())), 0)))
t = pd.DataFrame(rows)
print(t.to_string(index=False))
by_ap = o.assign(cat=np.select([cats["A unmatched NM"], cats["C day-shift: y>20h"], cats["E matched, NM proxy off by >1h"]],
                               ["A_unmatched", "C_dayshift", "E_proxy_off"], "other")).pivot_table(
    index="airport", columns="cat", values="se", aggfunc="sum") / tot * 100
print(by_ap.round(1).to_string())
t.to_csv(f"reports/checks/p6_error_budget_{EXP}.csv", index=False)
open(f"reports/checks/p6_error_budget_{EXP}.md", "w").write(
    f"# Check: p6_error_budget_{EXP}\n\nSquared-error budget of {EXP} on the Jan+Jul 2025 hold-outs by data-quality category "
    "(categories overlap; 'regular' = none of A-F). Script: scripts/explore/p6_error_budget.py.\n\n"
    + t.to_markdown(index=False) + "\n\n## % of total squared error by airport × category\n\n" + by_ap.round(1).to_markdown() + "\n")
