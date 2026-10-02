"""Blend hold-out predictions of several experiments (M-019): non-negative least squares without intercept.

Cross-fitted to avoid tuning on the scored validation month: weights fit on Jan-2025 are evaluated on Jul-2025 and
vice versa. Final weights (for the ranking set) are fit on both folds together.

  python -m prc.models.blend --members EXP-018 EXP-019 --exp-id EXP-025 [--hedge]
"""
import argparse
import json

import numpy as np
import pandas as pd
from scipy.optimize import nnls

from prc import validate as V
from prc.models import hedge as H
from prc.paths import MODELS


def load(members):
    folds = {}
    for fold in V.HOLDOUTS:
        base = None
        for e in members:
            d = pd.read_parquet(MODELS / "oof" / f"{e}_{fold}.parquet")
            if base is None:
                base = d.drop(columns=["pred"]).copy()
            base[e] = d.set_index("mvt_id").loc[base.mvt_id, "pred"].to_numpy()
        folds[fold] = base
    return folds


def weights(df, members):
    w, _ = nnls(df[members].to_numpy(float), df.y.to_numpy(float))
    return w


def main(members, exp_id, use_hedge=False):
    folds = load(members)
    names = list(folds)
    res, used = {}, {}
    for i, fold in enumerate(names):
        other = names[1 - i]
        w = weights(folds[other], members)
        used[fold] = dict(zip(members, np.round(w, 4)))
        va = folds[fold].copy()
        va["pred"] = va[members].to_numpy(float) @ w
        res[fold] = va
    if use_hedge:
        f = H._frame()
        tr = f[f.ds == "train"]
        for fold, d in V.HOLDOUTS.items():
            va = res[fold].merge(f[["mvt_id", "d_sched", "nm_unmatched"]], on="mvt_id")
            va["pred"] = H.apply(va, va.pred.to_numpy(), H.fit(tr[tr.month != pd.Timestamp(d)]))
            res[fold] = va
    w_all = weights(pd.concat(folds.values()), members)
    meta = {"members": members, "cross_fit_weights": json.dumps({k: {m: float(x) for m, x in v.items()} for k, v in used.items()}),
            "final_weights": json.dumps(dict(zip(members, map(float, np.round(w_all, 4))))), "hedge": use_hedge,
            "data": V.data_version(), "git": V.git_sha()}
    single = {m: {f: round(V.rmse(folds[f].y, folds[f][m]), 2) for f in names} for m in members}
    text = V.report_md(exp_id, f"NNLS blend of {', '.join(members)}" + (" + echo hedge" if use_hedge else ""), res, meta)
    text += "\n## Members alone\n\n" + pd.DataFrame(single).T.to_markdown() + "\n"
    V.write_report(exp_id, text)
    for fold, va in res.items():
        va.to_parquet(MODELS / "oof" / f"{exp_id}_{fold}.parquet")
    r = {k: round(V.rmse(v.y, v.pred), 2) for k, v in res.items()}
    print(exp_id, r, "final weights", dict(zip(members, np.round(w_all, 4))))
    return r, w_all


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--members", nargs="+", required=True)
    ap.add_argument("--exp-id", required=True)
    ap.add_argument("--hedge", action="store_true")
    a = ap.parse_args()
    main(a.members, a.exp_id, a.hedge)
