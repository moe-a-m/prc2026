"""M-028 ADS-B stand shrinkage: offsets, gate, clipped weights, rows without an estimate untouched."""
import numpy as np
import pandas as pd

from prc.models import adsb_stack as S


def _frame(n=600, seed=0):
    rng = np.random.default_rng(seed)
    y = rng.uniform(300, 1500, n)
    return pd.DataFrame({"airport": np.where(np.arange(n) % 2, "AAAA", "BBBB"), "y": y,
                         "pred": y + rng.normal(0, 150, n),
                         "est": y - np.where(np.arange(n) % 2, 20.0, 140.0) + rng.normal(0, 10, n)})


def test_fit_recovers_offsets_and_weights_in_unit_interval():
    m = S.fit(_frame())
    assert abs(m["offset"]["AAAA"] - 20) < 5 and abs(m["offset"]["BBBB"] - 140) < 5
    assert all(0 <= w <= 1 for w in m["w"].values())
    assert m["w"][1] > 0.8  # exact estimate after offset → weight near 1


def test_apply_gate_and_missing_estimate():
    m = {"offset": {"AAAA": 0.0}, "pooled_offset": 0.0, "w": {0: 1.0, 1: 0.5, 2: 0.5}}
    df = pd.DataFrame({"airport": ["AAAA"] * 4, "est": [500.0, 700.0, 2000.0, np.nan]})
    out = S.apply(df, np.array([450.0, 600.0, 600.0, 600.0]), m)
    assert out.tolist() == [500.0, 650.0, 600.0, 600.0]  # bin 0 full, bin 1 half, gap > gate and NaN unchanged


def test_unknown_airport_uses_pooled_offset():
    m = {"offset": {}, "pooled_offset": 30.0, "w": {0: 1.0, 1: 1.0, 2: 1.0}}
    df = pd.DataFrame({"airport": ["ZZZZ"], "est": [500.0]})
    assert S.apply(df, np.array([520.0]), m).tolist() == [530.0]
