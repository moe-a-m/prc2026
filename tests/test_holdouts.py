"""Hold-out month selection (PRC_HOLDOUTS) and the cross-fit helper used by blend / ADS-B step."""
from datetime import date

import pandas as pd
import pytest

from prc import validate as V


def test_default_is_jan_jul(monkeypatch):
    monkeypatch.delenv("PRC_HOLDOUTS", raising=False)
    assert V.holdouts() == {"jan": date(2025, 1, 1), "jul": date(2025, 7, 1)}


def test_all_and_list():
    h = V.holdouts("all")
    assert list(h) == V.MONTHS and h["dec"] == date(2025, 12, 1)
    assert V.holdouts("feb, jun") == {"feb": date(2025, 2, 1), "jun": date(2025, 6, 1)}
    with pytest.raises(ValueError):
        V.holdouts("jan,foo")


def test_others_two_folds_is_the_other_frame():
    a, b = pd.DataFrame({"x": [1]}), pd.DataFrame({"x": [2]})
    assert V.others({"jan": a, "jul": b}, "jan") is b   # unchanged M-019 rule: exactly the other month


def test_others_many_folds_excludes_own_month():
    frames = {m: pd.DataFrame({"m": [m] * 2}) for m in ["jan", "feb", "mar"]}
    o = V.others(frames, "feb")
    assert sorted(o.m.unique()) == ["jan", "mar"] and len(o) == 4


def test_validate_saves_each_fold_and_resumes(tmp_path, monkeypatch):
    """gbm.validate writes <exp>_<fold>.parquet + .json per fold; PRC_RESUME=1 reuses only matching folds."""
    import json
    import numpy as np
    from prc.models import gbm
    n = 400
    rng = np.random.default_rng(0)
    months = pd.to_datetime(np.where(np.arange(n) % 2 == 0, "2025-01-01", "2025-07-01"))
    df = pd.DataFrame({"mvt_id": np.arange(n), "ds": "train", "month": months, "airport": "EDDF", "y": rng.normal(600, 50, n),
                       "x": rng.normal(size=n)})
    monkeypatch.setattr(gbm, "MODELS", tmp_path)
    monkeypatch.setattr(gbm, "load_frame", lambda *a: df)
    monkeypatch.setattr(gbm, "EVAL_COLS", ["mvt_id", "airport", "month", "y"])
    monkeypatch.setattr(gbm, "design", lambda d, cfg, m: d[["x"]])
    monkeypatch.setattr(V, "data_version", lambda: "d1")
    monkeypatch.setattr(V, "write_report", lambda *a: None)
    calls = []
    cfg = {"exp_id": "EXP-T", "title": "t", "config_hash": "c1", "seed": 1, "params": {}, "num_boost_round": 1}
    monkeypatch.setattr(V, "HOLDOUTS", {"jan": pd.Timestamp("2025-01-01").date(), "jul": pd.Timestamp("2025-07-01").date()})
    class B:  # stands in for a fitted model
        def feature_importance(self, kind):
            return np.array([1.0])
    monkeypatch.setattr(gbm, "fit_predict", lambda d, X, fm, pm, cfg, s: (calls.append(1) or np.full(pm.sum(), 600.0), B()))
    gbm.validate(cfg, seeds=[1])
    assert len(calls) == 2 and (tmp_path / "oof" / "EXP-T_jan.parquet").exists()
    assert json.loads((tmp_path / "oof" / "EXP-T_jul.json").read_text())["seeds"] == [1]
    monkeypatch.setenv("PRC_RESUME", "1")
    gbm.validate(cfg, seeds=[1])
    assert len(calls) == 2                       # both folds resumed, nothing refit
    gbm.validate({**cfg, "config_hash": "c2"}, seeds=[1])
    assert len(calls) == 4                       # config changed: refit
