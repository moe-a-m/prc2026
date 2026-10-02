"""Shared helpers for scripts/fetch/*: external manifest, hashing, resumable parallel range downloads.

Raw bytes are written unmodified; every file gets a row (path, bytes, sha256, retrieved_at, source_id) in
data/external/MANIFEST.csv (CLAUDE.md §5). A listed file whose bytes no longer match stops the caller.
"""
import csv
import hashlib
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from prc.paths import ROOT

MANIFEST = ROOT / "data" / "external" / "MANIFEST.csv"
FIELDS = ["path", "bytes", "sha256", "retrieved_at", "source_id"]
UA = {"User-Agent": "prc-2026-taxi-out research (github: moe-a-m)"}
_lock = threading.Lock()


def sha256_file(path, chunk=1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def manifest_rows() -> list[dict]:
    if not MANIFEST.exists():
        return []
    with open(MANIFEST) as f:
        return list(csv.DictReader(f))


def record(path: Path, source_id: str, sha: str | None = None, size: int | None = None) -> dict:
    """Add/replace the manifest row for `path` (relative to repo root)."""
    rel = str(Path(path).resolve().relative_to(ROOT))
    rec = {"path": rel, "bytes": size if size is not None else Path(path).stat().st_size,
           "sha256": sha or sha256_file(path), "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "source_id": source_id}
    with _lock:
        rows = [r for r in manifest_rows() if r["path"] != rel] + [rec]
        with open(MANIFEST, "w", newline="") as f:
            w = csv.DictWriter(f, FIELDS)
            w.writeheader()
            w.writerows(sorted(rows, key=lambda r: r["path"]))
    return rec


def listed(path: Path) -> dict | None:
    rel = str(Path(path).resolve().relative_to(ROOT))
    return next((r for r in manifest_rows() if r["path"] == rel), None)


def download(url: str, dest: Path, n_conn: int = 4, expected_size: int | None = None, retries: int = 5,
             log=print) -> int:
    """Download url to dest with n_conn parallel HTTP range requests (resumable per chunk). Returns bytes."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if expected_size is None:
        r = requests.head(url, allow_redirects=True, headers=UA, timeout=60)
        r.raise_for_status()
        expected_size = int(r.headers["Content-Length"])
    part = dest.with_suffix(dest.suffix + ".part")
    if not part.exists() or part.stat().st_size != expected_size:
        with open(part, "wb") as f:
            f.truncate(expected_size)
    chunk = 64 << 20
    done_file = part.with_suffix(".done")
    done = set(int(x) for x in done_file.read_text().split()) if done_file.exists() else set()
    todo = [s for s in range(0, expected_size, chunk) if s not in done]
    errors = []

    def worker():
        while True:
            with _lock:
                if not todo:
                    return
                start = todo.pop(0)
            end = min(start + chunk, expected_size) - 1
            for attempt in range(retries):
                try:
                    # original URL each time: GitHub redirects to short-lived signed URLs
                    r = requests.get(url, headers={**UA, "Range": f"bytes={start}-{end}"}, timeout=180)
                    if r.status_code != 206:
                        raise IOError(f"HTTP {r.status_code}")
                    buf = r.content
                    if len(buf) != end - start + 1:
                        raise IOError(f"short read {len(buf)}")
                    with open(part, "r+b") as f:
                        f.seek(start)
                        f.write(buf)
                    with _lock:
                        with open(done_file, "a") as d:
                            d.write(f"{start}\n")
                    break
                except Exception as e:  # noqa: BLE001 — retry any transport error
                    log(f"  retry {attempt + 1} chunk {start}: {e}")
                    time.sleep(10 * (attempt + 1))
            else:
                errors.append(start)

    threads = [threading.Thread(target=worker) for _ in range(n_conn)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    if errors:
        raise IOError(f"{len(errors)} chunks failed for {url}")
    part.rename(dest)
    done_file.unlink(missing_ok=True)
    return expected_size
