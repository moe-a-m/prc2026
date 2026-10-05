"""Feature SQL must not depend on the arbitrary order of tied timestamps (reproducibility, CLAUDE.md §1.8).

Regression for the queue counts found non-reproducible on 2026-10-05 (row_number() over minute-rounded AOBT_3):
- every row_number() in the feature stages ends its ORDER BY with a unique key (mvt_id, or icao24 + segment);
- cumulative counts use count(*) with the default RANGE frame, which includes ties;
- every lag()/lead() window in the feature stages orders by mvt_id after the time column.
"""
import re

import duckdb

from prc.paths import SQL


def _feature_sql():
    out = {}
    for stage in ("30_features", "40_adsb"):
        for p in sorted((SQL / stage).glob("*.sql")):
            out[p] = "\n".join(line.split("--")[0] for line in p.read_text().splitlines())  # drop comments
    return out


def test_row_number_orders_end_with_a_unique_key():
    bad = []
    for p, s in _feature_sql().items():
        for m in re.finditer(r"row_number\(\)\s+OVER\s*\(([^)]*\([^)]*\)[^)]*|[^)]*)\)", s):
            order = m.group(1).split("ORDER BY")[-1]
            if not re.search(r"\b(mvt_id|air_seg)\s*$", order.strip()):
                bad.append(f"{p.name}: {m.group(0)}")
    assert not bad, f"row_number() without a unique tie-break: {bad}"


def test_cumulative_event_counts_include_ties():
    s = (SQL / "30_features" / "01_feat_events.sql").read_text()
    assert "count(*) OVER (PARTITION BY airport, kind ORDER BY ts) AS cnt" in s


def test_runway_sequence_window_has_tie_breaker():
    s = (SQL / "30_features" / "02_feat_dep.sql").read_text()
    assert re.search(r"WINDOW w AS \(PARTITION BY airport, runway ORDER BY t_mvt, mvt_id\)", s)


def test_count_window_includes_ties():
    con = duckdb.connect()
    r = con.sql("""SELECT ts, count(*) OVER (ORDER BY ts) AS cnt
                   FROM (VALUES (1), (2), (2), (3)) t(ts) ORDER BY ts""").fetchall()
    assert [c for _, c in r] == [1, 3, 3, 4]  # tied rows get the same count = events at or before ts
