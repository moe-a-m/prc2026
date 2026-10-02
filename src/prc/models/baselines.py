"""P2 baselines (provenance: simple statistics, CLAUDE.md §10 P2). Writes EXP-001..EXP-00N reports.

Each baseline is fit on the 11 training months and evaluated on the held-out month (Jan / Jul 2025).
Group statistics fall back to coarser groups when a key is unseen in training.
"""
import numpy as np
import pandas as pd

from prc import db, validate as V

SQL = """
SELECT mvt_id, month, airport, runway, stand, y,
       epoch(t_mvt) - epoch(t_aobt3) AS x_aobt3,
       f_no_nm_match, f_block_eq_sched, f_block_eq_planned, f_round_minute_block, f_negative_taxi, f_taxi_gt_3h
FROM clean_dep WHERE ds = 'train'
"""


def group_stat(tr, va, keys, stat):
    g = tr.groupby(keys, dropna=False).y.agg(stat).rename("s").reset_index()
    return va[keys].merge(g, on=keys, how="left")["s"].to_numpy()


def hierarchical(tr, va, levels, stat):
    """Predict with the finest level available, falling back through `levels` then the global stat."""
    p = np.full(len(va), tr.y.agg(stat), float)
    for keys in levels:  # coarse → fine; finer overwrites where available
        s = group_stat(tr, va, keys, stat)
        p = np.where(np.isnan(s), p, s)
    return p


def main():
    con = db.connect(read_only=True)
    df = con.sql(SQL).df()
    con.close()
    meta_base = {"data": V.data_version(), "git": V.git_sha(), "rows": len(df)}
    specs = []
    for stat in ["median", "mean"]:
        specs += [
            (f"global {stat}", lambda tr, va, s=stat: np.full(len(va), tr.y.agg(s))),
            (f"airport {stat}", lambda tr, va, s=stat: hierarchical(tr, va, [["airport"]], s)),
            (f"airport×runway {stat}", lambda tr, va, s=stat: hierarchical(tr, va, [["airport"], ["airport", "runway"]], s)),
            (f"airport×stand×runway {stat} (fallback airport×runway, airport)",
             lambda tr, va, s=stat: hierarchical(tr, va, [["airport"], ["airport", "runway"], ["airport", "stand", "runway"]], s)),
        ]

    def aobt3(tr, va, corrected):
        fb = hierarchical(tr, va, [["airport"], ["airport", "runway"], ["airport", "stand", "runway"]], "mean")
        x = va.x_aobt3.to_numpy(float)
        if corrected:  # + mean residual (y − x) per airport×runway from training
            trr = tr.assign(r=tr.y - tr.x_aobt3).dropna(subset=["r"])
            off = hierarchical(trr.assign(y=trr.r), va, [["airport"], ["airport", "runway"]], "mean")
            x = x + off
        return np.where(np.isnan(x), fb, x)

    specs += [("MVT − AOBT_3 (fallback stand×runway mean)", lambda tr, va: aobt3(tr, va, False)),
              ("MVT − AOBT_3 + airport×runway mean residual (fallback stand×runway mean)", lambda tr, va: aobt3(tr, va, True))]

    summary = []
    for i, (name, fn) in enumerate(specs, start=1):
        exp_id = f"EXP-{i:03d}"
        res = {}
        for fold, trm, vam in V.folds(df.month):
            tr, va = df[trm], df[vam].copy()
            va["pred"] = fn(tr, va)
            res[fold] = va
        text = V.report_md(exp_id, f"Baseline — {name}", res, meta_base)
        V.write_report(exp_id, text)
        r = {k: V.rmse(v.y, v.pred) for k, v in res.items()}
        r["combined"] = V.rmse(pd.concat(res.values()).y, pd.concat(res.values()).pred)
        summary.append((exp_id, name, r))
        print(f"{exp_id} {name:75s} jan={r['jan']:.1f} jul={r['jul']:.1f} comb={r['combined']:.1f}", flush=True)
    return summary


if __name__ == "__main__":
    main()
