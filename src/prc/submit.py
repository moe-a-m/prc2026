"""Submission file builder and checker (CLAUDE.md §12). Never uploads.

  python -m prc.submit build <pred_rank.parquet>   -> submissions/motivated-engine_v<N>.parquet (+ .check.md)
  python -m prc.submit final <pred_rank.parquet>   -> submissions/motivated-engine_final.parquet (single final-phase
                                                      file, name from the organizer, forum 2026-10-08 17:03)
  python -m prc.submit public <pred_rank.parquet>  -> submissions/motivated-engine_v<N>.parquet on the public-phase
                                                      template (the board stays open until the deadline): the final
                                                      predictions of the 344,841 public-phase departures, as an
                                                      end-to-end check of the final pipeline
  python -m prc.submit check [<file>]              -> validate a submission against the template
"""
import re
import sys

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from prc import manifest
from prc.paths import RAW_SUBMITTING, RAW_SUBMITTING_PUBLIC, ROOT, SUBMISSIONS

TEAM = "motivated-engine"           # organizer acceptance e-mail (docs/SUBMISSIONS.md)
CLIP = (0, 2 * 86400)               # seconds; lower: taxi-out cannot be negative in the submission;
                                    # upper: 2 days, above the largest 2025 label (131,167 s)
SUBMISSIONS_LOG = ROOT / "docs" / "SUBMISSIONS.md"


def next_version() -> int:
    used = [int(v) for v in re.findall(rf"{TEAM}_v(\d+)\.parquet", SUBMISSIONS_LOG.read_text())]
    return max(used, default=0) + 1


def template(tpl_path=RAW_SUBMITTING) -> pd.DataFrame:
    import csv
    with open(manifest.RAW_MANIFEST) as f:
        want = {r["file"]: r["sha256"] for r in csv.DictReader(f)}
    rel = str(tpl_path.relative_to(ROOT))
    if manifest.sha256(tpl_path) != want[rel]:
        raise SystemExit(f"{rel} does not match its manifest checksum")
    return pd.read_parquet(tpl_path)


def check(path, tpl_path=RAW_SUBMITTING) -> list[str]:
    tpl = template(tpl_path)
    sub = pd.read_parquet(path)
    problems = []
    if list(sub.columns) != list(tpl.columns):
        problems.append(f"columns {list(sub.columns)} != {list(tpl.columns)}")
    tsch, ssch = pq.read_schema(tpl_path), pq.read_schema(path)
    for name in tpl.columns:
        if name in ssch.names and ssch.field(name).type != tsch.field(name).type:
            problems.append(f"dtype {name}: {ssch.field(name).type} != {tsch.field(name).type}")
    if len(sub) != len(tpl):
        problems.append(f"rows {len(sub)} != {len(tpl)}")
    if sub.MVT_ID_mvt.duplicated().any():
        problems.append("duplicate MVT_ID_mvt")
    if set(sub.MVT_ID_mvt) != set(tpl.MVT_ID_mvt):
        problems.append("MVT_ID_mvt set differs from template")
    v = sub.TAXITIME_SEC_mvt.to_numpy(float)
    if np.isnan(v).any() or np.isinf(v).any():
        problems.append("null/inf predictions")
    if (v < 0).any():
        problems.append("negative predictions")
    if not re.fullmatch(rf"{TEAM}_(v\d+|final)\.parquet", path.name):
        problems.append(f"file name {path.name} does not match {TEAM}_v<N>.parquet or {TEAM}_final.parquet")
    return problems


def build(pred_path, version: int | str | None = None, tpl_path=RAW_SUBMITTING):
    tpl = template(tpl_path)
    pred = pd.read_parquet(pred_path)
    m = tpl[["MVT_ID_mvt"]].merge(pred.rename(columns={"mvt_id": "key"}).assign(
        MVT_ID_mvt=lambda d: d.key.astype(tpl.MVT_ID_mvt.dtype)), on="MVT_ID_mvt", how="left")
    if m.pred.isna().any():
        raise SystemExit(f"{int(m.pred.isna().sum())} template IDs have no prediction")
    raw = m.pred.to_numpy(float)
    clipped = np.clip(raw, *CLIP)
    n_lo, n_hi = int((raw < CLIP[0]).sum()), int((raw > CLIP[1]).sum())
    out = tpl.copy()
    out["TAXITIME_SEC_mvt"] = np.rint(clipped).astype("int32")
    version = version or next_version()
    SUBMISSIONS.mkdir(exist_ok=True)
    path = SUBMISSIONS / (f"{TEAM}_final.parquet" if version == "final" else f"{TEAM}_v{version}.parquet")
    # write with the template's exact Arrow schema (MVT_ID double, TAXITIME int32)
    pq.write_table(pa.Table.from_pandas(out, schema=pq.read_schema(tpl_path), preserve_index=False), path)
    problems = check(path, tpl_path)
    rep = [f"# {path.name}", "", f"- predictions: {pred_path}", f"- template: {tpl_path.relative_to(ROOT)}",
           f"- rows: {len(out)}",
           f"- clipped to {CLIP}: {n_lo} below, {n_hi} above", f"- rounded to integer seconds (template dtype)",
           f"- mean {clipped.mean():.1f}, median {np.median(clipped):.1f}, max {clipped.max():.0f}",
           f"- check: {'OK' if not problems else problems}"]
    path.with_suffix(".check.md").write_text("\n".join(rep) + "\n")
    print("\n".join(rep))
    return path, problems


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "build":
        build(sys.argv[2])
    elif cmd == "final":
        build(sys.argv[2], version="final")
    elif cmd == "public":
        build(sys.argv[2], tpl_path=RAW_SUBMITTING_PUBLIC)
    else:
        files = [p for p in [*(map(lambda a: ROOT / a, sys.argv[2:]))]] or sorted(SUBMISSIONS.glob(f"{TEAM}_final.parquet"))
        # default: the final-phase file only; v1–v11 were built for the public-phase template (344,841 rows)
        bad = 0
        for f in files:
            pr = check(f)
            print(f"{f.name}: {'OK' if not pr else pr}")
            bad += bool(pr)
        sys.exit(1 if bad else 0)
