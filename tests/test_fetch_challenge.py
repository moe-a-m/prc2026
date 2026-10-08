"""Challenge-data download (scripts/fetch/challenge.py): .env parsing, key names, bucket → repo layout (no network)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "fetch"))
import challenge as C  # noqa: E402
from prc.paths import RAW  # noqa: E402


def test_read_env_parses_and_environment_wins(tmp_path, monkeypatch):
    p = tmp_path / ".env"
    p.write_text("# team keys\nACCESS_KEY=abc123\nexport SECRET_KEY='s3cr3t-value'\n\nS3_ENDPOINT=\"example.org:443\"\n")
    monkeypatch.setenv("S3_ENDPOINT", "override.org:443")
    v = C.read_env(p)
    assert v["ACCESS_KEY"] == "abc123" and v["SECRET_KEY"] == "s3cr3t-value"
    assert v["S3_ENDPOINT"] == "override.org:443"


def test_setting_names_are_case_insensitive_with_prefixes():
    assert C.setting({"ACCESS_kEY": "a"}, "ACCESS_KEY") == "a"
    assert C.setting({"MINIO_SECRET_KEY": "b"}, "SECRET_KEY") == "b"
    assert C.setting({"OTHER": "x"}, "ACCESS_KEY") is None


def test_bucket_objects_map_to_the_repo_layout():
    assert C.target_for("training_2025-01-01_2025-02-01.parquet") == RAW / "training" / "training_2025-01-01_2025-02-01.parquet"
    assert C.target_for("ranking.parquet") == RAW / "ranking" / "ranking.parquet"
    assert C.target_for("submitting.parquet") == RAW / "submitting" / "submitting.parquet"
    assert C.target_for("final_ranking.parquet") == RAW / "ranking" / "final_ranking.parquet"
    assert C.target_for("final_submitting.parquet") == RAW / "submitting" / "final_submitting.parquet"
    assert C.target_for("README.txt") == RAW / "other" / "README.txt"


def test_every_manifest_file_has_a_bucket_name_that_maps_back_to_it():
    rows = C.manifest_rows()
    assert len(rows) == 14
    for rel, r in rows.items():
        obj = r["bucket_path"].split("/", 1)[-1]          # dc26:prc-2026-datasets/<object>
        assert str(C.target_for(obj).relative_to(C.ROOT)) == rel
