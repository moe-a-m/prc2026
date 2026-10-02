"""Run SQL stages in order: `python -m prc.pipeline 00_ingest 10_stage ...`.

`stage:prefix` runs only the files of that stage whose name starts with prefix (e.g. `30_features:03`).
"""
import sys

from prc import db

if __name__ == "__main__":
    con = db.connect()
    for arg in sys.argv[1:]:
        stage, _, prefix = arg.partition(":")
        print(f"[{arg}]")
        db.run_stage(con, stage, prefix=prefix)
    con.close()
