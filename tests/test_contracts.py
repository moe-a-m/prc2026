"""Data contracts: every sql/90_checks/*.sql must return zero rows (CLAUDE.md §8)."""
import pytest

from prc import db, manifest

CHECKS = db.sql_files("90_checks")


@pytest.mark.parametrize("path", CHECKS, ids=[p.stem for p in CHECKS])
def test_sql_check_returns_no_rows(con, path):
    rows = con.sql(path.read_text()).fetchall()
    assert rows == [], f"{path.name}: {len(rows)} violating rows, e.g. {rows[:5]}"


def test_ranking_and_submitting_counts(con):
    n_rank = con.sql("SELECT count(*) FROM raw_ranking WHERE PHASE_mvt='DEP'").fetchone()[0]
    n_sub = con.sql("SELECT count(*) FROM raw_submitting").fetchone()[0]
    assert n_rank == n_sub == 344_841


def test_no_stale_raw_files():
    import csv
    with open(manifest.RAW_MANIFEST) as f:
        hashes = {r["sha256"].upper() for r in csv.DictReader(f)}
    assert not hashes & set(manifest.STALE), "manifest lists a pre-reissue (stale) file"
