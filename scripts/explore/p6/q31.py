"""Combined exploratory post-hoc evaluation of rules R1-R3 on EXP-031 hold-outs (all estimates leave-one-month-out)."""
import sys; sys.path.insert(0,'/tmp/claude-1000/-home-m-opensky-2026/9cdb9da0-8aa7-43e9-ae6c-5d8fa22d5230/scratchpad')
from common import *
import pandas as pd, numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
con=connect()
FN=open('/tmp/claude-1000/-home-m-opensky-2026/9cdb9da0-8aa7-43e9-ae6c-5d8fa22d5230/scratchpad/fn.sql').read()
d = con.sql(f"""SELECT c.mvt_id, month(c.month) mon, c.airport, c.y, c.f_no_nm_match um, epoch(c.t_mvt)-epoch(c.t_sched) d_sched,
  epoch(c.t_mvt)-epoch(c.t_aobt3) px,
  (c.t_aobt3 IS NOT NULL AND NOT c.f_no_nm_match AND abs(epoch(c.t_aobt3)-epoch(c.t_eobt1)) <= 3600 AND epoch(c.t_mvt) >= epoch(c.t_aobt3)) px_ok,
  {FN} fn_class, coalesce(regexp_extract(c.flight_mvt,'^[A-Z]{{3}}'),'?') pfx, second(c.t_mvt)=0 mvt_s0, c.stand, c.t_mvt, c.t_sched
  FROM clean_dep c WHERE c.ds='train'""").df()
o = pd.concat([pd.read_parquet(f"models/oof/EXP-031_{k}.parquet")[["mvt_id","pred"]].assign(fold=k) for k in ["jan","jul"]])
h = o.merge(d, on="mvt_id"); h["new"] = h.pred.astype(float)
lu = d[(d.airport=="LIRF") & d.um].copy()
lu["echo"] = (lu.y-lu.d_sched).abs() <= 120
lu["dm"] = lu.y.between(72000,100800) & ~lu.echo
# R2 classifier for LIRF-unmatched 1-6 h
m16 = lu.d_sched.between(3600,21600)
def X_of(t):
    return pd.DataFrame({"d_sched": t.d_sched, "hour": pd.to_datetime(t.t_mvt).dt.hour, "sched_min": pd.to_datetime(t.t_sched).dt.minute,
        "mvt_s0": t.mvt_s0.astype(int), "pfx": pd.Categorical(t.pfx, categories=sorted(lu.pfx.unique())).codes,
        "fn": pd.Categorical(t.fn_class, categories=sorted(lu.fn_class.unique())).codes, "stand_num": pd.to_numeric(t.stand, errors="coerce")})
for m,k in [(1,"jan"),(7,"jul")]:
    tr = lu[lu.mon!=m]
    # R1: >= 6 h bands
    for lo,hi in [(21600,50400),(50400,1e9)]:
        t = tr[tr.d_sched.between(lo,hi,inclusive="left")]
        pe,pdm = t.echo.mean(), t.dm.mean(); pn = 1-pe-pdm
        mn = t.y[~t.echo & ~t.dm].mean() if pn>0 else 0.0; md = t.y[t.dm].mean() if pdm>0 else 0.0
        sel = (h.fold==k)&(h.airport=="LIRF")&h.um&(h.d_sched>=lo)&(h.d_sched<hi)
        h.loc[sel,"new"] = pe*h.d_sched[sel] + pdm*md + pn*mn
    # R2
    t = tr[m16.loc[tr.index]]
    clf = HistGradientBoostingClassifier(max_depth=3, max_iter=100, learning_rate=0.05, categorical_features=[4,5], random_state=0).fit(X_of(t), t.echo.astype(int))
    mn = t.y[~t.echo].mean()
    sel = (h.fold==k)&(h.airport=="LIRF")&h.um&(h.d_sched>=3600)&(h.d_sched<21600)
    p = clf.predict_proba(X_of(h[sel]))[:,1]
    h.loc[sel,"new"] = 0.5*h.pred[sel] + 0.5*(p*h.d_sched[sel] + (1-p)*mn)
# R3 clip to proxy ±30 min for matched non-suspect rows > 3 h late
sel = h.px_ok & (h.d_sched>10800)
h.loc[sel,"new"] = np.clip(h.pred[sel], h.px[sel]-1800, h.px[sel]+1800)
h["rule"] = np.select([(h.airport=="LIRF")&h.um&(h.d_sched>=21600), (h.airport=="LIRF")&h.um&(h.d_sched>=3600), h.px_ok&(h.d_sched>10800)],
                      ["R1 LIRF-unm >=6h regime hedge","R2 LIRF-unm 1-6h classifier hedge (avg)","R3 matched >3h clip to proxy ±30min"], "unchanged")
rows=[]
for k in ["jan","jul","all"]:
    s = h if k=="all" else h[h.fold==k]
    rows.append(dict(fold=k, n=len(s), rmse_exp031=round(float(np.sqrt(((s.pred-s.y)**2).mean())),2), rmse_rules=round(float(np.sqrt(((s.new-s.y)**2).mean())),2)))
r1 = pd.DataFrame(rows)
r2 = h.groupby(["fold","rule"]).apply(lambda s: pd.Series(dict(n=len(s), sse_exp031=((s.pred-s.y)**2).sum(), sse_rules=((s.new-s.y)**2).sum())), include_groups=False).reset_index()
r2["sse_exp031"]=r2.sse_exp031.map("{:.3e}".format); r2["sse_rules"]=r2.sse_rules.map("{:.3e}".format)
print(r1); print(r2)
r1.to_csv("reports/checks/p6_combined_posthoc_eval.csv", index=False)
open("reports/checks/p6_combined_posthoc_eval.md","w").write("# Check: p6_combined_posthoc_eval\n\n"
 "Exploratory (not an EXP): rules R1-R3 applied to EXP-031 Jan/Jul 2025 hold-out predictions. All probabilities/means/classifiers are "
 "fit on the 11 other 2025 months. R1: LIRF NM-unmatched, d_sched >= 6 h: p_echo*d_sched + p_dayminus*mean(y|dayminus) + p_normal*mean(y|normal) "
 "in bands [6,14) h and >= 14 h. R2: LIRF NM-unmatched, 1-6 h: average of EXP-031 and p_echo*d_sched + (1-p_echo)*mean(y|not echo), p_echo from a "
 "HistGradientBoostingClassifier (d_sched, hour, schedule minute, MVT sec==0, carrier prefix, flight-number class, stand). R3: NM-matched, "
 "proxy not suspect (AOBT_3 present, |AOBT_3-EOBT_1|<=1 h, AOBT_3 <= MVT), d_sched > 3 h: clip prediction to MVT-AOBT_3 ± 1800 s. "
 "Band edges were chosen after viewing all 2025 months (optimistic). Script: scratchpad q31.py.\n\n"
 + r1.to_markdown(index=False) + "\n\n" + r2.to_markdown(index=False) + "\n")

h["gain"] = (h.pred-h.y)**2 - (h.new-h.y)**2
conc=[]
for (k,rule),s in h[h.rule!="unchanged"].groupby(["fold","rule"]):
    g = s.gain.sort_values(ascending=False)
    conc.append(dict(fold=k, rule=rule, n=len(s), n_improved=int((s.gain>0).sum()), n_worse=int((s.gain<0).sum()),
                     total_gain=f"{g.sum():.3e}", top5_share_of_gain=round(float(g.head(5).sum()/g.sum()),3) if g.sum()>0 else None,
                     airports=",".join(sorted(s.airport.unique()))))
c=pd.DataFrame(conc); print(c.to_string())
with open("reports/checks/p6_combined_posthoc_eval.md","a") as f:
    f.write("\n## Concentration of the gain (squared-error reduction per row)\n\n" + c.to_markdown(index=False) + "\n")
