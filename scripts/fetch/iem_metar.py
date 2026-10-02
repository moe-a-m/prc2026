"""Fetch METAR/SPECI for the 10 challenge airports from the IEM ASOS archive (CLAUDE.md §6).

Writes unmodified response bytes to data/external/iem_metar/raw/<ICAO>_<start>_<end>.csv and records
path/bytes/SHA256/retrieved_at in data/external/MANIFEST.csv. Idempotent: a file already listed with a
matching SHA256 is skipped; a listed file whose bytes changed stops the run (never overwritten silently).
API: https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?help (snapshot in docs/references/).
Throttle: the service enforces 1 request/s per IP; we wait 5 s between requests.

  uv run python scripts/fetch/iem_metar.py
"""
import csv
import hashlib
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "external" / "iem_metar" / "raw"
MANIFEST = ROOT / "data" / "external" / "MANIFEST.csv"
LOG = ROOT / "logs" / "fetch"
URL = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
STATIONS = ["EDDF", "EDDM", "EGLL", "EHAM", "LEBL", "LEMD", "LFPG", "LIRF", "LSZH", "LTFM"]
# training year and ranking months, with ≥1 day margin each side
PERIODS = [("2024-12-30T00:00:00Z", "2026-01-03T00:00:00Z"),
           ("2025-12-30T00:00:00Z", "2026-08-03T00:00:00Z")]
PARAMS = {"data": "all", "tz": "Etc/UTC", "format": "onlycomma", "latlon": "yes", "elev": "yes",
          "missing": "M", "trace": "T"}
FIELDS = ["path", "bytes", "sha256", "retrieved_at", "source_id"]


def load_manifest():
    if not MANIFEST.exists():
        return []
    with open(MANIFEST) as f:
        return list(csv.DictReader(f))


def save_manifest(rows):
    with open(MANIFEST, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r["path"]))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    LOG.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        handlers=[logging.FileHandler(LOG / "iem_metar.log"), logging.StreamHandler()])
    rows = load_manifest()
    known = {r["path"]: r for r in rows}
    logging.info("requests %s, python %s", requests.__version__, sys.version.split()[0])
    for sts, ets in PERIODS:
        for st in STATIONS:
            path = OUT / f"{st}_{sts[:10]}_{ets[:10]}.csv"
            rel = str(path.relative_to(ROOT))
            if path.exists() and rel in known:
                h = hashlib.sha256(path.read_bytes()).hexdigest()
                if h != known[rel]["sha256"]:
                    logging.error("CHECKSUM MISMATCH %s — stop (CLAUDE.md §5 re-fetch policy)", rel)
                    return 1
                logging.info("skip %s (present, checksum ok)", rel)
                continue
            for attempt in range(5):
                r = requests.get(URL, params={**PARAMS, "station": st, "sts": sts, "ets": ets}, timeout=300)
                if r.status_code == 200 and r.content.startswith(b"station,valid"):
                    break
                logging.warning("%s %s attempt %d: HTTP %s %r", st, sts, attempt, r.status_code, r.content[:120])
                time.sleep(30 * (attempt + 1))
            else:
                logging.error("giving up on %s %s", st, sts)
                return 1
            path.write_bytes(r.content)
            rec = {"path": rel, "bytes": len(r.content), "sha256": hashlib.sha256(r.content).hexdigest(),
                   "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "source_id": "iem_metar"}
            known[rel] = rec
            rows = [x for x in rows if x["path"] != rel] + [rec]
            save_manifest(rows)
            logging.info("got %s %d bytes %s", rel, rec["bytes"], r.url)
            time.sleep(5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
