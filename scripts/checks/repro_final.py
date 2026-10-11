"""Clean-clone reproduction of the final file, member by member (2026-10-11). repro-final-2 (Modal, clean clone of
56c5e76, 2 CPUs, `scripts/modal/reproduce.sh`) ran verify-raw → ingest → clean → features → train → predict →
submit-check from the raw files and kept every member's ranking prediction. Each stage EXP-103–118 is compared per
airport with the original (final fits EXP-103–112 of 2026-10-08, post-chain EXP-113–118 of build-final-1).

  python scripts/checks/repro_final.py <orig_dir> <repro_dir> [<run stdout.log>]
      # <dir>/EXP-###/pred_rank.parquet on each side; the run log (logs/modal/runs/<run>/stdout.log) adds the commit,
      # CPU flags, runtime and final-file SHA256 -> reports/checks/final_reproduction.md
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from prc import db
from prc.paths import CHECKS

STAGES = [(f"EXP-{e}", s) for e, s in zip(range(103, 113), ["lgb s42", "cat s42", "lgb s7", "lgb s99", "lgb s11",
                                                            "lgb s23", "cat s7", "cat s99", "cat s11", "cat s23"])]
STAGES += [("EXP-113", "LightGBM 5-seed average"), ("EXP-114", "CatBoost 5-seed average"), ("EXP-115", "blend"),
           ("EXP-116", "three-regime hedge"), ("EXP-117", "ADS-B step"), ("EXP-118", "LOBT window")]

orig, repro = Path(sys.argv[1]), Path(sys.argv[2])
ap = db.connect(read_only=True).sql("SELECT mvt_id, airport FROM feat_dep WHERE ds = 'rank'").df()
rows, per_ap = [], []
for exp, step in STAGES:
    a, b = orig / exp / "pred_rank.parquet", repro / exp / "pred_rank.parquet"
    if not (a.exists() and b.exists()):
        rows.append({"stage": exp, "step": step, "status": "missing"})
        continue
    m = pd.read_parquet(a).merge(pd.read_parquet(b), on="mvt_id", suffixes=("_o", "_r")).merge(ap, on="mvt_id")
    m["d"] = m.pred_r - m.pred_o
    rows.append({"stage": exp, "step": step, "status": "ok", "rows": len(m),
                 "rows differing": int((m.d != 0).sum()), "max |d| (s)": float(m.d.abs().max()),
                 "rms d (s)": float(np.sqrt((m.d ** 2).mean()))})
    for airport, g in m[m.d != 0].groupby("airport"):
        per_ap.append({"stage": exp, "airport": airport, "rows differing": len(g),
                       "rms d (s)": float(np.sqrt((g.d ** 2).mean())), "max |d| (s)": float(g.d.abs().max())})
run = []
if len(sys.argv) > 3:
    pat = re.compile(r"^(commit |cpu: |avx |elapsed |[0-9a-f]{64}  submissions/)")
    run = ["## Run log", "", "```", *[l for l in Path(sys.argv[3]).read_text().splitlines() if pat.match(l)], "```", ""]
lines = ["# Final-file clean-clone reproduction", "", __doc__.split("\n\n", 1)[0].strip(), "", *run,
         "## Per stage", "", pd.DataFrame(rows).to_markdown(index=False), "",
         "## Airports with differing rows", "",
         pd.DataFrame(per_ap).to_markdown(index=False) if per_ap else "none", ""]
(CHECKS / "final_reproduction.md").write_text("\n".join(lines))
print("\n".join(lines))
