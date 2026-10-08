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
