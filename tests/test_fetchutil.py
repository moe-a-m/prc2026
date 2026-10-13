"""External-data manifest (src/prc/fetchutil.py): a re-downloaded file whose bytes differ from the committed manifest
row stops the fetch instead of silently replacing the row (fresh clone after an upstream change). No network."""
import pytest

from prc import fetchutil as F


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "ROOT", tmp_path)
    monkeypatch.setattr(F, "MANIFEST", tmp_path / "MANIFEST.csv")
    monkeypatch.delenv(F.ACCEPT_ENV, raising=False)
    return tmp_path


def test_new_file_is_recorded(repo):
    p = repo / "a.csv"
    p.write_bytes(b"one")
    F.record(p, "src")
    assert F.listed(p)["sha256"] == F.sha256_file(p)


def test_same_bytes_rerecorded(repo):
    p = repo / "a.csv"
    p.write_bytes(b"one")
    F.record(p, "src")
    F.record(p, "src")
    assert len(F.manifest_rows()) == 1


def test_changed_upstream_stops_and_keeps_manifest(repo):
    p = repo / "a.csv"
    p.write_bytes(b"one")
    want = F.record(p, "src")["sha256"]
    p.write_bytes(b"two")  # the same path re-downloaded with other bytes
    with pytest.raises(SystemExit, match="upstream file changed"):
        F.record(p, "src")
    assert not p.exists() and F.listed(p)["sha256"] == want


def test_changed_upstream_accepted_by_env_or_flag(repo, monkeypatch):
    p = repo / "a.csv"
    p.write_bytes(b"one")
    F.record(p, "src")
    p.write_bytes(b"two")
    F.record(p, "src", allow_change=True)
    assert F.listed(p)["sha256"] == F.sha256_file(p)
    p.write_bytes(b"three")
    monkeypatch.setenv(F.ACCEPT_ENV, "1")
    F.record(p, "src")
    assert F.listed(p)["sha256"] == F.sha256_file(p)
