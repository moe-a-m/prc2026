"""Blend hold-out predictions of several experiments (M-019): non-negative least squares without intercept.

Cross-fitted to avoid tuning on the scored validation month: weights fit on the other hold-out months are evaluated on
each month (Jan-2025 ↔ Jul-2025 by default; PRC_HOLDOUTS=all: leave-one-month-out over 2025). Final weights (for the
ranking set) are fit on all hold-out folds together.

  python -m prc.models.blend --members EXP-018 EXP-019 --exp-id EXP-025 [--hedge]
  python -m prc.models.blend --average EXP-025:1 EXP-029:2 --exp-id EXP-030      # ranking preds, weighted mean
  python -m prc.models.blend --final --exp-id EXP-031                            # ranking preds, weights from report
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
    for fold in names:
        w = weights(V.others(folds, fold), members)
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


def _rank_preds(e):
    return pd.read_parquet(MODELS / e / "pred_rank.parquet").set_index("mvt_id").pred


def average(spec, exp_id):
    """Weighted mean of members' predictions, e.g. seed averages ('EXP-025:1 EXP-029:2'). Writes the ranking
    predictions and/or the hold-out predictions, whichever the members have."""
    parts = [(e, float(w)) for e, w in (x.split(":") for x in spec)]
    wsum = sum(w for _, w in parts)
    if all((MODELS / e / "pred_rank.parquet").exists() for e, _ in parts):
        preds = [_rank_preds(e) * w for e, w in parts]
        out = sum(preds[1:], preds[0]) / wsum
        (MODELS / exp_id).mkdir(parents=True, exist_ok=True)
        out.rename("pred").reset_index().to_parquet(MODELS / exp_id / "pred_rank.parquet", index=False)
        print(f"wrote {MODELS / exp_id / 'pred_rank.parquet'} ({len(out)} rows) from {parts}")
    for fold in V.HOLDOUTS:
        files = [MODELS / "oof" / f"{e}_{fold}.parquet" for e, _ in parts]
        if not all(f.exists() for f in files):
            continue
        base = pd.read_parquet(files[0])
        base["pred"] = sum(pd.read_parquet(f).set_index("mvt_id").loc[base.mvt_id, "pred"].to_numpy() * w
                           for f, (_, w) in zip(files, parts)) / wsum
        base.to_parquet(MODELS / "oof" / f"{exp_id}_{fold}.parquet")
        print(f"wrote hold-out average {exp_id}_{fold} ({len(base)} rows)")


def final(exp_id):
    """Apply the blend's final weights (recorded in reports/experiments/<exp_id>.md) to members' ranking predictions."""
    import re
    from prc.paths import REPORTS
    rep = (REPORTS / "experiments" / f"{exp_id}.md").read_text()
    w = json.loads(re.search(r"- final_weights: (\{.*\})", rep).group(1))
    if re.search(r"- hedge: True", rep):
        raise SystemExit("blend was evaluated with the hedge; apply prc.models.hedge final as well")
    preds = {e: _rank_preds(e) for e in w}
    idx = next(iter(preds.values())).index
    out = sum(preds[e].loc[idx] * wt for e, wt in w.items())
    (MODELS / exp_id).mkdir(parents=True, exist_ok=True)
    out.rename("pred").reset_index().to_parquet(MODELS / exp_id / "pred_rank.parquet", index=False)
    print(f"wrote {MODELS / exp_id / 'pred_rank.parquet'} ({len(out)} rows), weights {w}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--members", nargs="+")
    ap.add_argument("--average", nargs="+")
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--exp-id", required=True)
    ap.add_argument("--hedge", action="store_true")
    a = ap.parse_args()
    if a.average:
        average(a.average, a.exp_id)
    elif a.final:
        final(a.exp_id)
    else:
        main(a.members, a.exp_id, a.hedge)
