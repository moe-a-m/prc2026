"""adsb.lol globe_history (ODbL-1.0): stream-download daily dumps, extract airport-surface points, delete raw.

Two loops, run as separate processes (download is network-bound, extract is CPU-bound):

  uv run python scripts/fetch/adsblol.py download   # parts -> data/external/adsblol/raw_tmp/<tag>/ (≤ BUFFER days)
  uv run python scripts/fetch/adsblol.py extract    # -> data/external/adsblol/extract/<YYYY-MM-DD>.parquet

Which release per day: the upstream PREFERRED_RELEASES.txt (largest release per day), snapshotted and checksummed.
Every raw part is verified against the SHA256 digest GitHub publishes for the release asset, recorded in
data/external/MANIFEST.csv, and deleted after extraction (disk: ~388 GB total would not fit). Anyone can re-fetch
the identical bytes from the manifest. The extract keeps, for points inside a box around each challenge airport
(runway-threshold extent from OurAirports + MARGIN_KM), those on the ground or below MAX_ALT_FT.
Data card: docs/data_sources/adsblol.md.
"""
import bisect
import gzip
import io
import logging
import shutil
import sys
import tarfile
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import orjson
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests

from prc import fetchutil as F
from prc.paths import ROOT

BASE = ROOT / "data" / "external" / "adsblol"
RAW = BASE / "raw_tmp"
EXTRACT = BASE / "extract"
META = BASE / "meta"
LOGDIR = ROOT / "logs" / "fetch"
AIRPORTS = ["EDDF", "EDDM", "EGLL", "EHAM", "LEBL", "LEMD", "LFPG", "LIRF", "LSZH", "LTFM"]
MARGIN_KM = 2.0
MAX_ALT_FT = 3000
BUFFER = 3
N_CONN = 4


def days():
    """Jan and Jul of 2025 and 2026, interleaved so a partial run stays balanced between training and ranking."""
    out = []
    for d in range(31):
        for y, m in [(2026, 1), (2025, 1), (2026, 7), (2025, 7)]:
            out.append(date(y, m, 1) + timedelta(days=d))
    return out


def log_setup(name):
    LOGDIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        handlers=[logging.FileHandler(LOGDIR / f"adsblol_{name}.log"), logging.StreamHandler()])
    return logging.getLogger()


def preferred(year: int) -> dict:
    """date -> list of part URLs, from a checksummed snapshot of PREFERRED_RELEASES.txt."""
    META.mkdir(parents=True, exist_ok=True)
    p = META / f"PREFERRED_RELEASES_{year}.txt"
    if not p.exists():
        r = requests.get(f"https://raw.githubusercontent.com/adsblol/globe_history_{year}/main/PREFERRED_RELEASES.txt",
                         headers=F.UA, timeout=60)
        r.raise_for_status()
        p.write_bytes(r.content)
        F.record(p, "adsblol")
    out = {}
    for line in p.read_text().split():
        urls = line.split(",")
        tag = urls[0].split("/")[-2]                    # v2025.01.07-planes-readsb-staging-0
        y, m, d = tag[1:11].split(".")
        out[date(int(y), int(m), int(d))] = urls
    return out


def assets(year: int, tag: str) -> dict:
    """asset name -> (size, sha256) from the GitHub releases API (unauthenticated; ~1 call per day)."""
    cache = META / f"{tag}.assets.json"
    if not cache.exists():
        for attempt in range(10):
            r = requests.get(f"https://api.github.com/repos/adsblol/globe_history_{year}/releases/tags/{tag}",
                             headers={**F.UA, "Accept": "application/vnd.github+json"}, timeout=60)
            if r.status_code == 200:
                break
            time.sleep(120 * (attempt + 1))  # rate limit: 60 requests/hour unauthenticated
        r.raise_for_status()
        cache.write_bytes(r.content)
    js = orjson.loads(cache.read_bytes())
    return {a["name"]: (a["size"], (a.get("digest") or "").removeprefix("sha256:")) for a in js["assets"]}


def cmd_download():
    log = log_setup("download")
    prefs = {y: preferred(y) for y in (2025, 2026)}
    for day in days():
        tag_dir = None
        urls = prefs[day.year].get(day)
        if not urls:
            log.warning("%s: no preferred release", day)
            continue
        tag = urls[0].split("/")[-2]
        tag_dir = RAW / tag
        if (EXTRACT / f"{day}.parquet").exists() or (tag_dir / "READY").exists():
            continue
        while len([d for d in RAW.glob("*/READY")]) >= BUFFER:
            time.sleep(60)
        info = assets(day.year, tag)
        for u in urls:
            name = u.split("/")[-1]
            size, digest = info[name]
            dest = tag_dir / name
            if dest.exists() and F.listed(dest) and F.listed(dest)["sha256"] == digest:
                continue
            t0 = time.time()
            F.download(u, dest, n_conn=N_CONN, expected_size=size, log=log.info)
            sha = F.sha256_file(dest)
            if digest and sha != digest:
                dest.unlink()
                log.error("%s: SHA256 mismatch vs GitHub digest — removed, stop", name)
                return 1
            F.record(dest, "adsblol", sha=sha, size=size)
            log.info("%s %.2f GB in %.0f s (%.2f MB/s), sha256 ok", name, size / 1e9, time.time() - t0,
                     size / 1e6 / (time.time() - t0))
        (tag_dir / "READY").write_text(str(day))
    log.info("download loop finished")
    (RAW / "DOWNLOAD_DONE").write_text("done")
    return 0


class Concat(io.RawIOBase):
    """Sequential reader over the split tar parts (equivalent to `cat x.tar.aa x.tar.ab`)."""

    def __init__(self, paths):
        self.paths, self.i, self.f = list(paths), 0, None

    def readable(self):
        return True

    def readinto(self, b):
        while True:
            if self.f is None:
                if self.i >= len(self.paths):
                    return 0
                self.f = open(self.paths[self.i], "rb")
                self.i += 1
            n = self.f.readinto(b)
            if n:
                return n
            self.f.close()
            self.f = None


def boxes():
    r = pd.read_csv(ROOT / "data" / "external" / "ourairports" / "raw" / "runways.csv")
    r = r[r.airport_ident.isin(AIRPORTS) & (r.closed == 0)]
    out = []
    for a, g in r.groupby("airport_ident"):
        lat = np.r_[g.le_latitude_deg, g.he_latitude_deg]
        lon = np.r_[g.le_longitude_deg, g.he_longitude_deg]
        dlat = MARGIN_KM / 111.0
        dlon = MARGIN_KM / (111.0 * np.cos(np.radians(np.nanmean(lat))))
        out.append((a, np.nanmin(lat) - dlat, np.nanmax(lat) + dlat, np.nanmin(lon) - dlon, np.nanmax(lon) + dlon))
    return out


SCHEMA = pa.schema([("airport", pa.string()), ("icao24", pa.string()), ("reg", pa.string()), ("actype", pa.string()),
                    ("callsign", pa.string()), ("ts", pa.float64()), ("lat", pa.float64()), ("lon", pa.float64()),
                    ("alt_ft", pa.float64()), ("on_ground", pa.bool_()), ("gs_kt", pa.float64()),
                    ("track_deg", pa.float64()), ("new_leg", pa.bool_()), ("src", pa.string())])


def extract_trace(d, bx, cols):
    tr = d.get("trace") or []
    if not tr:
        return
    lat = np.fromiter((p[1] if p[1] is not None else np.nan for p in tr), float, len(tr))
    lon = np.fromiter((p[2] if p[2] is not None else np.nan for p in tr), float, len(tr))
    hit = False
    for a, la0, la1, lo0, lo1 in bx:
        m = (lat >= la0) & (lat <= la1) & (lon >= lo0) & (lon <= lo1)
        if m.any():
            hit = True
            for i in np.flatnonzero(m):
                p = tr[i]
                alt = p[3]
                ground = alt == "ground"
                if not ground and (alt is None or alt > MAX_ALT_FT):
                    continue
                cols["airport"].append(a)
                cols["idx"].append(i)
                cols["ts"].append(d["timestamp"] + p[0])
                cols["lat"].append(p[1]); cols["lon"].append(p[2])
                cols["alt_ft"].append(np.nan if ground else float(alt)); cols["on_ground"].append(ground)
                cols["gs_kt"].append(p[4] if p[4] is not None else np.nan)
                cols["track_deg"].append(p[5] if p[5] is not None else np.nan)
                cols["new_leg"].append(bool((p[6] or 0) & 2))
                cols["src"].append(p[9] if len(p) > 9 else None)
                cols["icao24"].append(d.get("icao")); cols["reg"].append(d.get("r")); cols["actype"].append(d.get("t"))
                cols["_trace"].append(len(cols["_traces"]))
    if hit:
        # callsign: latest 'flight' seen in the trace details at or before each point (details dict at p[8])
        flights = [(j, p[8]["flight"]) for j, p in enumerate(tr) if len(p) > 8 and isinstance(p[8], dict) and p[8].get("flight")]
        cols["_traces"].append(flights)


def process_parts(parts, bx, strict=True):
    """Stream the concatenated tar parts; return (table of kept points, n trace files, n unreadable)."""
    n_files, n_bad = 0, 0
    cols = {k: [] for k in ["airport", "idx", "ts", "lat", "lon", "alt_ft", "on_ground", "gs_kt", "track_deg",
                            "new_leg", "src", "icao24", "reg", "actype", "_trace", "_traces"]}
    try:
        with tarfile.open(fileobj=io.BufferedReader(Concat(parts), 1 << 22), mode="r|") as tar:
            for m in tar:
                if not (m.isfile() and "/trace_full_" in m.name):
                    continue
                n_files += 1
                try:
                    raw = tar.extractfile(m).read()
                    d = orjson.loads(gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw)
                except Exception:  # noqa: BLE001 — corrupt member: count it, keep going
                    n_bad += 1
                    continue
                extract_trace(d, bx, cols)
    except tarfile.ReadError:
        if strict:
            raise
    cs = []
    for t, i in zip(cols["_trace"], cols["idx"]):
        fl = cols["_traces"][t]
        k = bisect.bisect_right([j for j, _ in fl], i) if fl else 0
        cs.append(fl[k - 1][1].strip() if k else None)
    tbl = pa.table({k: cols[k] for k in SCHEMA.names if k != "callsign"} | {"callsign": cs}).select(SCHEMA.names)
    return tbl.cast(SCHEMA), n_files, n_bad


def cmd_extract():
    log = log_setup("extract")
    EXTRACT.mkdir(parents=True, exist_ok=True)
    bx = boxes()
    while True:
        ready = sorted(RAW.glob("*/READY"))
        if not ready:
            if (RAW / "DOWNLOAD_DONE").exists():
                log.info("extract loop finished")
                return 0
            time.sleep(60)
            continue
        tag_dir = ready[0].parent
        day = ready[0].read_text().strip()
        parts = sorted(p for p in tag_dir.iterdir() if ".tar" in p.name and not p.name.endswith(".part"))
        t0 = time.time()
        tbl, n_files, n_bad = process_parts(parts, bx)
        out = EXTRACT / f"{day}.parquet"
        pq.write_table(tbl, out, compression="zstd")
        F.record(out, "adsblol_extract")
        log.info("%s: %d trace files (%d unreadable), %d points kept, %.1f MB, %.0f s", day, n_files, n_bad,
                 tbl.num_rows, out.stat().st_size / 1e6, time.time() - t0)
        shutil.rmtree(tag_dir)  # raw parts deleted; their SHA256 stays in the manifest


if __name__ == "__main__":
    sys.exit({"download": cmd_download, "extract": cmd_extract}[sys.argv[1]]())
