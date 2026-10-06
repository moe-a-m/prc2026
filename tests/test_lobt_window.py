"""M-031 LOBT feasible-interval projection: clip to d_lobt ± WINDOW_S, floor 0, rows without LOBT untouched, never
farther from a target inside the interval."""
import numpy as np

from prc.models import lobt_window as L


def test_clip_floor_and_missing_lobt():
    W = L.WINDOW_S
    pred = np.array([100.0, 9000.0, 500.0, -50.0, 7000.0])
    d = np.array([5000.0, 1000.0, 600.0, np.nan, np.nan])
    out = L.project(pred, d)
    assert out.tolist() == [5000.0 - W, 1000.0 + W, 500.0, 0.0, 7000.0]


def test_projection_never_increases_error_for_feasible_targets():
    rng = np.random.default_rng(0)
    d = rng.uniform(0, 20000, 5000)
    y = np.maximum(d + rng.uniform(-L.WINDOW_S, L.WINDOW_S, 5000), 0)   # targets inside the feasible interval
    pred = rng.uniform(-5000, 40000, 5000)
    assert np.all(np.abs(L.project(pred, d) - y) <= np.abs(pred - y) + 1e-9)
