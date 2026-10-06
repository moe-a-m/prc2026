"""Challenge-data download helper: .env parsing, key-name matching, manifest → bucket object mapping (no network)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "fetch"))
import challenge as C  # noqa: E402


def test_read_env_parses_and_environment_wins(tmp_path, monkeypatch):
    p = tmp_path / ".env"
    p.write_text("# team keys\nACCESS_kEY=abc123\nexport SECRET_KEY='s3cr3t-value'\n\nS3_ENDPOINT=\"https://example.org\"\n")
    monkeypatch.setenv("S3_ENDPOINT", "https://override.org")
    v = C.read_env(p)
    assert v["ACCESS_kEY"] == "abc123" and v["SECRET_KEY"] == "s3cr3t-value"
    assert v["S3_ENDPOINT"] == "https://override.org"


def test_credential_names_are_case_insensitive_with_prefixes():
    assert C.credential({"ACCESS_kEY": "a"}, "ACCESS_KEY") == "a"
    assert C.credential({"MINIO_SECRET_KEY": "b"}, "SECRET_KEY") == "b"
    assert C.credential({"OTHER": "x"}, "ACCESS_KEY") is None


def test_plan_maps_bucket_paths_and_marks_present_files():
    rows = C.plan()
    assert len(rows) == 14
    r = next(r for r in rows if r["file"].endswith("ranking.parquet"))
    assert r["object"] == "prc-2026-datasets/ranking.parquet"


def test_mc_env_uses_temporary_alias_for_url_safe_keys():
    env, cfg = C.mc_env("ACCESS123", "secret+key-1", "https://s3.example.org")
    assert cfg is None and env["MC_HOST_prcdl"] == "https://ACCESS123:secret+key-1@s3.example.org"
