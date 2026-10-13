"""Fetch OurAirports airports.csv and runways.csv (public domain) — runway thresholds for airport geometry.

Files are updated nightly upstream. We retrieved them on 2026-10-02 from the project's site; the same bytes are in
the upstream git repository at commit ac08c30 (2026-10-02 01:53 UTC; SHA256 of both files checked equal to the
manifest on 2026-10-13), so the download is pinned to that commit and a fresh clone gets the identical files.
Each file's SHA256 is in data/external/MANIFEST.csv; a listed file is never overwritten.
  uv run python scripts/fetch/ourairports.py
"""
import sys
from pathlib import Path

import requests

from prc import fetchutil as F
from prc.paths import ROOT

OUT = ROOT / "data" / "external" / "ourairports" / "raw"
FILES = ["airports.csv", "runways.csv"]
COMMIT = "ac08c301fd36bc1b9ea2bf4acfd4fef691360b5c"  # github.com/davidmegginson/ourairports-data
BASE = f"https://raw.githubusercontent.com/davidmegginson/ourairports-data/{COMMIT}/"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        p = OUT / name
        row = F.listed(p)
        if p.exists() and row:
            if F.sha256_file(p) != row["sha256"]:
                print(f"CHECKSUM MISMATCH {p} — stop")
                return 1
            print(f"skip {name} (present, checksum ok)")
            continue
        r = requests.get(BASE + name, headers=F.UA, timeout=300)
        r.raise_for_status()
        p.write_bytes(r.content)
        print("got", F.record(p, "ourairports"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
