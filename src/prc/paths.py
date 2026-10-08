"""Repository paths. Everything is relative to the repo root so a fresh clone works."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
RAW_TRAINING = RAW / "training"
# final phase (organizer e-mail 2026-10-08): Jan, Feb, Jun, Jul 2026; supersets of the public-phase ranking/submitting files
RAW_RANKING = RAW / "ranking" / "final_ranking.parquet"
RAW_SUBMITTING = RAW / "submitting" / "final_submitting.parquet"
RAW_MANIFEST = RAW / "MANIFEST.csv"
DB = DATA / "prc.duckdb"
SQL = ROOT / "sql"
REPORTS = ROOT / "reports"
CHECKS = REPORTS / "checks"
MODELS = ROOT / "models"
SUBMISSIONS = ROOT / "submissions"
CONFIGS = ROOT / "configs"
