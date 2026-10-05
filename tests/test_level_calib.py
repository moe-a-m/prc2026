"""M-029 EC level calibration: gap model with a snow slope, deltas only on rows with pred ≤ cap."""
import numpy as np
import pandas as pd

from prc.models import level_calib as L


def test_fit_gap_recovers_snow_slope_and_intercept_only():
    m = pd.DataFrame({"airport": ["A"] * 4 + ["B"] * 4, "month": list(range(4)) * 2,
                      "ec": [800.0] * 8, "snow": [0, 0.1, 0.2, 0.0, 0, 0, 0, 0],
                      "ybar": [810, 910, 1010, 810, 795, 805, 800, 800]})
    g = L.fit_gap(m)
    assert abs(g["A"][0] - 10) < 1e-6 and abs(g["A"][1] - 1000) < 1e-6
    assert g["B"] == (0.0, 0.0)


def test_deltas_shift_to_level_and_skip_long_rows():
    rows = pd.DataFrame({"airport": ["A", "A", "A"], "month": [1, 1, 1], "pred": [700.0, 900.0, 9000.0]})
    tgt = pd.DataFrame({"airport": ["A"], "month": [1], "ec": [850.0], "snow": [0.0], "ybar": [np.nan]})
    d = L.deltas(rows, tgt, {"A": (10.0, 0.0)})
    assert d.tolist() == [60.0, 60.0, 0.0]  # level 860 − mean(700, 900); the 9000 s row is untouched
