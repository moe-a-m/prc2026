"""Residual corrector on hold-out base predictions (M-020, CLAUDE.md §10 P5).

A small LightGBM learns r = y − base_pred from the base prediction and label-defect/context inputs. Cross-fitted on
the two hold-out months: fit on Jan-2025 hold-out predictions, evaluate on Jul-2025, and vice versa, so the corrector
is never scored on the month it was fit on. For the ranking set it is fit on both months.

  python -m prc.models.corrector --base EXP-022 --exp-id EXP-026
"""
import argparse
import json

import lightgbm as lgb
import numpy as np
import pandas as pd

from prc import db, validate as V
from prc.paths import MODELS

FEATURES = ["base_pred", "airport", "nm_unmatched", "d_sched", "day_shift", "actype_mvt_missing", "flt_prefix",
            "hour_local", "d_aobt3", "d_eobt1", "aobt3_round_minute"]
CATS = ["airport", "flt_prefix"]
PARAMS = {"objective": "regression", "learning_rate": 0.05, "num_leaves": 15, "min_data_in_leaf": 300,
          "lambda_l2": 50.0, "feature_fraction": 0.9, "bagging_fraction": 0.8, "bagging_freq": 1, "deterministic": True,
          "force_row_wise": True, "num_threads": 4, "verbose": -1, "seed": 7}
ROUNDS = 300


def context():
    con = db.connect(read_only=True)
    f = con.sql(f"SELECT mvt_id, {', '.join(c for c in FEATURES if c != 'base_pred')} FROM feat_dep").df()
    con.close()
    return f


def frame(d: pd.DataFrame, ctx: pd.DataFrame) -> pd.DataFrame:
    x = d[["mvt_id", "pred"]].rename(columns={"pred": "base_pred"}).merge(ctx, on="mvt_id", how="left")
    X = x[FEATURES].copy()
    for c in CATS:
        X[c] = X[c].astype("category")
    for c in ["nm_unmatched", "actype_mvt_missing", "aobt3_round_minute"]:
        X[c] = X[c].astype(float)
    return X


def fit(X, r):
    return lgb.train(PARAMS, lgb.Dataset(X, r, categorical_feature=CATS), num_boost_round=ROUNDS)


def main(base, exp_id):
    ctx = context()
    folds = {k: pd.read_parquet(MODELS / "oof" / f"{base}_{k}.parquet") for k in V.HOLDOUTS}
    names = list(folds)
    res = {}
    for i, fold in enumerate(names):
        tr = folds[names[1 - i]]
        Xtr = frame(tr, ctx)
        m = fit(Xtr, (tr.y - tr.pred).to_numpy(float))
        va = folds[fold].copy()
        Xva = frame(va, ctx)
        # categories must match the training frame
        for c in CATS:
            Xva[c] = pd.Categorical(Xva[c].astype(object), categories=Xtr[c].cat.categories)
        va["pred"] = va.pred + m.predict(Xva)
        res[fold] = va
    meta = {"base": base, "features": json.dumps(FEATURES), "params": json.dumps(PARAMS), "rounds": ROUNDS,
            "data": V.data_version(), "git": V.git_sha()}
    text = V.report_md(exp_id, f"Cross-fitted residual corrector on {base}", res, meta)
    text += "\n## Base alone\n\n" + pd.DataFrame({k: [round(V.rmse(v.y, v.pred), 2)] for k, v in folds.items()}).to_markdown(index=False) + "\n"
    V.write_report(exp_id, text)
    for fold, va in res.items():
        va.to_parquet(MODELS / "oof" / f"{exp_id}_{fold}.parquet")
    r = {k: round(V.rmse(v.y, v.pred), 2) for k, v in res.items()}
    print(exp_id, r, "base", {k: round(V.rmse(v.y, v.pred), 2) for k, v in folds.items()})
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--exp-id", required=True)
    a = ap.parse_args()
    main(a.base, a.exp_id)
