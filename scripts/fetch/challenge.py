"""Download the challenge files from the organizers' S3 (MinIO) bucket into data/raw/ and verify them.

  make download                                        # = uv run python scripts/fetch/challenge.py
  uv run python scripts/fetch/challenge.py --check     # list the bucket and what would be downloaded, no writes

Same approach as the PRC 2024 data page (pyopensky's S3Client = a `minio.Minio` client on s3.opensky-network.org:443,
`list_objects(bucket, recursive=True)`, one download per object) — i.e. the Python equivalent of
`mc cp --recursive <alias>/prc-2026-datasets data` — with credentials from `.env` instead of the pyopensky config file,
and every object sorted into the repo layout:
    training_*.parquet   -> data/raw/training/
    [final_]ranking*.parquet     -> data/raw/ranking/      (final_* = final-phase files, organizer e-mail 2026-10-08)
    [final_]submitting*.parquet  -> data/raw/submitting/
    anything else        -> data/raw/other/        (reported; not part of the pipeline)

Credentials (never committed): environment variables or `.env` in the repo root (see `.env.example`):
    ACCESS_KEY, SECRET_KEY         team keys from the organizer acceptance e-mail (names case-insensitive; MINIO_/PRC_
                                   prefix accepted)
    S3_ENDPOINT   optional         default s3.opensky-network.org:443
    DATASET_BUCKET optional        default prc-2026-datasets (not BUCKET_NAME: that is the team upload bucket)
Each object is downloaded to a temporary name and checked against data/raw/MANIFEST.csv (bytes + SHA256) before it is
moved into place. A mismatch, a stale pre-reissue file, or an object missing from the manifest stops with a report —
nothing verified is overwritten (re-fetch policy, CLAUDE.md §5). Files already present and verified are skipped.
"""
import argparse
import csv
import os
import sys
from pathlib import Path

from minio import Minio

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from prc.manifest import STALE, sha256, verify  # noqa: E402
from prc.paths import RAW, RAW_MANIFEST  # noqa: E402

DEFAULT_ENDPOINT = "s3.opensky-network.org:443"
DEFAULT_BUCKET = "prc-2026-datasets"


def read_env(path: Path = ROOT / ".env") -> dict:
    """KEY=VALUE lines (comments, blank lines, `export ` prefix and surrounding quotes allowed); real environment wins."""
    vals = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.removeprefix("export ").split("=", 1)
            vals[k.strip()] = v.strip().strip('"').strip("'")
    vals.update(os.environ)
    return vals


def setting(vals: dict, name: str) -> str | None:
    """First non-empty value whose upper-cased key is NAME, MINIO_NAME or PRC_NAME."""
    want = {name, f"MINIO_{name}", f"PRC_{name}"}
    for k, v in vals.items():
        if k.upper() in want and v:
            return v
    return None


def target_for(object_name: str) -> Path:
    """Repo location for a bucket object (layout of data/raw/, see the module docstring)."""
    name = Path(object_name).name
    kind = name.removeprefix("final_")
    if name.startswith("training_") and name.endswith(".parquet"):
        return RAW / "training" / name
    if kind.startswith("ranking") and name.endswith(".parquet"):
        return RAW / "ranking" / name
    if kind.startswith("submitting") and name.endswith(".parquet"):
        return RAW / "submitting" / name
    return RAW / "other" / object_name


def manifest_rows(manifest: Path = RAW_MANIFEST) -> dict:
    with open(manifest) as f:
        return {r["file"]: r for r in csv.DictReader(f)}


def is_verified(local: Path, row: dict | None) -> bool:
    return (row is not None and local.exists() and local.stat().st_size == int(row["bytes"])
            and sha256(local) == row["sha256"])


def client(vals: dict) -> Minio:
    access, secret = setting(vals, "ACCESS_KEY"), setting(vals, "SECRET_KEY")
    if not access or not secret:
        raise SystemExit("set ACCESS_KEY and SECRET_KEY in the environment or in .env (team keys; see .env.example)")
    endpoint = setting(vals, "S3_ENDPOINT") or DEFAULT_ENDPOINT
    endpoint = endpoint.removeprefix("https://").removeprefix("http://")
    return Minio(endpoint, access_key=access, secret_key=secret, secure=True)


def fetch(s3: Minio, bucket: str, obj, local: Path, row: dict | None) -> str:
    """Download one object to a temporary name, check it, move it into place. Returns a status word."""
    local.parent.mkdir(parents=True, exist_ok=True)
    part = local.with_name(f".{local.name}.part")
    s3.fget_object(bucket, obj.object_name, str(part))
    h = sha256(part)
    if h.upper() in STALE:
        part.unlink()
        raise SystemExit(f"{obj.object_name} is a STALE pre-reissue copy ({STALE[h.upper()]}); stop and ask the organizers")
    if row is None:
        part.replace(local)
        return "NEW (not in the manifest — review, then `python -m prc.manifest build`)"
    if h != row["sha256"] or part.stat().st_size != int(row["bytes"]):
        part.unlink()
        raise SystemExit(f"{obj.object_name}: SHA256/size differ from the manifest — upstream changed; nothing overwritten")
    part.replace(local)
    return "downloaded, sha256 ok"


def main(check_only: bool = False) -> int:
    vals = read_env()
    s3 = client(vals)
    bucket = setting(vals, "DATASET_BUCKET") or DEFAULT_BUCKET
    rows = manifest_rows()
    objects = list(s3.list_objects(bucket, recursive=True))
    print(f"{bucket}: {len(objects)} objects; manifest: {len(rows)} files")
    seen, new = set(), 0
    for obj in objects:
        local = target_for(obj.object_name)
        rel = str(local.relative_to(ROOT))
        row = rows.get(rel)
        seen.add(rel)
        if is_verified(local, row):
            print(f"  ok        {rel}")
            continue
        if check_only:
            print(f"  MISSING   {rel}  <- {bucket}/{obj.object_name} ({obj.size} bytes)")
            continue
        status = fetch(s3, bucket, obj, local, row)
        new += status.startswith("NEW")
        print(f"  {status:9s} {rel}")
    absent = sorted(set(rows) - seen)
    for rel in absent:
        print(f"  NOT IN BUCKET {rel} (listed in the manifest)")
    if check_only:
        return 0
    rc = verify()
    return 1 if (rc or new or absent) else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="list the bucket and what would be downloaded, no writes")
    raise SystemExit(main(ap.parse_args().check))
