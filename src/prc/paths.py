"""Repository paths. Everything is relative to the repo root so a fresh clone works."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
RAW_TRAINING = RAW / "training"
RAW_RANKING = RAW / "ranking" / "ranking.parquet"
RAW_SUBMITTING = RAW / "submitting" / "submitting.parquet"
RAW_MANIFEST = RAW / "MANIFEST.csv"
DB = DATA / "prc.duckdb"
SQL = ROOT / "sql"
REPORTS = ROOT / "reports"
CHECKS = REPORTS / "checks"
MODELS = ROOT / "models"
SUBMISSIONS = ROOT / "submissions"
CONFIGS = ROOT / "configs"
