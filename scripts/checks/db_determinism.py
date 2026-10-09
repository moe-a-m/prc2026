"""Compare the feature tables of the working DB (data/prc.duckdb, rebuilt from raw in this run) with a reference DB
built earlier from the same raw files and SQL — row-level, per airport. Motivated by repro-final-1 (2026-10-09):
a clean-clone rebuild reproduced the final file except 48,731 EHAM rows.

  python scripts/checks/db_determinism.py /vol/prc.duckdb      -> reports/checks/db_determinism.md
"""
import sys

from prc import db
from prc.paths import CHECKS

REF = sys.argv[1]
TABLES = ["feat_dep", "feat_dep_recent", "feat_dep_wx"]   # every table the final models read (gbm.load_frame)

con = db.connect(read_only=False)
con.sql(f"ATTACH '{REF}' AS ref (READ_ONLY)")
lines = ["# DB determinism: working DB vs reference", "", f"reference: `{REF}`", ""]
for t in TABLES:
    try:
        cols = [r[0] for r in con.sql(f"DESCRIBE {t}").fetchall()]
        rcols = [r[0] for r in con.sql(f"DESCRIBE ref.{t}").fetchall()]
    except Exception as e:  # noqa: BLE001 — table missing in one DB
        lines += [f"## {t}: not comparable ({e})", ""]
        continue
    common = [c for c in cols if c in rcols]
    sel = ", ".join(f'"{c}"' for c in common)
    n_a = con.sql(f"SELECT count(*) FROM {t}").fetchone()[0]
    n_b = con.sql(f"SELECT count(*) FROM ref.{t}").fetchone()[0]
    diff = con.sql(f"SELECT * FROM (SELECT {sel} FROM {t} EXCEPT ALL SELECT {sel} FROM ref.{t})").df()
    lines += [f"## {t}", "", f"rows: working {n_a:,}, reference {n_b:,}; columns compared {len(common)}; "
              f"rows of the working table not in the reference: {len(diff):,}", ""]
    if len(diff) and "mvt_id" in common:
        ids = ",".join(str(int(x)) for x in diff.mvt_id.head(20000))
        per_col = []
        for c in common:
            if c == "mvt_id":
                continue
            n = con.sql(f"""SELECT count(*) FROM {t} a JOIN ref.{t} b USING (mvt_id)
                            WHERE a."{c}" IS DISTINCT FROM b."{c}" """).fetchone()[0]
            if n:
                per_col.append((c, n))
        lines += ["columns that differ (rows):", ""] + [f"- {c}: {n:,}" for c, n in per_col] + [""]
        if "airport" in common:
            by_ap = diff.groupby("airport").size().to_dict()
            lines += [f"differing rows per airport: {by_ap}", ""]
        if "ds" in common:
            lines += [f"differing rows per ds: {diff.groupby('ds').size().to_dict()}", ""]
CHECKS.mkdir(parents=True, exist_ok=True)
(CHECKS / "db_determinism.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
