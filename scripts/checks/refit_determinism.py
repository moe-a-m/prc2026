"""Base-model refit determinism (2026-10-10). repro-final-1 (clean clone of e8a3773) reproduced the final file except
48,731 EHAM rows; its model inputs were identical (db_determinism.md). Each final-fit member (EXP-103–112, Modal runs
fin-*, CatBoost on 4 CPUs) was refit on a fresh 2-CPU container (EXP-151–160, runs det-*-2cpu) and compared per
airport with the original prediction of the ranking set.

  python scripts/checks/refit_determinism.py <dir>     # <dir>/EXP-###/pred_rank.parquet for both sides
                                                       -> reports/checks/refit_determinism.md
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from prc import db
from prc.paths import CHECKS

PAIRS = [("lgb", 42, "EXP-103", "EXP-151"), ("cat", 42, "EXP-104", "EXP-152"),
         ("lgb", 7, "EXP-105", "EXP-153"), ("lgb", 99, "EXP-106", "EXP-154"),
         ("lgb", 11, "EXP-107", "EXP-155"), ("lgb", 23, "EXP-108", "EXP-156"),
         ("cat", 7, "EXP-109", "EXP-157"), ("cat", 99, "EXP-110", "EXP-158"),
         ("cat", 11, "EXP-111", "EXP-159"), ("cat", 23, "EXP-112", "EXP-160")]

src = Path(sys.argv[1])
ap = db.connect(read_only=True).sql("SELECT mvt_id, airport FROM feat_dep WHERE ds = 'rank'").df()
rows, per_ap = [], []
for fam, seed, orig, refit in PAIRS:
    a, b = src / orig / "pred_rank.parquet", src / refit / "pred_rank.parquet"
    if not (a.exists() and b.exists()):
        rows.append({"family": fam, "seed": seed, "final fit": orig, "refit": refit, "status": "missing"})
        continue
    m = pd.read_parquet(a).merge(pd.read_parquet(b), on="mvt_id", suffixes=("_o", "_r")).merge(ap, on="mvt_id")
    m["d"] = m.pred_r - m.pred_o
    rows.append({"family": fam, "seed": seed, "final fit": orig, "refit": refit, "status": "ok", "rows": len(m),
                 "rows differing": int((m.d != 0).sum()), "max |d| (s)": float(m.d.abs().max()),
                 "rms d (s)": float(np.sqrt((m.d ** 2).mean()))})
    for airport, g in m[m.d != 0].groupby("airport"):
        per_ap.append({"final fit": orig, "airport": airport, "rows differing": len(g),
                       "rms d (s)": float(np.sqrt((g.d ** 2).mean())), "max |d| (s)": float(g.d.abs().max())})
lines = ["# Base-model refit determinism", "", __doc__.split("\n\n", 1)[0].strip(), "",
         "## Per member", "", pd.DataFrame(rows).to_markdown(index=False), "",
         "## Airports with differing rows", "",
         pd.DataFrame(per_ap).to_markdown(index=False) if per_ap else "none", ""]
(CHECKS / "refit_determinism.md").write_text("\n".join(lines))
print("\n".join(lines))
