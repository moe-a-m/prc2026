"""Fetch OurAirports airports.csv and runways.csv (public domain) — runway thresholds for airport geometry.

Files are updated nightly upstream, so each retrieval is pinned by SHA256 in data/external/MANIFEST.csv;
an existing listed file is never overwritten (delete it deliberately to refresh, CLAUDE.md §5).
  uv run python scripts/fetch/ourairports.py
"""
import sys
from pathlib import Path

import requests

from prc import fetchutil as F
from prc.paths import ROOT

OUT = ROOT / "data" / "external" / "ourairports" / "raw"
FILES = ["airports.csv", "runways.csv"]
BASE = "https://davidmegginson.github.io/ourairports-data/"


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
