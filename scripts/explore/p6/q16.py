import sys; sys.path.insert(0,'/tmp/claude-1000/-home-m-opensky-2026/9cdb9da0-8aa7-43e9-ae6c-5d8fa22d5230/scratchpad')
from common import *
con=connect()
FN=open('/tmp/claude-1000/-home-m-opensky-2026/9cdb9da0-8aa7-43e9-ae6c-5d8fa22d5230/scratchpad/fn.sql').read()
base = f"""SELECT c.*, epoch(c.t_mvt)-epoch(c.t_sched) d_sched, abs(c.y-(epoch(c.t_mvt)-epoch(c.t_sched)))<=120 echo,
   {FN} fn_class, coalesce(regexp_extract(c.flight_mvt,'^[A-Z]{{3}}'),'?') pfx, second(c.t_mvt)=0 mvt_sec0
   FROM clean_dep c WHERE c.airport='LIRF' AND c.f_no_nm_match AND epoch(c.t_mvt)-epoch(c.t_sched) BETWEEN 3600 AND 21600"""
run(con, "p6_lirf_unmatched_echo_by_marker", f"""
WITH b AS ({base}), u AS (
  SELECT 'carrier' m, CASE WHEN pfx IN (SELECT pfx FROM b WHERE ds='train' GROUP BY pfx HAVING count(*)>=25) THEN pfx ELSE 'other' END v, echo, ds FROM b
  UNION ALL SELECT 'fn_class', fn_class, echo, ds FROM b
  UNION ALL SELECT 'mvt_sec0', mvt_sec0::VARCHAR, echo, ds FROM b
  UNION ALL SELECT 'dsched_band', CASE WHEN d_sched<5400 THEN '1-1.5h' WHEN d_sched<7200 THEN '1.5-2h' WHEN d_sched<10800 THEN '2-3h' ELSE '3-6h' END, echo, ds FROM b
  UNION ALL SELECT 'season', CASE WHEN month(month) IN (1,2,3,11,12) THEN 'winter' ELSE 'summer' END, echo, ds FROM b
  UNION ALL SELECT 'stand_class', CASE WHEN stand IS NULL THEN 'null' WHEN regexp_matches(stand,'^[0-9]+$') THEN 'numeric' ELSE 'alpha' END, echo, ds FROM b)
SELECT m AS marker, v AS value, count(*) FILTER (ds='train') n_train, round(100*avg(echo::INT) FILTER (ds='train'),1) pct_echo_2025,
  count(*) FILTER (ds='rank') n_rank2026
FROM u GROUP BY ALL ORDER BY marker, n_train DESC""",
"LIRF NM-unmatched departures 1-6 h late: echo share (|y-d_sched|<=120 s) by label-free marker (2025), and the count of matching 2026 ranking rows.")
import pandas as pd, numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
d = con.sql(f"WITH b AS ({base}) SELECT * FROM b WHERE ds='train'").df()
d["mon"]=pd.to_datetime(d.month).dt.month
X = pd.DataFrame({"d_sched": d.d_sched, "hour": pd.to_datetime(d.t_mvt).dt.hour, "sched_min": pd.to_datetime(d.t_sched).dt.minute,
     "mvt_sec0": d.mvt_sec0.astype(int), "pfx": d.pfx.astype("category").cat.codes, "fn": d.fn_class.astype("category").cat.codes,
     "stand_num": pd.to_numeric(d.stand, errors="coerce")})
y = d.echo.astype(int).to_numpy(); p = np.zeros(len(d))
for m in range(1,13):
    te = d.mon==m
    if te.sum()==0: continue
    clf = HistGradientBoostingClassifier(max_depth=3, max_iter=100, learning_rate=0.05, categorical_features=[4,5], random_state=0)
    clf.fit(X[~te], y[~te]); p[te] = clf.predict_proba(X[te])[:,1]
auc = roc_auc_score(y, p); auc_ds = roc_auc_score(y, d.d_sched)
open("reports/checks/p6_lirf_echo_classifier_auc.md","w").write("# Check: p6_lirf_echo_classifier_auc\n\n"
 f"Leave-one-month-out HistGradientBoostingClassifier (sklearn, depth 3, 100 iter) predicting echo (|y-d_sched|<=120 s) for LIRF NM-unmatched 2025 departures 1-6 h late (n={len(d)}, echo rate {y.mean():.3f}). "
 f"Inputs: d_sched, take-off hour, schedule minute, MVT second==0, carrier prefix, flight-number class, numeric stand.\n\n"
 f"- AUC (month-held-out) = {auc:.3f}\n- AUC of d_sched alone = {auc_ds:.3f}\n- Brier = {np.mean((p-y)**2):.4f} vs constant-rate Brier = {np.mean((y.mean()-y)**2):.4f}\n")
print(auc, auc_ds, np.mean((p-y)**2), np.mean((y.mean()-y)**2))

# --- hedge evaluation on EXP-031 hold-outs
o = pd.concat([pd.read_parquet(f"models/oof/EXP-031_{k}.parquet")[["mvt_id","y","pred"]] for k in ["jan","jul"]])
TOT = ((o.pred-o.y)**2).sum()
d["p"] = p
rows=[]
for m,k in [(1,"jan"),(7,"jul")]:
    tr = d[(d.mon!=m)]; mn = tr.y[~tr.echo].mean()
    s = d[d.mon==m].merge(o[["mvt_id","pred"]], on="mvt_id")
    s["hedge"] = s.p*s.d_sched + (1-s.p)*mn
    for name,col in [("EXP-031","pred"),("classifier hedge","hedge")]:
        rows.append(dict(fold=k, n=len(s), method=name, pct_total_sq_err=round(100*((s[col]-s.y)**2).sum()/TOT,2)))
    rows.append(dict(fold=k, n=len(s), method="mean(EXP-031, hedge)", pct_total_sq_err=round(100*(((s.pred+s.hedge)/2-s.y)**2).sum()/TOT,2)))
r = pd.DataFrame(rows); print(r)
with open("reports/checks/p6_lirf_echo_classifier_auc.md","a") as f:
    f.write("\n## Hedge with classifier probability on the EXP-031 hold-out rows of this population\n\n"
            "hedge = p_echo*d_sched + (1-p_echo)*mean(y | not echo, other months). % of total EXP-031 Jan+Jul hold-out squared error.\n\n"
            + r.to_markdown(index=False) + "\n")
