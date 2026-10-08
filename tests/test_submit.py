"""Submission builder/checker on a synthetic prediction (no upload)."""
import pandas as pd
import pytest

from prc import paths, submit


@pytest.fixture
def tmp_subdir(tmp_path, monkeypatch):
    if not paths.RAW_SUBMITTING.exists():
        pytest.skip("submitting.parquet not present")
    monkeypatch.setattr(submit, "SUBMISSIONS", tmp_path)
    return tmp_path


def test_build_and_check(tmp_subdir, tmp_path):
    tpl = pd.read_parquet(paths.RAW_SUBMITTING)
    pred = pd.DataFrame({"mvt_id": tpl.MVT_ID_mvt.astype("int64"), "pred": 900.4})
    pred.loc[0, "pred"] = -5  # must be clipped to 0
    pp = tmp_path / "pred.parquet"
    pred.to_parquet(pp)
    path, problems = submit.build(pp, version=999)
    assert problems == []
    out = pd.read_parquet(path)
    assert len(out) == 670_790 and out.TAXITIME_SEC_mvt.min() == 0 and out.TAXITIME_SEC_mvt.max() == 900


def test_check_detects_missing_rows(tmp_subdir, tmp_path):
    tpl = pd.read_parquet(paths.RAW_SUBMITTING).iloc[:-1].assign(TAXITIME_SEC_mvt=1)
    p = tmp_path / "motivated-engine_v998.parquet"
    tpl.to_parquet(p)
    assert any("rows" in x for x in submit.check(p))


def test_final_name(tmp_subdir, tmp_path):
    tpl = pd.read_parquet(paths.RAW_SUBMITTING)
    pp = tmp_path / "pred.parquet"
    pd.DataFrame({"mvt_id": tpl.MVT_ID_mvt.astype("int64"), "pred": 600.0}).to_parquet(pp)
    path, problems = submit.build(pp, version="final")
    assert path.name == "motivated-engine_final.parquet" and problems == []
