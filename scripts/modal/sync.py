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
    """Copy the run's outputs into the working tree. Runs record the files they wrote in changed.txt; only those are
    copied. Older runs (no changed.txt) copied whole trees, so for them only files missing locally are copied."""
    dest = ROOT / "logs" / "modal" / "runs"
    dest.mkdir(parents=True, exist_ok=True)
    _get(f"/runs/{run_id}", dest)
    run = dest / run_id
    listed = (run / "changed.txt").read_text().split() if (run / "changed.txt").exists() else None
    changed, skipped = [], []
    for sub in ("reports", "docs"):
        src = run / sub
        for f in src.rglob("*") if src.exists() else []:
            if not f.is_file():
                continue
            rel = f.relative_to(run)
            tgt = ROOT / rel
            if listed is not None and str(rel) not in listed:
                continue
            if listed is None and tgt.exists():
                if not filecmp.cmp(f, tgt, shallow=False):
                    skipped.append(str(rel))
                continue
            if not tgt.exists() or not filecmp.cmp(f, tgt, shallow=False):
                tgt.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, tgt)
                changed.append(str(rel))
    rc = (run / "exit_code").read_text().strip() if (run / "exit_code").exists() else "?"
    print(f"run {run_id}: exit code {rc}; {len(changed)} files updated"
          + ("" if listed is not None else f" (old-style run: {len(skipped)} differing existing files NOT copied)"))
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
