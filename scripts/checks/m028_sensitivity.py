"""M-028 robustness on the EXP-078 hold-outs and the 2026 ranking rows.

1. Sensitivity: cross-fitted hold-out RMSE of the ADS-B step for near-stand radius 100 / 150 / 200 m (sources
   still,moving,near) and gate 300 / 600 / 900 s; reference rows = EXP-079 (still,moving) and EXP-080 (150 m, 600 s).
2. Transfer 2025 → 2026 without labels: per source and airport, the gap (offset-corrected ADS-B estimate − base
   prediction) on the 2025 hold-outs vs the 2026 ranking rows, with the EXP-080 final parameters.

  python scripts/checks/m028_sensitivity.py        (needs the adsb.lol tables and the spatial extension)
"""
import numpy as np
import pandas as pd

from prc import db, validate as V
from prc.models import adsb_stack as S
from prc.paths import CHECKS, MODELS, ROOT

BASE = "EXP-078"
SQL = (ROOT / "sql" / "40_adsb" / "05_feat_dep_adsb_near.sql").read_text()

con = db.connect()
for r in (100, 200):
    con.execute(SQL.replace("<= 150", f"<= {r}").replace("feat_dep_adsb_near", f"feat_dep_adsb_near_r{r}"))
con.close()


def crossfit(sources, gate=600, table_near="feat_dep_adsb_near"):
    S.GATE_S, S.BINS = gate, [0, 60, 180, gate]
    S.TABLE["near"] = table_near
    est = S._est(sources)
    frames = {fold: S._fold_frame(BASE, fold, est) for fold in V.HOLDOUTS}
    names, out = list(frames), {}
    for i, fold in enumerate(names):
        model = S.fit_sources(frames[names[1 - i]])
        va = frames[fold]
        p = S.apply_sources(va, va.pred.to_numpy(), model)
        nl = (va.airport != "LIRF") & (va.y <= 10800)
        out[fold] = (V.rmse(va.y, p), V.rmse(va.y[nl], p[nl.to_numpy()]), int((p != va.pred.to_numpy()).sum()))
    return out


rows = []
variants = [("EXP-079: still,moving", ("still", "moving"), 600, "feat_dep_adsb_near")]
variants += [(f"near {r} m, gate 600", ("still", "moving", "near"), 600,
              "feat_dep_adsb_near" if r == 150 else f"feat_dep_adsb_near_r{r}") for r in (100, 150, 200)]
variants += [(f"near 150 m, gate {g}", ("still", "moving", "near"), g, "feat_dep_adsb_near") for g in (300, 900)]
for label, src, gate, tab in variants:
    r = crossfit(src, gate, tab)
    rows.append({"variant": label, "jan": round(r["jan"][0], 2), "jul": round(r["jul"][0], 2),
                 "jan_nonLIRF_y≤3h": round(r["jan"][1], 2), "jul_nonLIRF_y≤3h": round(r["jul"][1], 2),
                 "changed_jan": r["jan"][2], "changed_jul": r["jul"][2]})
sens = pd.DataFrame(rows)

# transfer: gap distribution 2025 hold-outs vs 2026 ranking, EXP-080 final parameters
S.GATE_S, S.BINS, S.TABLE["near"] = 600, [0, 60, 180, 600], "feat_dep_adsb_near"
model = S.load_final_model("EXP-080")
est = S._est(("still", "moving", "near"))
hold = pd.concat([pd.read_parquet(MODELS / "oof" / f"{BASE}_{f}.parquet")[["mvt_id", "airport", "pred"]].assign(year=2025)
                  for f in V.HOLDOUTS])
rank = pd.read_parquet(MODELS / BASE / "pred_rank.parquet")[["mvt_id", "pred"]]
con = db.connect(read_only=True)
ap = con.sql("SELECT mvt_id, airport FROM feat_dep WHERE ds = 'rank'").df()
con.close()
rank = rank.merge(ap, on="mvt_id").assign(year=2026)
d = pd.concat([hold, rank]).merge(est[["mvt_id", "est", "src"]], on="mvt_id")
d["off"] = [model[s]["offset"].get(a, model[s]["pooled_offset"]) for s, a in zip(d.src, d.airport)]
d["gap"] = d.est + d.off - d.pred
n_all = pd.concat([hold, rank]).groupby(["airport", "year"]).size().rename("n_dep")
tr = (d.groupby(["src", "airport", "year"])
      .agg(n=("gap", "size"), within_gate=("gap", lambda g: round(float((g.abs() <= 600).mean()), 3)),
           gap_p10=("gap", lambda g: round(float(g.quantile(0.1)))), gap_med=("gap", lambda g: round(float(g.median()))),
           gap_p90=("gap", lambda g: round(float(g.quantile(0.9)))))
      .reset_index().merge(n_all.reset_index(), on=["airport", "year"]))
tr["share_of_dep"] = (tr.n / tr.n_dep).round(3)

CHECKS.mkdir(parents=True, exist_ok=True)
text = ["# Check: m028_sensitivity", "", f"Base {BASE} hold-out predictions; ADS-B step M-028 cross-fitted as in "
        "`prc.models.adsb_stack eval`. Script: scripts/checks/m028_sensitivity.py.", "",
        "## 1. Sensitivity (hold-out RMSE)", "", sens.to_markdown(index=False), "",
        "## 2. Transfer 2025 → 2026 (no labels): gap = est + offset − base prediction, EXP-080 final parameters", "",
        "`within_gate` = share of rows the step may change (|gap| ≤ 600 s); `share_of_dep` = rows with an estimate / "
        "departures of that airport-year (hold-out months for 2025, ranking for 2026).", "", tr.to_markdown(index=False), ""]
(CHECKS / "m028_sensitivity.md").write_text("\n".join(text))
sens.to_csv(CHECKS / "m028_sensitivity.csv", index=False)
tr.to_csv(CHECKS / "m028_transfer.csv", index=False)
print("\n".join(text))
