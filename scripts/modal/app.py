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
    with open(out / "stdout.log", "w") as log:
        rc = subprocess.run(["bash", "-o", "pipefail", "-c", cmd], cwd=repo, stdout=log, stderr=subprocess.STDOUT,
                            env={**os.environ}).returncode
    for d in ("reports", "logs", "docs"):
        if (repo / d).exists():
            shutil.copytree(repo / d, out / d, dirs_exist_ok=True)
    if write_db and rc == 0 and db.exists():
        shutil.copy2(db, db_vol)
    (out / "exit_code").write_text(str(rc))
    VOL.commit()
    return rc


@app.local_entrypoint()
def main(cmd: str, run_id: str = "", cpu: float = 2.0, memory_gib: int = 16, timeout_h: float = 6.0,
         write_db: bool = False, spawn: bool = False):
    """--spawn (use with `modal run --detach`): submit and return at once, so a local network drop cannot cancel the
    job (2026-10-05: four detached jobs were cancelled when the blocking client hit a DNS failure). Results are read
    from the volume (runs/<run_id>/exit_code) with sync.py."""
    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    timeout_s = int(timeout_h * 3600)
    budget.authorize(run_id, cpu, memory_gib, timeout_s, cmd)  # raises SystemExit when over the cap
    f = run.with_options(cpu=cpu, memory=memory_gib * 1024, timeout=timeout_s)
    print(f"run {run_id}: {shlex.quote(cmd)} (cpu {cpu}, {memory_gib} GiB, timeout {timeout_h} h)")
    if spawn:
        call = f.spawn(cmd, run_id, write_db)
        print(f"run {run_id} spawned: function call {call.object_id}")
        return
    rc = f.remote(cmd, run_id, write_db)
    print(f"run {run_id} exit code {rc}")
