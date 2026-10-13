"""Fetch OpenStreetMap aeroway features (stands, holding points, de-icing pads) for the 10 airports via Overpass.

ODbL (https://www.openstreetmap.org/copyright, snapshot docs/references/licences/osm_copyright_2026-10-02.html).
Reproducible: every query is pinned to SNAPSHOT with the Overpass [date:...] setting; the raw JSON response is
stored unmodified and checksummed in data/external/MANIFEST.csv. Existing listed files are never overwritten.
The response header carries the server's current database time (osm3s.timestamp_osm_base), so a re-download never
has the same raw bytes; in a fresh clone the `elements` (the only part the pipeline reads, sql/00_ingest/07) must
match ELEMENTS_SHA256, the hashes of our archived 2026-10-02 responses, or the script stops.
  uv run python scripts/fetch/osm_aeroway.py
"""
import hashlib
import os
import sys
import time

import orjson
import requests

from prc import fetchutil as F
from prc.paths import ROOT

OUT = ROOT / "data" / "external" / "osm_aeroway" / "raw"
URL = "https://overpass-api.de/api/interpreter"
SNAPSHOT = "2026-10-01T00:00:00Z"
AIRPORTS = ["EDDF", "EDDM", "EGLL", "EHAM", "LEBL", "LEMD", "LFPG", "LIRF", "LSZH", "LTFM"]
# SHA256 of orjson.dumps(response["elements"], option=OPT_SORT_KEYS) for the archived responses (2026-10-02)
ELEMENTS_SHA256 = {
    "EDDF": "6ec501c7a9207cf45ae8e21f2c87846da2959a5829d14785798881922a7e46c1",
    "EDDM": "af37337cdd04b34e6754d5907770c33b314fa6714808193bdcc782896edddc66",
    "EGLL": "7f61b06f157f16dd34ebab761b5f0ef2bc1b26be36637b9af17d487497a1e2c4",
    "EHAM": "c86532dace3715c0b8b26f080206b7418ce8f7a4d682e560fc7ec4f73c6db37e",
    "LEBL": "bfe51d7ab0d16dd836508e35731d6187587819a7ac9d795b52abbcdd0b4c2d4e",
    "LEMD": "d87ad63bdb1c6bc7568d4a99b7ec91cd5b60e95d72b252d00eebc8a0f31ac399",
    "LFPG": "c81fd7020b18d4fe041cc3cd9ca1d52a4527194d4efbe2f715c3bb422ae4c699",
    "LIRF": "6377683936406274b6e668c11810de14440865314e1400df19ce2e442957a9c9",
    "LSZH": "797571fdf0682af9b4691bf224a1341c9a0fee7f999cf434e59c43935d38a29e",
    "LTFM": "1fc47b3ad334676c4c47944c59708b44d31b12eb5f4801258e35cdbf89384815",
}


def elements_sha256(content: bytes) -> str:
    return hashlib.sha256(orjson.dumps(orjson.loads(content)["elements"], option=orjson.OPT_SORT_KEYS)).hexdigest()


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
        if elements_sha256(r.content) != ELEMENTS_SHA256[icao] and os.environ.get(F.ACCEPT_ENV) != "1":
            print(f"{icao}: OSM elements differ from the archived 2026-10-02 response — stop "
                  f"(set {F.ACCEPT_ENV}=1 to accept them; results may then differ from ours)")
            return 1
        p.write_bytes(r.content)
        # raw bytes differ from the manifest in the header timestamp only (elements checked above)
        print("got", F.record(p, "osm_aeroway", allow_change=True))
        time.sleep(10)
    return 0


if __name__ == "__main__":
    sys.exit(main())
