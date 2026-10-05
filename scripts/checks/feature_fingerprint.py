"""Order-independent fingerprint of every column of the model input tables (reproducibility check).

Per column: non-null count and bit_xor(hash(mvt_id, value)) — equal fingerprints mean identical values per mvt_id.
Floating columns are rounded to 6 decimals first so that last-bit differences are visible separately (`raw` hash).

  python scripts/checks/feature_fingerprint.py out.csv
"""
import sys

import pandas as pd

from prc import db

TABLES = ["feat_dep", "feat_dep_wx", "feat_dep_ec", "feat_dep_adsb", "feat_dep_adsb_stand"]
con = db.connect(read_only=True)
rows = []
for t in TABLES:
    for name, typ, *_ in con.sql(f"DESCRIBE {t}").fetchall():
        if name == "mvt_id":
            continue
        q = f'"{name}"'
        rounded = f"round({q}, 6)" if typ in ("DOUBLE", "FLOAT") or typ.startswith("DECIMAL") else q
        n, h_raw, h_round = con.sql(f"SELECT count({q}), bit_xor(hash(mvt_id, {q})), bit_xor(hash(mvt_id, {rounded})) "
                                    f"FROM {t}").fetchone()
        rows.append({"table": t, "column": name, "type": typ, "n": n, "hash_raw": str(h_raw), "hash_round6": str(h_round)})
out = pd.DataFrame(rows)
out.to_csv(sys.argv[1], index=False)
print(f"{len(out)} columns fingerprinted -> {sys.argv[1]}")
