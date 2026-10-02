"""Fetch OpenStreetMap aeroway features (stands, holding points, de-icing pads) for the 10 airports via Overpass.

ODbL (https://www.openstreetmap.org/copyright, snapshot docs/references/licences/osm_copyright_2026-10-02.html).
Reproducible: every query is pinned to SNAPSHOT with the Overpass [date:...] setting; the raw JSON response is
stored unmodified and checksummed in data/external/MANIFEST.csv. Existing listed files are never overwritten.
  uv run python scripts/fetch/osm_aeroway.py
"""
import sys
import time

import requests

from prc import fetchutil as F
from prc.paths import ROOT

OUT = ROOT / "data" / "external" / "osm_aeroway" / "raw"
URL = "https://overpass-api.de/api/interpreter"
SNAPSHOT = "2026-10-01T00:00:00Z"
AIRPORTS = ["EDDF", "EDDM", "EGLL", "EHAM", "LEBL", "LEMD", "LFPG", "LIRF", "LSZH", "LTFM"]
QUERY = ('[out:json][timeout:170][date:"{snap}"];area["aeroway"="aerodrome"]["icao"="{icao}"]->.a;'
         'nwr(area.a)["aeroway"~"^(parking_position|holding_position|deicing_pad|gate)$"];out tags center;')


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for icao in AIRPORTS:
        p = OUT / f"{icao}_{SNAPSHOT[:10]}.json"
        row = F.listed(p)
        if p.exists() and row:
            if F.sha256_file(p) != row["sha256"]:
                print(f"CHECKSUM MISMATCH {p} — stop")
                return 1
            print(f"skip {p.name}")
            continue
        for attempt in range(6):
            r = requests.post(URL, data={"data": QUERY.format(snap=SNAPSHOT, icao=icao)}, headers=F.UA, timeout=240)
            if r.status_code == 200 and r.content.lstrip().startswith(b"{"):
                break
            print(f"{icao}: HTTP {r.status_code}, retry {attempt + 1}")
            time.sleep(30 * (attempt + 1))
        else:
            return 1
        p.write_bytes(r.content)
        print("got", F.record(p, "osm_aeroway"))
        time.sleep(10)
    return 0


if __name__ == "__main__":
    sys.exit(main())
