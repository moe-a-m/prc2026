import sys; sys.path.insert(0,'/tmp/claude-1000/-home-m-opensky-2026/9cdb9da0-8aa7-43e9-ae6c-5d8fa22d5230/scratchpad')
from common import *
import pandas as pd, numpy as np
con=connect()
# the regime table used by the rule (saved as a check, aggregated over all 2025 months)
REG = """CASE WHEN abs(y - d_sched) <= 120 THEN 'echo' WHEN y BETWEEN 72000 AND 100800 THEN 'dayminus' ELSE 'normal' END"""
BAND = """CASE WHEN d_sched < 10800 THEN '0 <3h' WHEN d_sched < 21600 THEN '1 3-6h' WHEN d_sched < 50400 THEN '2 6-14h' ELSE '3 >=14h' END"""
base = f"""SELECT mvt_id, month, y, epoch(t_mvt)-epoch(t_sched) d_sched FROM clean_dep WHERE ds='train' AND airport='LIRF' AND f_no_nm_match"""
run(con, "p6_lirf_unmatched_regimes_by_band", f"""
WITH b AS ({base}), r AS (SELECT *, {REG} reg, {BAND} band FROM b)
SELECT band, count(*) n, round(100*avg((reg='echo')::INT),1) pct_echo, round(100*avg((reg='dayminus')::INT),1) pct_dayminus,
  round(100*avg((reg='normal')::INT),1) pct_normal, round(avg(y) FILTER (reg='normal')) mean_y_normal,
  round(avg(y-86400) FILTER (reg='dayminus')) mean_y_minus_86400_dayminus
FROM r GROUP BY 1 ORDER BY 1""",
"LIRF NM-unmatched 2025 departures: three label regimes (echo |y-d_sched|<=120 s; day-minus y in [20h,28h] not echo; normal) by lateness band.")
d = con.sql(f"WITH b AS ({base}) SELECT *, {REG} reg, {BAND} band FROM b").df()
o = pd.concat([pd.read_parquet(f"models/oof/EXP-031_{k}.parquet")[["mvt_id","pred"]].assign(fold=k) for k in ["jan","jul"]])
allo = pd.concat([pd.read_parquet(f"models/oof/EXP-031_{k}.parquet")[["mvt_id","y","pred"]] for k in ["jan","jul"]])
TOT = ((allo.pred-allo.y)**2).sum()
d["mon"] = pd.to_datetime(d.month).dt.month
out=[]
for k, m in [("jan",1),("jul",7)]:
    tr = d[d.mon != m]; te = d[d.mon == m].merge(o[o.fold==k], on="mvt_id")
    for band in ["1 3-6h","2 6-14h","3 >=14h"]:
        t = tr[tr.band==band]; s = te[te.band==band].copy()
        if len(s)==0: continue
        pe=(t.reg=="echo").mean(); pdm=(t.reg=="dayminus").mean(); pn=1-pe-pdm
        mn = t.y[t.reg=="normal"].mean() if pn>0 else 0
        md = t.y[t.reg=="dayminus"].mean() if pdm>0 else 0
        s["rule"] = pe*s.d_sched + pdm*md + pn*mn
        out.append(dict(fold=k, band=band, n_train=len(t), p_echo=round(pe,3), p_dayminus=round(pdm,3), n_hold=len(s),
            se_exp031_pct_total=round(100*((s.pred-s.y)**2).sum()/TOT,2), se_rule_pct_total=round(100*((s.rule-s.y)**2).sum()/TOT,2),
            se_blend50_pct_total=round(100*(((s.rule+s.pred)/2-s.y)**2).sum()/TOT,2)))
res = pd.DataFrame(out); print(res.to_string())
res.to_csv("reports/checks/p6_lirf_regime_hedge_eval.csv", index=False)
open("reports/checks/p6_lirf_regime_hedge_eval.md","w").write("# Check: p6_lirf_regime_hedge_eval\n\n"
 "Exploratory post-hoc evaluation (not an experiment) of a three-regime hedge for LIRF NM-unmatched departures on the EXP-031 "
 "Jan/Jul 2025 hold-outs. Regime probabilities and regime means estimated on the 11 other 2025 months; prediction = p_echo*d_sched + "
 "p_dayminus*mean(y|dayminus) + p_normal*mean(y|normal). Squared error expressed as % of the total EXP-031 hold-out squared error "
 "(Jan+Jul). Caveat: the band edges (3/6/14 h) were chosen after viewing all 2025 months incl. the hold-outs. "
 "Script: scratchpad q9.py (regime SQL in p6_lirf_unmatched_regimes_by_band).\n\n" + res.to_markdown(index=False) + "\n")
