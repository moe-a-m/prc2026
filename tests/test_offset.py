"""Baseline offset (M-022): trees learn y − offset and predictions add it back."""
import numpy as np
import pandas as pd

from prc.models import gbm

CFG = {"params": {"objective": "regression", "verbose": -1, "num_threads": 1, "min_data_in_leaf": 20,
                  "deterministic": True, "force_row_wise": True}, "categorical": [], "num_boost_round": 30}


def _df(n=3000, seed=0):
    rng = np.random.default_rng(seed)
    proxy = rng.uniform(300, 30000, n)
    df = pd.DataFrame({"airport": rng.choice(["A", "B"], n), "d_aobt3": proxy, "d_eobt1": np.nan, "d_sched": proxy})
    df["y"] = proxy + rng.normal(0, 30, n)          # target = proxy + noise: needs extrapolation along the proxy
    return df, pd.DataFrame({"x": rng.normal(size=n)})


def test_offset_extrapolates_and_is_added_back():
    df, X = _df()
    fm = (df.d_aobt3 < 20000).to_numpy()            # train on small proxies, predict large ones
    p_off, _ = gbm.fit_predict(df, X, fm, ~fm, {**CFG, "offset": "nm_proxy", "per_airport": True}, 1)
    p_raw, _ = gbm.fit_predict(df, X, fm, ~fm, {**CFG, "per_airport": True}, 1)
    err = lambda p: np.sqrt(np.mean((p - df.y[~fm]) ** 2))
    assert err(p_off) < 100 < err(p_raw)


def test_no_offset_is_zero():
    df, _ = _df(50)
    assert not gbm.offset(df, {}).any()
    assert np.allclose(gbm.offset(df, {"offset": "nm_proxy"}), df.d_aobt3)
