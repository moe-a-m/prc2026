import sys; sys.path.insert(0,'/tmp/claude-1000/-home-m-opensky-2026/9cdb9da0-8aa7-43e9-ae6c-5d8fa22d5230/scratchpad')
from common import *
import pandas as pd, numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
con=connect()
FN=open('/tmp/claude-1000/-home-m-opensky-2026/9cdb9da0-8aa7-43e9-ae6c-5d8fa22d5230/scratchpad/fn.sql').read()
base=f"""SELECT c.mvt_id, c.month, c.y, abs(epoch(c.t_block)-epoch(c.t_sched)) <= 60 echo, (epoch(c.t_aobt3)-epoch(c.t_sched)) nm_delay,
   epoch(c.t_mvt)-epoch(c.t_sched) d_sched, epoch(c.t_mvt)-epoch(c.t_aobt3) px, second(c.t_mvt)=0 mvt_s0, ({FN})='mangled_repeat' mangled,
   coalesce(c.operator,'?') op, c.stand, hour(c.t_mvt) hr, c.runway
   FROM clean_dep c WHERE c.ds='train' AND c.airport='LIRF' AND NOT c.f_no_nm_match AND c.t_aobt3 IS NOT NULL AND epoch(c.t_aobt3)-epoch(c.t_sched) > 600"""
run(con, "p6_lirf_matched_late_echo_by_mvtsec0", f"""
WITH b AS ({base}) SELECT mvt_s0, mangled, count(*) n, round(100*avg(echo::INT),1) pct_echo FROM b GROUP BY ALL ORDER BY ALL""",
"LIRF NM-matched 2025 departures with NM delay (AOBT_3-SCHED) > 10 min: echo share (|BLOCK-SCHED|<=60 s) by MVT on a whole minute and mangled flight number.")
d = con.sql(f"WITH b AS ({base}) SELECT * FROM b").df()
d["mon"]=pd.to_datetime(d.month).dt.month
X = pd.DataFrame({"nm_delay": d.nm_delay, "d_sched": d.d_sched, "px": d.px, "mvt_s0": d.mvt_s0.astype(int), "mangled": d.mangled.astype(int),
                  "op": d.op.astype("category").cat.codes, "stand": pd.to_numeric(d.stand, errors="coerce"), "hr": d.hr,
                  "rw": d.runway.astype("category").cat.codes})
y = d.echo.astype(int).to_numpy(); p = np.zeros(len(d))
for m in range(1,13):
    te=(d.mon==m).to_numpy()
    clf=HistGradientBoostingClassifier(max_depth=4, max_iter=200, learning_rate=0.05, categorical_features=[5,8], random_state=0)
    clf.fit(X[~te], y[~te]); p[te]=clf.predict_proba(X[te])[:,1]
auc=roc_auc_score(y,p)
# hedge evaluation: expected y = p*d_sched + (1-p)*(px + median non-echo residual) vs EXP-031
o = pd.concat([pd.read_parquet(f"models/oof/EXP-031_{k}.parquet")[["mvt_id","y","pred"]] for k in ["jan","jul"]])
TOT=((o.pred-o.y)**2).sum()
d["p"]=p
rows=[]
for m,k in [(1,"jan"),(7,"jul")]:
    tr=d[d.mon!=m]; off=np.median((tr.y-tr.px)[~tr.echo])
    s=d[d.mon==m].merge(o[["mvt_id","pred"]], on="mvt_id")
    s["hedge"]=s.p*s.d_sched+(1-s.p)*(s.px+off)
    s["mix"]=s.pred+s.p*(s.d_sched-s.pred)*0  # placeholder
    for name,col in [("EXP-031","pred"),("classifier hedge","hedge")]:
        rows.append(dict(fold=k,n=len(s),method=name,pct_total_sq_err=round(100*((s[col]-s.y)**2).sum()/TOT,3)))
    rows.append(dict(fold=k,n=len(s),method="mean(EXP-031, hedge)",pct_total_sq_err=round(100*(((s.pred+s.hedge)/2-s.y)**2).sum()/TOT,3)))
r=pd.DataFrame(rows); print(auc); print(r)
open("reports/checks/p6_lirf_matched_echo_classifier.md","w").write("# Check: p6_lirf_matched_echo_classifier\n\n"
 f"LIRF NM-matched 2025 departures with NM delay > 10 min (n={len(d)}, echo rate {y.mean():.3f}). Leave-one-month-out HistGradientBoostingClassifier "
 "(depth 4, 200 iter) on nm_delay, d_sched, MVT-AOBT_3, MVT second==0, mangled flight number, NM operator, stand, take-off hour, runway.\n\n"
 f"- AUC (month-held-out) = {auc:.3f}; AUC of nm_delay alone = {roc_auc_score(y,-d.nm_delay):.3f}\n\n"
 "Hedge = p*d_sched + (1-p)*(MVT-AOBT_3 + median non-echo residual of other months), on EXP-031 hold-out rows of this population; % of total EXP-031 Jan+Jul squared error.\n\n"
 + r.to_markdown(index=False)+"\n")
