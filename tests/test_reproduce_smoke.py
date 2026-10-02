"""End-to-end smoke test on a tiny slice (CLAUDE.md §5): SQL features -> OOF target encodings -> LightGBM -> predict.
Uses two airports, two days of training data and two days of ranking data, so a broken stage fails on every commit."""
import duckdb
import numpy as np
import pandas as pd
import pytest

from prc import db, paths
from prc.models import gbm

SLICE = ("airport IN ('EDDM', 'LIRF') AND ((t_mvt >= TIMESTAMP '2025-03-10' AND t_mvt < TIMESTAMP '2025-03-12') "
         "OR (t_mvt >= TIMESTAMP '2025-04-10' AND t_mvt < TIMESTAMP '2025-04-12') "
         "OR (t_mvt >= TIMESTAMP '2026-01-10' AND t_mvt < TIMESTAMP '2026-01-12'))")


@pytest.fixture(scope="module")
def frame(con):
    c = duckdb.connect()
    c.execute("SET TimeZone = 'UTC'")
    c.execute(f"ATTACH '{paths.DB}' AS src (READ_ONLY)")
    c.execute(f"CREATE TABLE stg_mvt AS SELECT * FROM src.stg_mvt WHERE {SLICE}")
    c.execute("CREATE TABLE stg_metar AS SELECT * FROM src.stg_metar WHERE station IN ('EDDM', 'LIRF')")
    c.execute("DETACH src")
    for stage, prefix in [("10_stage", "02"), ("20_clean", ""), ("30_features", "")]:
        db.run_stage(c, stage, verbose=False, prefix=prefix)
    side = [t for (t,) in c.sql("SELECT table_name FROM duckdb_tables() WHERE table_name LIKE 'feat_dep_%' "
                                "AND table_name <> 'feat_dep_base' ORDER BY 1").fetchall()]
    df = c.sql("SELECT * FROM feat_dep " + " ".join(f"LEFT JOIN {t} USING (mvt_id)" for t in side)
               + " ORDER BY mvt_id").df()
    c.close()
    df["ap_runway"] = df.airport + "_" + df.runway.fillna("NA")
    df["ap_stand"] = df.airport + "_" + df.stand.fillna("NA")
    df["month"] = pd.to_datetime(df.month)
    return df


def test_slice_has_train_and_rank(frame):
    assert set(frame.ds) == {"train", "rank"}
    assert frame.loc[frame.ds == "rank", "y"].isna().all()


def test_fit_predict_end_to_end(frame):
    cfg = gbm.load_config("configs/ablations/EXP-018_weather.yaml")
    cfg["numeric"] += ["n_rw_takeoffs_since_aobt3", "n_rw_takeoffs_since_sched", "d_aobt3_minus_default"]
    cfg["te_quantiles"] = {0.1: [["airport", "stand", "runway"]]}
    cfg["num_boost_round"] = 20
    cfg["params"] = dict(cfg["params"], min_data_in_leaf=5, num_leaves=15, min_data_per_group=5)
    tr = (frame.ds == "train").to_numpy()
    X = gbm.design(frame, cfg, tr)
    assert list(X.columns[: len(cfg["numeric"])]) == cfg["numeric"]
    assert "te_q10_airport_stand_runway" in X and "te_q10_airport_stand_runway_n" not in X
    # OOF encodings: a training row never sees its own month
    assert X.loc[tr, "te_airport_stand_runway_n"].max() < tr.sum()
    b = gbm.fit(X[tr], frame.y[tr].to_numpy(float), cfg, seed=1)
    p = b.predict(X[~tr])
    assert len(p) == (~tr).sum() and np.isfinite(p).all()


def test_nn_fit_predict_end_to_end(frame):
    from prc.models import nn as tabnn
    cfg = gbm.load_config("configs/nn.yaml")
    cfg["nn"] = dict(cfg["nn"], epochs=1, hidden=[16], batch_size=256, min_count=1, threads=1)
    tr = (frame.ds == "train").to_numpy()
    X = gbm.design(frame, cfg, tr)
    (p,) = tabnn.train_predict(X[tr], frame.y[tr].to_numpy(float), [X[~tr]], cfg, seed=1)
    assert len(p) == (~tr).sum() and np.isfinite(p).all()
