"""Full-year hold-out check of the v11 recipe (final phase: organizer e-mail 2026-10-08, METHODS M-001 full-year variant).

Base: PRC_HOLDOUTS=all hold-out predictions of the v11 base models, 5-seed averages EXP-145 (LightGBM, EXP-135–139)
and EXP-146 (CatBoost, EXP-140–144). Two ways to apply the post-steps, reported per month and for Jan/Jul, Feb/Jun,
the other eight months and all twelve:

  A  frozen v11 parameters, as in the submission: blend weights from EXP-115, M-026 regime table fit on the training
     months without the hold-out month (as `hedge eval3`), ADS-B parameters from EXP-117, LOBT projection (M-031).
     The EXP-115 / EXP-117 parameters were fit on Jan + Jul 2025, so A is in-sample for those two months only.
  B  leave-one-month-out cross-fit chain EXP-147 (blend) → EXP-148 (hedge) → EXP-149 (ADS-B) → EXP-150 (LOBT).

  PRC_HOLDOUTS=all python scripts/checks/fullyear_summary.py      -> reports/checks/fullyear_v11_recipe.md
"""
import json
import re

import numpy as np
import pandas as pd

from prc import validate as V
from prc.models import adsb_stack as A
from prc.models import hedge as H
from prc.models import lobt_window as L
from prc.paths import CHECKS, MODELS, REPORTS

LGB, CAT = "EXP-145", "EXP-146"
CHAIN = ["EXP-145", "EXP-146", "EXP-147", "EXP-148", "EXP-149", "EXP-150"]
SOURCES = ("still", "moving", "near")
GROUPS = {"Jan/Jul": ["jan", "jul"], "Feb/Jun": ["feb", "jun"],
          "other 8": [m for m in V.MONTHS if m not in ("jan", "jul", "feb", "jun")], "all 12": V.MONTHS}


def oof(exp, fold):
    return pd.read_parquet(MODELS / "oof" / f"{exp}_{fold}.parquet")


def frozen_weights():
    rep = (REPORTS / "experiments" / "EXP-115.md").read_text()
    w = json.loads(re.search(r"- final_weights: (\{.*\})", rep).group(1))
    return {LGB: w["EXP-113"], CAT: w["EXP-114"]}   # EXP-113/114 = 5-seed averages of the same configs


def variant_a(folds):
    w = frozen_weights()
    f = H._frame()
    tr = f[f.ds == "train"]
    est = A._est(SOURCES)
    adsb = A.load_final_model("EXP-117")
    d_lobt = L._d_lobt()
    out = {}
    for fold, d in folds.items():
        va = oof(LGB, fold)
        va["pred"] = w[LGB] * va.pred.to_numpy() + w[CAT] * oof(CAT, fold).set_index("mvt_id").loc[va.mvt_id, "pred"].to_numpy()
        va = va.merge(f[["mvt_id", "d_sched", "nm_unmatched", "day_shift"]], on="mvt_id")
        va["pred"] = H.apply_regimes(va, va.pred.to_numpy(), H.fit_regimes(tr[tr.month != pd.Timestamp(d)]))
        va = va.merge(est[["mvt_id", "est", "src"]], on="mvt_id", how="left")
        va["pred"] = A.apply_sources(va, va.pred.to_numpy(), adsb)
        va = va.merge(d_lobt, on="mvt_id", how="left")
        va["pred"] = L.project(va.pred.to_numpy(), va.d_lobt)
        out[fold] = va
    return out


def rmse_rows(frames: dict, label: str):
    rows = [{"variant": label, "months": m, "n": len(frames[m]), "rmse": V.rmse(frames[m].y, frames[m].pred)}
            for m in frames]
    for g, ms in GROUPS.items():
        c = pd.concat([frames[m] for m in ms if m in frames])
        rows.append({"variant": label, "months": g, "n": len(c), "rmse": V.rmse(c.y, c.pred)})
    return rows


def main():
    folds = V.HOLDOUTS
    assert list(folds) == V.MONTHS, "run with PRC_HOLDOUTS=all"
    a = variant_a(folds)
    b = {m: oof("EXP-150", m) for m in folds}
    for m in folds:   # both variants score the same rows
        assert len(a[m]) == len(b[m]) and set(a[m].mvt_id) == set(b[m].mvt_id), m
    table = pd.DataFrame(rmse_rows(a, "A frozen v11 parameters") + rmse_rows(b, "B leave-one-month-out refit"))
    wide = table.pivot(index="months", columns="variant", values="rmse").reindex(V.MONTHS + list(GROUPS)).round(2)
    wide.insert(0, "n", table.drop_duplicates("months").set_index("months").n.reindex(wide.index))
    stages = pd.DataFrame({e: {m: V.rmse(oof(e, m).y, oof(e, m).pred) for m in folds} |
                           {g: V.rmse(pd.concat([oof(e, m) for m in ms]).y, pd.concat([oof(e, m) for m in ms]).pred)
                            for g, ms in GROUPS.items()} for e in CHAIN}).round(2)
    per_airport = pd.DataFrame({g: {ap: V.rmse(x.y, x.pred) for ap, x in pd.concat([a[m] for m in ms]).groupby("airport")}
                                for g, ms in GROUPS.items()}).round(1)
    lines = ["# Full-year hold-out check of the v11 recipe", "", __doc__.split("\n\n", 1)[1].strip(), "",
             f"- data: {V.data_version()}, git: {V.git_sha()}", "",
             "## RMSE per hold-out month and month group (s)", "", wide.to_markdown(), "",
             "## Chain stages, variant B (RMSE, s)", "", stages.to_markdown(), "",
             "## Per airport, variant A (RMSE, s)", "", per_airport.to_markdown(), ""]
    out = CHECKS / "fullyear_v11_recipe.md"
    out.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
