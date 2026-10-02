"""Train/serve parity (CLAUDE.md §3): features must not change when departure BLOCK_TIME / TAXITIME are blank,
as they are for every ranking DEP row. Builds features on a small slice twice and compares."""
import duckdb
import pandas as pd
import pytest

from prc import db, paths

LABEL_COLS = {"y", "f_block_eq_sched", "f_block_eq_planned", "f_round_minute_block", "f_negative_taxi",
              "f_taxi_gt_3h"}
SLICE = "airport IN ('EDDM', 'LIRF') AND t_mvt >= TIMESTAMP '2025-03-10' AND t_mvt < TIMESTAMP '2025-03-12'"


def build(blank_dep_labels: bool) -> pd.DataFrame:
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    con.execute(f"ATTACH '{paths.DB}' AS src (READ_ONLY)")
    con.execute(f"CREATE TABLE stg_mvt AS SELECT * FROM src.stg_mvt WHERE {SLICE}")
    con.execute("CREATE TABLE stg_metar AS SELECT * FROM src.stg_metar WHERE station IN ('EDDM', 'LIRF')")
    for t in ['raw_ec_taxi', 'raw_ec_predep', 'raw_ec_slot']:  # small external tables, copied whole
        con.execute(f"CREATE TABLE {t} AS SELECT * FROM src.{t}")
    if blank_dep_labels:
        con.execute("UPDATE stg_mvt SET t_block = NULL, y = NULL WHERE phase = 'DEP'")
    con.execute("DETACH src")
    for stage, prefix in [("10_stage", "02"), ("20_clean", ""), ("30_features", "")]:
        db.run_stage(con, stage, verbose=False, prefix=prefix)
    side = [t for (t,) in con.sql("SELECT table_name FROM duckdb_tables() WHERE table_name LIKE 'feat_dep_%' "
                                  "AND table_name <> 'feat_dep_base' ORDER BY 1").fetchall()]
    df = con.sql("SELECT * FROM feat_dep " + " ".join(f"LEFT JOIN {t} USING (mvt_id)" for t in side)
                 + " ORDER BY mvt_id").df()
    con.close()
    return df


@pytest.fixture(scope="module")
def pair(con):  # `con` fixture skips when the DuckDB file is missing
    return build(False), build(True)


def test_slice_not_empty(pair):
    full, _ = pair
    assert len(full) > 500 and full.y.notna().all()


def test_features_identical_without_dep_labels(pair):
    full, blank = pair
    assert list(full.mvt_id) == list(blank.mvt_id)
    cols = [c for c in full.columns if c not in LABEL_COLS]
    pd.testing.assert_frame_equal(full[cols], blank[cols], check_dtype=False)


def test_model_config_has_no_label_columns():
    from prc.models.gbm import load_config
    cfg = load_config("configs/gbm.yaml")
    used = set(cfg["numeric"]) | set(cfg["categorical"]) | {k for ks in cfg["target_encodings"] for k in ks}
    assert not used & (LABEL_COLS | {"t_block", "mvt_id", "t_mvt_epoch"})


def test_blanking_took_effect(pair):
    _, blank = pair
    assert blank.y.isna().all() and blank.f_negative_taxi.isna().all()
