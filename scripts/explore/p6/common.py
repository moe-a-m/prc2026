import sys
sys.path.insert(0, '/home/m/opensky/2026/src')
from prc import db
import time
def connect():
    for i in range(10):
        try:
            return db.connect(read_only=True)
        except Exception as e:
            print('lock?', e); time.sleep(60)
    raise SystemExit('no db')
OOF = """oof AS (SELECT mvt_id, y AS y_oof, pred, (pred-y)*(pred-y) AS se, CASE WHEN month(month)=1 THEN 'jan' ELSE 'jul' END fold
             FROM read_parquet('models/oof/EXP-031_j*.parquet')),
tot AS (SELECT sum(se) tot_se FROM oof)"""
def run(con, name, sql, note):
    df = db.save_check(con, name, sql, note)
    import pandas as pd
    with pd.option_context('display.width', 250, 'display.max_columns', 40, 'display.max_rows', 200):
        print(df)
    return df
