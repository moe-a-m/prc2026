"""adsb.lol globe_history (ODbL-1.0): stream-download daily dumps, extract airport-surface points, delete raw.

Two loops, run as separate processes (download is network-bound, extract is CPU-bound):

  uv run python scripts/fetch/adsblol.py download [SET]  # parts -> data/external/adsblol/raw_tmp/<tag>/ (≤ BUFFER days)
  uv run python scripts/fetch/adsblol.py extract         # -> data/external/adsblol/extract/<YYYY-MM-DD>.parquet
  (`make fetch-adsblol ADSB_DAYS=<SET>` runs both)
  GITHUB_TOKEN=$(gh auth token) uv run python scripts/fetch/adsblol.py assets   # asset lists for days_more()

SET (which days to download; days already extracted are skipped):
  janjul  Jan + Jul of 2025 and 2026 (default; the public phase and the Jan/Jul 2025 hold-outs, `make validate`)
  final   Jan, Feb, Jun, Jul 2026: the scored days of the final phase (`make predict` needs these)
  all     every 2025 day + Jan, Feb, Jun, Jul 2026 (also `make validate-fullyear`)
We fetched the days_more() set on Modal (scripts/modal/app.py::fetch_adsblol) for bandwidth; the local loops fetch the
same release assets, checked against the same GitHub SHA256 digests.

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
import os
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
BUFFER = int(os.environ.get("ADSBLOL_BUFFER", "3"))  # raw days waiting for extraction (≈ 4 GB each)
N_CONN = 4


def days():
    """Jan and Jul of 2025 and 2026 in priority order (bandwidth is the bottleneck, ~1-2 MB/s):
    1) every 2026 day interleaved with every second 2025 day (ranking rows need their own day; the model needs
       enough labelled 2025 days to learn the ADS-B features), 2) the remaining 2025 days."""
    first, rest = [], []
    for d in range(31):
        first += [date(2026, 1, 1) + timedelta(days=d), date(2026, 7, 1) + timedelta(days=d)]
        pair = [date(2025, 1, 1) + timedelta(days=d), date(2025, 7, 1) + timedelta(days=d)]
        (first if d % 2 == 0 else rest).extend(pair)
    return first + rest


def days_more():
    """Days added for the final phase (organizer e-mail 2026-10-08: Jan, Feb, Jun, Jul 2026 scored) and the full-year
    hold-out check: Feb and Jun 2026 first (needed for the final submission), then every 2025 day outside Jan/Jul."""
    def month(y, m):
        d = date(y, m, 1)
        while d.month == m:
            yield d
            d += timedelta(days=1)
    out = [d for m in (2, 6) for d in month(2026, m)]
    return out + [d for m in (2, 3, 4, 5, 6, 8, 9, 10, 11, 12) for d in month(2025, m)]


DAY_SETS = {
    "janjul": lambda: days(),
    "final": lambda: [d for d in days() + days_more() if d.year == 2026],
    "all": lambda: days() + days_more(),
}


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
        # upstream appends new days every day, so a fresh snapshot differs from ours; the day -> release choice is
        # still checked downstream (release parts by GitHub SHA256, extracts against the manifest)
        F.record(p, "adsblol", allow_change=True)
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
        r = None
        for attempt in range(10):
            try:
                # optional GITHUB_TOKEN: 5,000 instead of 60 requests/hour; the response is the same public JSON
                auth = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"} if os.environ.get("GITHUB_TOKEN") else {}
                r = requests.get(f"https://api.github.com/repos/adsblol/globe_history_{year}/releases/tags/{tag}",
                                 headers={**F.UA, "Accept": "application/vnd.github+json", **auth}, timeout=60)
            except requests.RequestException:  # network outage: wait and retry like the downloads
                r = None
            if r is not None and r.status_code == 200:
                break
            time.sleep(120 * (attempt + 1))  # rate limit: 60 requests/hour unauthenticated
        if r is None:
            raise RuntimeError(f"GitHub API unreachable for {tag}")
        r.raise_for_status()
        cache.write_bytes(r.content)
    js = orjson.loads(cache.read_bytes())
    return {a["name"]: (a["size"], (a.get("digest") or "").removeprefix("sha256:")) for a in js["assets"]}


def cmd_download():
    log = log_setup("download")
    sel = sys.argv[2] if len(sys.argv) > 2 else "janjul"
    if sel not in DAY_SETS:
        raise SystemExit(f"unknown day set {sel!r}; choose one of {sorted(DAY_SETS)}")
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "DOWNLOAD_DONE").unlink(missing_ok=True)  # a marker left by an earlier run would stop `extract` early
    prefs = {y: preferred(y) for y in (2025, 2026)}
    for day in DAY_SETS[sel]():
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
            while True:  # network outages: wait and resume (chunks already written are kept)
                try:
                    F.download(u, dest, n_conn=N_CONN, expected_size=size, log=log.info)
                    break
                except (IOError, requests.RequestException) as e:
                    log.warning("%s: %s — retrying in 5 min", name, e)
                    time.sleep(300)
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


def cmd_assets():
    """Cache the release-asset JSON (sizes + SHA256 digests) of every days_more() day, for the Modal fetch
    (scripts/modal/app.py::fetch_adsblol), whose containers read META from the volume."""
    log = log_setup("assets")
    prefs = {y: preferred(y) for y in (2025, 2026)}
    n = 0
    for day in days_more():
        urls = prefs[day.year].get(day)
        if not urls:
            log.warning("%s: no preferred release", day)
            continue
        assets(day.year, urls[0].split("/")[-2])
        n += 1
    log.info("asset lists cached for %d days", n)
    return 0


def cmd_merge():
    """Merge the per-day manifest rows written by the Modal fetch (data/external/adsblol/manifest_parts/*.csv, copied
    from the volume) into data/external/MANIFEST.csv, after checking every listed extract present locally."""
    import csv
    log = log_setup("merge")
    new = {}
    for p in sorted((BASE / "manifest_parts").glob("*.csv")):
        with open(p) as f:
            for r in csv.DictReader(f):
                new[r["path"]] = r
    bad = 0
    for path, r in new.items():
        if r["source_id"] == "adsblol_extract":
            local = ROOT / path
            if not local.exists() or F.sha256_file(local) != r["sha256"]:
                log.error("%s: missing locally or SHA256 differs from the Modal record", path)
                bad += 1
    if bad:
        return 1
    rows = {r["path"]: r for r in F.manifest_rows()}
    for path, r in new.items():
        if path in rows and rows[path]["sha256"] != r["sha256"]:
            log.error("%s: already listed with another SHA256 — not overwritten", path)
            return 1
    rows.update(new)
    with open(F.MANIFEST, "w", newline="") as f:
        w = csv.DictWriter(f, F.FIELDS)
        w.writeheader()
        w.writerows(sorted(rows.values(), key=lambda r: r["path"]))
    log.info("merged %d rows from %d day files", len(new), len(list((BASE / "manifest_parts").glob("*.csv"))))
    return 0


def download_then_mark():
    """`download`, then the DOWNLOAD_DONE marker even on failure, so a parallel `extract` finishes the ready days and
    exits instead of waiting forever (`make fetch-adsblol` runs both and returns the download's status)."""
    try:
        return cmd_download()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "DOWNLOAD_DONE").write_text("done")


if __name__ == "__main__":
    cmds = {"download": download_then_mark, "extract": cmd_extract, "assets": cmd_assets, "merge": cmd_merge}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        raise SystemExit(__doc__)
    sys.exit(cmds[sys.argv[1]]())
