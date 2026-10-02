"""Out-of-fold target encoding semantics (M-005, M-016)."""
import numpy as np
import pandas as pd

from prc.models.gbm import target_encode


def _frame():
    rng = np.random.default_rng(1)
    n = 600
    return pd.DataFrame({"k": rng.choice(["a", "b", "c"], n),
                         "month": pd.to_datetime(rng.choice(["2025-01-01", "2025-02-01", "2025-03-01"], n)),
                         "y": rng.normal(900, 200, n)})


def test_leave_one_month_out_and_holdout():
    df = _frame()
    fit = (df.month != "2025-03-01").to_numpy()
    for q in (None, 0.1):
        te = target_encode(df, fit, [["k"]], df.month, q=q)
        col = "te_k" if q is None else "te_q10_k"
        stat = (lambda s: s.median()) if q is None else (lambda s: s.quantile(0.1))
        i = np.flatnonzero(fit & (df.month == "2025-01-01").to_numpy())[0]          # fit row: other fit month only
        other = df[fit & (df.month != df.month[i]).to_numpy() & (df.k == df.k[i]).to_numpy()]
        assert np.isclose(te[col].iloc[i], stat(other.y))
        j = np.flatnonzero(~fit)[0]                                                  # held-out row: all fit rows
        assert np.isclose(te[col].iloc[j], stat(df[fit & (df.k == df.k[j]).to_numpy()].y))
    assert "te_k_n" in target_encode(df, fit, [["k"]], df.month).columns
