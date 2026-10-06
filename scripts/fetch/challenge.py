"""Download the challenge files from the organizers' MinIO bucket and verify them against data/raw/MANIFEST.csv.

  uv run python scripts/fetch/challenge.py            # download missing / mismatching files, then verify all
  uv run python scripts/fetch/challenge.py --check    # list what would be downloaded, no network writes

Credentials (never committed): environment variables or a `.env` file in the repo root with
  ACCESS_KEY=...   SECRET_KEY=...      (team keys from the organizer acceptance e-mail; key names are case-insensitive,
                                        an optional MINIO_ / PRC_ prefix is accepted)
  S3_ENDPOINT=...                       (optional, default https://s3.opensky-network.org)
Source paths come from the committed manifest (`bucket_path` column, e.g. dc26:prc-2026-datasets/ranking.parquet;
the alias part is ignored). Every file is downloaded to a temporary name, checked for size and SHA256, then renamed;
a mismatch stops the run and nothing is overwritten (re-fetch policy, CLAUDE.md §5). Pre-reissue (stale) files are
refused (prc.manifest.STALE).

Uses the MinIO client `mc` (https://docs.min.io, "AIStor Client"; tested with RELEASE.2025-08-13). The alias is passed
as `MC_HOST_<alias>=https://ACCESS:SECRET@host` (documented "temporary alias ... for use with scripting"), so no config
file is written and no key appears on a command line; if a key contains characters that are not URL-safe, a throwaway
`--config-dir` with `mc alias set` is used instead and deleted afterwards.
"""
import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from prc.manifest import STALE, sha256, verify  # noqa: E402
from prc.paths import RAW_MANIFEST  # noqa: E402

DEFAULT_ENDPOINT = "https://s3.opensky-network.org"
ALIAS = "prcdl"
URL_SAFE = re.compile(r"^[A-Za-z0-9._~+-]+$")


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
    vals.update({k: v for k, v in os.environ.items()})
    return vals


def credential(vals: dict, name: str) -> str | None:
    """First value whose upper-cased key is NAME, MINIO_NAME or PRC_NAME (e.g. ACCESS_kEY → ACCESS_KEY)."""
    want = {name, f"MINIO_{name}", f"PRC_{name}"}
    for k, v in vals.items():
        if k.upper() in want and v:
            return v
    return None


def plan(manifest: Path = RAW_MANIFEST) -> list[dict]:
    """Manifest rows with the bucket object path (alias stripped) and whether the local file already matches."""
    with open(manifest) as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        bucket_path = r["bucket_path"].split(":", 1)[-1]           # "dc26:prc-2026-datasets/x" -> "prc-2026-datasets/x"
        local = ROOT / r["file"]
        ok = local.exists() and local.stat().st_size == int(r["bytes"]) and sha256(local) == r["sha256"]
        out.append({**r, "object": bucket_path, "local": local, "ok": ok})
    return out


def mc_env(access: str, secret: str, endpoint: str) -> tuple[dict, str | None]:
    """Environment for `mc` with a temporary alias; returns (env, config_dir_to_delete_or_None)."""
    u = urlparse(endpoint)
    env = {**os.environ, "NO_COLOR": "1"}
    env.pop("FORCE_COLOR", None)
    if URL_SAFE.match(access) and URL_SAFE.match(secret):
        env[f"MC_HOST_{ALIAS}"] = f"{u.scheme}://{access}:{secret}@{u.netloc}"
        return env, None
    cfg = tempfile.mkdtemp(prefix="mc-prc-")
    subprocess.run(["mc", "--config-dir", cfg, "alias", "set", ALIAS, endpoint, access, secret],
                   check=True, env=env, capture_output=True)
    return env, cfg


def download(row: dict, env: dict, cfg: str | None) -> None:
    local: Path = row["local"]
    local.parent.mkdir(parents=True, exist_ok=True)
    part = local.with_name(f".{local.name}.part")
    cmd = ["mc"] + (["--config-dir", cfg] if cfg else []) + ["cp", "--quiet", f"{ALIAS}/{row['object']}", str(part)]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        part.unlink(missing_ok=True)
        raise SystemExit(f"download failed for {row['object']}: {r.stderr.strip()[:300]}")
    h = sha256(part)
    if h.upper() in STALE:
        part.unlink()
        raise SystemExit(f"{row['object']} is a STALE pre-reissue copy ({STALE[h.upper()]}); stop and ask the organizers")
    if h != row["sha256"] or part.stat().st_size != int(row["bytes"]):
        part.unlink()
        raise SystemExit(f"{row['object']}: SHA256/size differ from the manifest — upstream changed; nothing overwritten")
    part.replace(local)
    print(f"downloaded {row['file']} ({local.stat().st_size} bytes, sha256 ok)")


def main(check_only: bool = False) -> int:
    rows = plan()
    todo = [r for r in rows if not r["ok"]]
    print(f"{len(rows)} files in the manifest, {len(rows) - len(todo)} present and verified, {len(todo)} to download")
    if check_only or not todo:
        return verify() if not todo else 0
    vals = read_env()
    access, secret = credential(vals, "ACCESS_KEY"), credential(vals, "SECRET_KEY")
    if not access or not secret:
        raise SystemExit("set ACCESS_KEY and SECRET_KEY in the environment or in .env (team MinIO keys)")
    endpoint = credential(vals, "S3_ENDPOINT") or DEFAULT_ENDPOINT
    if shutil.which("mc") is None:
        raise SystemExit("the MinIO client `mc` is required (https://docs.min.io, AIStor Client)")
    env, cfg = mc_env(access, secret, endpoint)
    try:
        for r in todo:
            download(r, env, cfg)
    finally:
        if cfg:
            shutil.rmtree(cfg, ignore_errors=True)
    return verify()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="only report which files are missing or differ")
    raise SystemExit(main(ap.parse_args().check))
