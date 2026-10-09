"""Run a pipeline command on Modal (optional speed-up for experiments; the reference path stays `make reproduce` locally).

Container: python 3.14 + `uv sync --frozen` from this repo's uv.lock, repo code (incl. .git for provenance) at /repo.
Volume `prc2026-data` (private) holds raw/ (challenge files), external/, prc.duckdb, models/ and runs/<run_id>/.
Inside the container data/raw, data/external, models are symlinks into the volume; prc.duckdb is copied to local disk
and copied back only with --write-db. reports/, logs/, docs/ changes are saved to runs/<run_id>/ for `sync.py`.
Every launch passes the budget guard (scripts/modal/budget.py) first.

  PYENV_VERSION=3.13.15 modal run --detach scripts/modal/app.py --run-id smoke --timeout-h 0.25 \
      --cmd "python -m prc.manifest verify"
"""
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

import modal

if modal.is_local():  # inside the container this file is /root/app.py; repo paths and the guard are local-only
    HERE = Path(__file__).resolve().parent
    ROOT = HERE.parents[1]
    sys.path.insert(0, str(HERE))
    import budget  # noqa: E402
else:
    ROOT = Path("/repo")

VOL = modal.Volume.from_name("prc2026-data")
IGNORE = [".venv", "data", "models", "submissions", "logs", "**/__pycache__", "*.duckdb", ".env", ".pytest_cache"]
image = (modal.Image.from_registry("python:3.14.7-slim-bookworm")
         .apt_install("git", "make")
         .uv_sync(str(ROOT), frozen=True, uv_version="0.12.20")
         .apt_install("libgomp1")  # OpenMP runtime needed by the LightGBM wheel
         .env({"PYTHONPATH": "/repo/src", "PYTHONUNBUFFERED": "1"})
         .add_local_dir(ROOT, "/repo", ignore=IGNORE))
app = modal.App("prc2026", image=image)


@app.function(volumes={"/vol": VOL}, timeout=86400, cpu=2.0, memory=16384, nonpreemptible=True)
def run_np(cmd: str, run_id: str, write_db: bool = False) -> int:
    """Same as run(), never preempted (3x CPU/memory price; https://modal.com/docs/guide/preemption). For long jobs
    that were preempted repeatedly (det3-cat-s11, 2026-10-06)."""
    return run.local(cmd, run_id, write_db)


@app.function(volumes={"/vol": VOL}, timeout=86400, cpu=2.0, memory=16384)
def run(cmd: str, run_id: str, write_db: bool = False) -> int:
    import os
    import shutil
    import subprocess

    repo, vol = Path("/repo"), Path("/vol")
    (repo / "data").mkdir(exist_ok=True)
    for name, target in [("data/raw", vol / "raw"), ("data/external", vol / "external"), ("models", vol / "models"), ("submissions", vol / "submissions")]:
        target.mkdir(parents=True, exist_ok=True)
        if not (repo / name).exists():
            (repo / name).symlink_to(target)
    (repo / "logs").mkdir(exist_ok=True)
    db_vol, db = vol / "prc.duckdb", repo / "data" / "prc.duckdb"
    if db_vol.exists():
        shutil.copy2(db_vol, db)
    out = vol / "runs" / run_id
    out.mkdir(parents=True, exist_ok=True)
    import time
    start = time.time() - 1
    # volume writes become visible outside this container only on commit(); commit every 10 min while the command runs
    # so finished work (per-fold hold-out files, stdout.log) survives a timeout or preemption (fy-cat-*, 2026-10-08)
    import threading
    stop = threading.Event()

    def _commit_loop():
        while not stop.wait(600):
            try:
                VOL.commit()
            except Exception as e:  # noqa: BLE001 — a failed periodic commit must not kill the run
                print(f"periodic volume commit failed: {e}")

    threading.Thread(target=_commit_loop, daemon=True).start()
    with open(out / "stdout.log", "w") as log:
        rc = subprocess.run(["bash", "-o", "pipefail", "-c", cmd], cwd=repo, stdout=log, stderr=subprocess.STDOUT,
                            env={**os.environ}).returncode
    stop.set()
    # copy back only files the command wrote (an unchanged image copy of docs/ once overwrote newer local docs)
    changed = []
    for d in ("reports", "logs", "docs"):
        for f in (repo / d).rglob("*") if (repo / d).exists() else []:
            if f.is_file() and f.stat().st_mtime >= start:
                rel = f.relative_to(repo)
                (out / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, out / rel)
                changed.append(str(rel))
    (out / "changed.txt").write_text("\n".join(sorted(changed)) + "\n")
    if write_db and rc == 0 and db.exists():
        shutil.copy2(db, db_vol)
    (out / "exit_code").write_text(str(rc))
    VOL.commit()
    return rc


ADSB_TIMEOUT_S = 1800  # one day took ~5 min on Modal (2026-02-01 test: 2.8 GB in ~30 s + ~4 min extraction)


@app.function(volumes={"/vol": VOL}, timeout=ADSB_TIMEOUT_S, cpu=1.0, memory=4096,
              max_containers=20, retries=1)
def adsblol_day(day_iso: str) -> str:
    """adsb.lol for one day (scripts/fetch/adsblol.py, same code paths): download the preferred release parts to the
    container's disk, check each against the GitHub SHA256 digest, extract airport-surface points to the volume's
    external/adsblol/extract/<day>.parquet, write the day's manifest rows to external/adsblol/manifest_parts/<day>.csv
    (merged into data/external/MANIFEST.csv locally by `adsblol.py merge`), delete the raw parts."""
    import csv
    import shutil
    from datetime import date

    repo, vol = Path("/repo"), Path("/vol")
    (repo / "data").mkdir(exist_ok=True)
    if not (repo / "data" / "external").exists():
        (repo / "data" / "external").symlink_to(vol / "external")
    sys.path.insert(0, str(repo / "scripts" / "fetch"))
    import adsblol as A
    from prc import fetchutil as F

    day = date.fromisoformat(day_iso)
    out = A.EXTRACT / f"{day}.parquet"
    parts_dir = vol / "external" / "adsblol" / "manifest_parts"
    rows_path = parts_dir / f"{day}.csv"
    if out.exists() and rows_path.exists():
        return f"{day}: already done"
    for year in (day.year, day.year + 1):  # 2025-12-31 is listed in the 2026 repository
        prefs = A.preferred(year)
        if day in prefs:
            urls = prefs[day]
            break
    else:
        raise RuntimeError(f"{day}: no preferred release")
    tag = urls[0].split("/")[-2]
    info = A.assets(year, tag)
    tmp = Path("/tmp/adsblol") / tag
    rows, parts = [], []
    now = lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")  # noqa: E731
    for u in urls:
        name = u.split("/")[-1]
        size, digest = info[name]
        dest = tmp / name
        F.download(u, dest, n_conn=8, expected_size=size, log=print)
        sha = F.sha256_file(dest)
        if digest and sha != digest:
            raise RuntimeError(f"{name}: SHA256 {sha} != GitHub digest {digest}")
        rows.append({"path": f"data/external/adsblol/raw_tmp/{tag}/{name}", "bytes": size, "sha256": sha,
                     "retrieved_at": now(), "source_id": "adsblol"})
        parts.append(dest)
    tbl, n_files, n_bad = A.process_parts(sorted(parts), A.boxes())
    part_out = out.with_name(f".{out.name}.part")
    A.pq.write_table(tbl, part_out, compression="zstd")
    part_out.rename(out)
    rows.append({"path": f"data/external/adsblol/extract/{day}.parquet", "bytes": out.stat().st_size,
                 "sha256": F.sha256_file(out), "retrieved_at": now(), "source_id": "adsblol_extract"})
    parts_dir.mkdir(parents=True, exist_ok=True)
    with open(rows_path, "w", newline="") as f:
        w = csv.DictWriter(f, F.FIELDS)
        w.writeheader()
        w.writerows(rows)
    shutil.rmtree(tmp)
    VOL.commit()
    msg = f"{day}: {n_files} trace files ({n_bad} unreadable), {tbl.num_rows} points kept"
    print(msg)
    return msg


@app.local_entrypoint()
def fetch_adsblol(run_id: str = "", limit: int = 0):
    """Spawn adsblol_day for every days_more() day without an extract on the volume (use with `modal run --detach`):
    PYENV_VERSION=3.13.15 modal run --detach scripts/modal/app.py::fetch_adsblol --run-id adsb-more-1"""
    import subprocess  # the local modal client's Python lacks the project dependencies: ask the project env
    listing = subprocess.run(["uv", "run", "--frozen", "python", "-c", "import sys; sys.path.insert(0, 'scripts/fetch'); "
                              "import adsblol as A; print(' '.join(map(str, A.days_more())))"],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    done = {e.path.rsplit("/", 1)[-1] for e in VOL.listdir("external/adsblol/manifest_parts")} \
        if any(e.path.endswith("manifest_parts") for e in VOL.listdir("external/adsblol")) else set()
    days = [d for d in listing if f"{d}.csv" not in done]
    days = days[:limit] if limit else days
    if not days:
        print("nothing to fetch")
        return
    run_id = run_id or datetime.now(timezone.utc).strftime("adsb-%Y%m%dT%H%M%S")
    # worst case: every day runs to its timeout; 5 GiB = 4 GiB memory + disk margin
    budget.authorize(run_id, 1.0, 5, ADSB_TIMEOUT_S * len(days), f"adsblol_day x {len(days)}: {days[0]} .. {days[-1]}")
    adsblol_day.spawn_map(days)
    print(f"run {run_id}: spawned adsblol_day for {len(days)} days ({days[0]} .. {days[-1]})")


@app.local_entrypoint()
def main(cmd: str, run_id: str = "", cpu: float = 2.0, memory_gib: int = 16, timeout_h: float = 6.0,
         write_db: bool = False, spawn: bool = False, nonpreemptible: bool = False):
    """--spawn (use with `modal run --detach`): submit and return at once, so a local network drop cannot cancel the
    job (2026-10-05: four detached jobs were cancelled when the blocking client hit a DNS failure). Results are read
    from the volume (runs/<run_id>/exit_code) with sync.py."""
    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    timeout_s = int(timeout_h * 3600)
    budget.authorize(run_id, cpu, memory_gib, timeout_s, cmd,  # raises SystemExit when over the cap
                     price_multiplier=3.0 if nonpreemptible else 1.0)
    f = (run_np if nonpreemptible else run).with_options(cpu=cpu, memory=memory_gib * 1024, timeout=timeout_s)
    print(f"run {run_id}: {shlex.quote(cmd)} (cpu {cpu}, {memory_gib} GiB, timeout {timeout_h} h)")
    if spawn:
        call = f.spawn(cmd, run_id, write_db)
        print(f"run {run_id} spawned: function call {call.object_id}")
        return
    rc = f.remote(cmd, run_id, write_db)
    print(f"run {run_id} exit code {rc}")
