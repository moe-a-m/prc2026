"""Bring a Modal run's outputs back into the local repo (no network beyond `modal volume get`).

  python scripts/modal/sync.py <run_id> [--models EXP-041 ...]

runs/<run_id>/ → logs/modal/runs/<run_id>/ (stdout, exit code), and new or changed files under reports/ and docs/
are copied into the working tree (git shows them for review before committing). --models fetches models/<EXP>/ and
models/oof/<EXP>_*.parquet for the given experiments.
"""
import argparse
import filecmp
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOLUME = "prc2026-data"


def _get(remote: str, local: Path):
    env = {**os.environ, "PYENV_VERSION": os.environ.get("PYENV_VERSION", "3.13.15")}
    subprocess.run(["modal", "volume", "get", "--force", VOLUME, remote, str(local)], check=True, env=env)


def sync_run(run_id: str):
    dest = ROOT / "logs" / "modal" / "runs"
    dest.mkdir(parents=True, exist_ok=True)
    _get(f"/runs/{run_id}", dest)
    run = dest / run_id
    changed = []
    for sub in ("reports", "docs"):
        src = run / sub
        for f in src.rglob("*") if src.exists() else []:
            if f.is_file():
                tgt = ROOT / sub / f.relative_to(src)
                if not tgt.exists() or not filecmp.cmp(f, tgt, shallow=False):
                    tgt.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, tgt)
                    changed.append(str(tgt.relative_to(ROOT)))
    rc = (run / "exit_code").read_text().strip() if (run / "exit_code").exists() else "?"
    print(f"run {run_id}: exit code {rc}; {len(changed)} files updated")
    for c in changed:
        print("  ", c)


def sync_models(exps):
    with tempfile.TemporaryDirectory() as tmp:
        for e in exps:
            _get(f"/models/{e}", Path(tmp))
            for fold in ("jan", "jul"):
                try:
                    _get(f"/models/oof/{e}_{fold}.parquet", ROOT / "models" / "oof" / f"{e}_{fold}.parquet")
                except subprocess.CalledProcessError:
                    pass
        for d in Path(tmp).iterdir():
            if d.is_dir():
                shutil.copytree(d, ROOT / "models" / d.name, dirs_exist_ok=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    ap.add_argument("--models", nargs="*", default=[])
    a = ap.parse_args()
    sync_run(a.run_id)
    if a.models:
        sync_models(a.models)
