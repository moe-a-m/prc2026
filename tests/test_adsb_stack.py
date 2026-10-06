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


def test_sources_have_separate_models_and_unmatched_rows_untouched():
    models = {"still": {"offset": {"AAAA": 0.0}, "pooled_offset": 0.0, "w": {0: 1.0, 1: 1.0, 2: 1.0}},
              "moving": {"offset": {"AAAA": 100.0}, "pooled_offset": 0.0, "w": {0: 0.5, 1: 0.5, 2: 0.5}}}
    df = pd.DataFrame({"airport": ["AAAA"] * 3, "est": [500.0, 400.0, np.nan], "src": ["still", "moving", np.nan]})
    out = S.apply_sources(df, np.array([450.0, 450.0, 450.0]), models)
    assert out.tolist() == [500.0, 475.0, 450.0]  # still: full step; moving: offset +100 then half step; no source: same


def test_fit_sources_one_model_per_source():
    a, b = _frame(seed=1).assign(src="still"), _frame(seed=2).assign(src="moving")
    m = S.fit_sources(pd.concat([a, b]))
    assert set(m) == {"still", "moving"}


def test_final_model_round_trips_through_report(tmp_path, monkeypatch):
    import json
    from prc import paths
    m = S.fit_sources(pd.concat([_frame(seed=1).assign(src="still"), _frame(seed=2).assign(src="moving")]))
    (tmp_path / "experiments").mkdir()
    (tmp_path / "experiments" / "EXP-999.md").write_text(f"# x\n\n- final_model: {json.dumps(m)}\n")
    monkeypatch.setattr(paths, "REPORTS", tmp_path)
    back = S.load_final_model("EXP-999")
    df = pd.DataFrame({"airport": ["AAAA", "BBBB"], "est": [500.0, 520.0], "src": ["still", "moving"]})
    pred = np.array([450.0, 470.0])
    assert np.array_equal(S.apply_sources(df, pred, back), S.apply_sources(df, pred, m))
