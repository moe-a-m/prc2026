"""Build and verify data/raw/MANIFEST.csv (CLAUDE.md §8.0).

`python -m prc.manifest build`  — (re)write the manifest from the files on disk.
`python -m prc.manifest verify` — recompute hashes; exit 1 on any mismatch or stale file.
"""
import csv
import hashlib
import sys
from datetime import datetime, timezone

from prc.paths import RAW, RAW_MANIFEST, ROOT

# Pre-reissue (stale) files, hashes posted on forum by a participant on 2026-09-22.
STALE = {
    "25556E61C5F71020287CA130377CE079DC22D2FA7F7F1EAF4A2F22ACAFAB463D": "ranking.parquet (pre 2026-09-04 reissue)",
    "241724D8C234D2C34C96519EF1B6891646E694B142BFF2C3504E83A394EE8F73": "submitting.parquet (pre 2026-09-04 reissue)",
}
FIELDS = ["file", "bytes", "sha256", "bucket_path", "downloaded_at"]


def sha256(path, chunk=1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def raw_files():
    return sorted(p for p in RAW.rglob("*.parquet"))


def build() -> None:
    old = {}
    if RAW_MANIFEST.exists():
        with open(RAW_MANIFEST) as f:
            old = {r["file"]: r for r in csv.DictReader(f)}
    rows = []
    for p in raw_files():
        rel = str(p.relative_to(ROOT))
        prev = old.get(rel, {})
        mtime = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
        rows.append({
            "file": rel,
            "bytes": p.stat().st_size,
            "sha256": sha256(p),
            "bucket_path": prev.get("bucket_path", "unknown"),
            "downloaded_at": prev.get("downloaded_at", mtime),
        })
    with open(RAW_MANIFEST, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {RAW_MANIFEST}")


def verify() -> int:
    with open(RAW_MANIFEST) as f:
        rows = list(csv.DictReader(f))
    bad = 0
    for r in rows:
        p = ROOT / r["file"]
        if not p.exists():
            print(f"MISSING  {r['file']}")
            bad += 1
            continue
        h = sha256(p)
        if h.upper() in STALE:
            print(f"STALE    {r['file']}: matches {STALE[h.upper()]} — re-download from the bucket")
            bad += 1
        elif h != r["sha256"] or p.stat().st_size != int(r["bytes"]):
            print(f"MISMATCH {r['file']}")
            bad += 1
    listed = {r["file"] for r in rows}
    for p in raw_files():
        if str(p.relative_to(ROOT)) not in listed:
            print(f"UNLISTED {p.relative_to(ROOT)}")
            bad += 1
    print(f"verify-raw: {len(rows)} files, {bad} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "build":
        build()
    else:
        sys.exit(verify())
