"""Exposure of the final ranking months to snow / freezing conditions, against the same months of 2025.

Follow-up of scripts/checks/winter_snow_days.py (reports/checks/winter_snow_days.md): on the 2025 hold-outs the final
recipe under-predicts departures with snow or freezing reported in the 3 h before take-off, most at LTFM and most
when AOBT_3_flt is missing. How many such departures are in January / February 2026 (final_ranking.parquet)?
Same weather and NM-status definitions as winter_snow_days.py; label-free, so train and rank rows are counted alike.

  python scripts/checks/winter_snow_exposure.py      -> reports/checks/winter_snow_exposure.md
"""
import pandas as pd

from prc import db
from prc import validate as V
from prc.paths import CHECKS

SQL = """
WITH day_wx AS (
    SELECT station AS airport, CAST(t_obs AS DATE) AS d, bool_or(wx_snow OR wx_freezing) AS day_snow
    FROM stg_metar GROUP BY ALL
),
r AS (
    SELECT f.ds, strftime(f.month, '%Y-%m') AS ym, f.airport,
           CAST(timezone('UTC', to_timestamp(f.t_mvt_epoch)) AS DATE) AS d,
           coalesce(w.wx3h_snow, false) OR coalesce(w.wx3h_freezing, false) AS wx3h,
           f.d_aobt3 IS NULL AS no_aobt3, coalesce(x.day_snow, false) AS day_snow
    FROM feat_dep f
    LEFT JOIN feat_dep_wx w USING (mvt_id)
    LEFT JOIN day_wx x ON x.airport = f.airport AND x.d = CAST(timezone('UTC', to_timestamp(f.t_mvt_epoch)) AS DATE)
    WHERE month(f.month) IN (1, 2)
)
SELECT ds, ym, airport, count(*) AS n_dep,
       count(DISTINCT CASE WHEN day_snow THEN d END) AS snow_days,
       sum(wx3h::INT) AS n_wx3h,
       sum((wx3h AND no_aobt3)::INT) AS n_wx3h_no_aobt3,
       sum(no_aobt3::INT) AS n_no_aobt3,
       round(100.0 * sum(wx3h::INT) / count(*), 2) AS pct_wx3h
FROM r GROUP BY ALL ORDER BY airport, ym
"""


def main():
    con = db.connect(read_only=True)
    t = con.sql(SQL).df()
    con.close()
    tot = t.groupby(["ds", "ym"])[["n_dep", "n_wx3h", "n_wx3h_no_aobt3", "n_no_aobt3"]].sum()
    piv = t.pivot(index="airport", columns="ym", values=["snow_days", "n_wx3h", "n_wx3h_no_aobt3"]).fillna(0).astype(int)
    lines = ["# Snow / freezing exposure: January and February, 2025 vs 2026 (final ranking)", "",
             __doc__.split("\n\n", 1)[1].strip(), "",
             f"- data: {V.data_version()}, git: {V.git_sha()}", "",
             "## Totals per month", "", tot.to_markdown(), "",
             "## Per airport: snow days, departures with snow/freezing in the 3 h before take-off, of which AOBT_3 missing",
             "", piv.to_markdown(), "",
             "## Long table", "", t.to_markdown(index=False), ""]
    out = CHECKS / "winter_snow_exposure.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
