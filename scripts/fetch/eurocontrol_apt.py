"""Fetch EUROCONTROL Aviation Intelligence Portal airport datasets (ansperformance.eu), files kept unmodified.

Terms (https://ansperformance.eu/about/disclaimer/, snapshot docs/references/licences/): copying allowed with
EUROCONTROL as source, non-commercial, no modification without permission. Challenge eligibility: organizer
rulings 17/09/2026 and 27/09/2026 (docs/data_sources/eurocontrol_apt.md). Used only behind a config flag.
  uv run python scripts/fetch/eurocontrol_apt.py
"""
import sys
import time

import requests

from prc import fetchutil as F
from prc.paths import ROOT

OUT = ROOT / "data" / "external" / "eurocontrol_apt" / "raw"
BASE = "https://www.eurocontrol.int/performance/data/download/csv/"
NAMES = ["taxi_out_additional_time_{y}.csv", "airport_traffic_{y}.csv", "apt_dly_{y}.csv.bz2",
         "all_pre_departure_delays_{y}.csv", "atfm_slot_adherence_{y}.csv"]
YEARS = [2025, 2026]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for y in YEARS:
        for pat in NAMES:
            name = pat.format(y=y)
            p = OUT / name
            row = F.listed(p)
            if p.exists() and row:
                if F.sha256_file(p) != row["sha256"]:
                    print(f"CHECKSUM MISMATCH {p} — stop")
                    return 1
                print(f"skip {name}")
                continue
            r = requests.get(BASE + name, headers=F.UA, timeout=300)
            r.raise_for_status()
            p.write_bytes(r.content)
            print("got", F.record(p, "eurocontrol_apt"))
            time.sleep(2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
