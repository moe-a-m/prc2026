"""M-030 paired comparison: hold-out predictions of a reference and robust-label variants (after the M-026 hedge),
overall, non-LIRF y ≤ 3 h, LIRF split by NM match and label range.

  python scripts/checks/m030_paired.py REF VARIANT [VARIANT ...]     (reads models/oof/<EXP>_{jan,jul}.parquet)
"""
import sys

import numpy as np
import pandas as pd

from prc import db
from prc.paths import CHECKS, MODELS

exps = sys.argv[1:]
con = db.connect(read_only=True)
um = con.sql("SELECT mvt_id, coalesce(nm_unmatched, false) AS um FROM feat_dep WHERE ds = 'train'").df()
rows = []
for fold in ("jan", "jul"):
    base = pd.read_parquet(MODELS / "oof" / f"{exps[0]}_{fold}.parquet")[["mvt_id", "airport", "y"]].merge(um, on="mvt_id")
    for e in exps:
        p = pd.read_parquet(MODELS / "oof" / f"{e}_{fold}.parquet")[["mvt_id", "pred"]]
        d = base.merge(p, on="mvt_id")
        lirf = d.airport == "LIRF"
        groups = {"all": np.ones(len(d), bool), "non-LIRF y≤3h": ~lirf & (d.y <= 10800),
                  "LIRF matched y≤3h": lirf & ~d.um & (d.y <= 10800), "LIRF unmatched y≤3h": lirf & d.um & (d.y <= 10800),
                  "LIRF y>3h": lirf & (d.y > 10800), "non-LIRF y>3h": ~lirf & (d.y > 10800)}
        for g, m in groups.items():
            m = np.asarray(m)
            rows.append({"fold": fold, "exp": e, "group": g, "n": int(m.sum()),
                         "rmse": round(float(np.sqrt(((d.y[m] - d.pred[m]) ** 2).mean())), 2),
                         "sse_share_of_all": round(float(((d.y[m] - d.pred[m]) ** 2).sum() / ((d.y - d.pred) ** 2).sum()), 3)})
out = pd.DataFrame(rows).pivot_table(index=["fold", "group"], columns="exp", values="rmse").reset_index()
name = "m030_paired_" + "_".join(exps)
CHECKS.mkdir(parents=True, exist_ok=True)
pd.DataFrame(rows).to_csv(CHECKS / f"{name}.csv", index=False)
(CHECKS / f"{name}.md").write_text(f"# Check: {name}\n\nHold-out RMSE by group, {exps[0]} = reference "
                                   f"(M-030, docs/METHODS.md). Script: scripts/checks/m030_paired.py.\n\n"
                                   + out.to_markdown(index=False) + "\n")
print(out.to_string())
