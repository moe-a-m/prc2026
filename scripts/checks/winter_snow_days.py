"""Snow / freezing days in the full-year hold-outs: how the final recipe (variant A of fullyear_summary.py = frozen
v11 parameters, as submitted) does on departures at snow or freezing conditions, split by NM off-block status.

Prompted by a forum question (10/10/2026 07:05: "February brings de-icing and snow
days. For flights without an NM off-block time on those days, did anything beat the base model?"). Descriptive check
only, no model change. Weather flags from stg_metar (M-012: wx_snow = SN|SG|PL, wx_freezing = FZ in IEM wxcodes):

  wx3h      snow or freezing reported in the 3 h before take-off (feat_dep_wx.wx3h_snow / wx3h_freezing)
  wx_day    no such report in those 3 h, but one at the airport on the same UTC day
  dry       no snow/freezing report at the airport that UTC day

NM off-block status (M-004, feat_dep.d_aobt3, feat_dep_nm.aobt3_at_default):
  no_aobt3        AOBT_3_flt missing
  aobt3_default   MVT − AOBT_3 on the NM default taxi minute (little off-block information)
  aobt3_info      AOBT_3 present and off the default

Scope: hold-out months Nov–Mar 2025 (the snow season; nearly all wx rows fall there). bias = mean(pred − y).

  PRC_HOLDOUTS=all python scripts/checks/winter_snow_days.py      -> reports/checks/winter_snow_days.md
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fullyear_summary as FY  # noqa: E402
from prc import db  # noqa: E402
from prc import validate as V  # noqa: E402
from prc.paths import CHECKS  # noqa: E402

WINTER = ["nov", "dec", "jan", "feb", "mar"]

SQL = """
WITH day_wx AS (
    SELECT station AS airport, CAST(t_obs AS DATE) AS d, bool_or(wx_snow OR wx_freezing) AS day_snow
    FROM stg_metar GROUP BY ALL
)
SELECT f.mvt_id,
       CASE WHEN coalesce(w.wx3h_snow, false) OR coalesce(w.wx3h_freezing, false) THEN 'wx3h'
            WHEN coalesce(x.day_snow, false) THEN 'wx_day' ELSE 'dry' END AS wx,
       CASE WHEN f.d_aobt3 IS NULL THEN 'no_aobt3'
            WHEN n.aobt3_at_default THEN 'aobt3_default' ELSE 'aobt3_info' END AS nm,
       CAST(timezone('UTC', to_timestamp(f.t_mvt_epoch)) AS DATE) AS d
FROM feat_dep f
LEFT JOIN feat_dep_wx w USING (mvt_id)
LEFT JOIN feat_dep_nm n USING (mvt_id)
LEFT JOIN day_wx x ON x.airport = f.airport AND x.d = CAST(timezone('UTC', to_timestamp(f.t_mvt_epoch)) AS DATE)
WHERE f.ds = 'train'
"""


def summary(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    tot = float(((df.pred - df.y) ** 2).sum())
    g = df.assign(e=df.pred - df.y, se=(df.pred - df.y) ** 2).groupby(keys, observed=True)
    out = pd.DataFrame({"n": g.size(), "rmse": np.sqrt(g.se.mean()), "bias": g.e.mean(),
                        "mean_y": g.y.mean(), "share_sq_err_%": 100 * g.se.sum() / tot})
    return out.round(1)


def main():
    folds = {m: d for m, d in V.HOLDOUTS.items() if m in WINTER}
    assert set(folds) == set(WINTER), "run with PRC_HOLDOUTS=all"
    a = FY.variant_a(folds)
    con = db.connect(read_only=True)
    lab = con.sql(SQL).df()
    con.close()
    df = pd.concat([a[m].assign(hold_month=m) for m in WINTER])[["mvt_id", "airport", "hold_month", "y", "pred"]]
    df = df.merge(lab, on="mvt_id", how="left")
    assert df.wx.notna().all() and len(df) == df.mvt_id.nunique()
    df["wx"] = pd.Categorical(df.wx, ["wx3h", "wx_day", "dry"])
    df["nm"] = pd.Categorical(df.nm, ["no_aobt3", "aobt3_default", "aobt3_info"])
    days = df[df.wx != "dry"].groupby(["airport", "hold_month"], observed=True).d.nunique().unstack().fillna(0)

    snow_ap = df[df.wx != "dry"].airport.unique()
    feb = df[df.hold_month == "feb"]
    lines = ["# Snow / freezing days in the full-year hold-outs (final recipe, variant A)", "",
             __doc__.split("\n\n", 1)[1].strip(), "",
             f"- data: {V.data_version()}, git: {V.git_sha()}", f"- rows: {len(df)} (Nov–Mar hold-outs)", "",
             "## Days with any snow/freezing report, per airport and hold-out month", "",
             days.reindex(columns=[m for m in WINTER if m in days.columns]).astype(int).to_markdown(), "",
             "## Nov–Mar, all airports: weather × NM status", "", summary(df, ["wx", "nm"]).to_markdown(), "",
             "## February only: weather × NM status", "", summary(feb, ["wx", "nm"]).to_markdown(), "",
             "## Nov–Mar, airports with snow/freezing days: airport × weather × (AOBT_3 missing?)", "",
             summary(df[df.airport.isin(snow_ap)].assign(no_aobt3=lambda x: x.nm == "no_aobt3"),
                     ["airport", "wx", "no_aobt3"]).to_markdown(), ""]
    out = CHECKS / "winter_snow_days.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
