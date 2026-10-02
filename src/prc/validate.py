"""Validation protocol (CLAUDE.md §9): month hold-outs, RMSE breakdowns, experiment reports."""
import hashlib
import subprocess
from datetime import date

import numpy as np
import pandas as pd

from prc.paths import RAW_MANIFEST, REPORTS, ROOT, SQL

HOLDOUTS = {"jan": date(2025, 1, 1), "jul": date(2025, 7, 1)}
FLAG_COLS = ["f_no_nm_match", "f_block_eq_sched", "f_block_eq_planned", "f_round_minute_block",
             "f_negative_taxi", "f_taxi_gt_3h"]


def data_version() -> str:
    """Hash of raw-file identities (path + SHA256 from the manifest) and all SQL. Bookkeeping columns of the
    manifest (bucket path, download time) do not change it."""
    import csv
    h = hashlib.sha256()
    with open(RAW_MANIFEST) as f:
        for r in sorted(csv.DictReader(f), key=lambda r: r["file"]):
            h.update(f"{r['file']}:{r['sha256']}\n".encode())
    for f in sorted(SQL.rglob("*.sql")):
        h.update(str(f.relative_to(ROOT)).encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:12]


def git_sha() -> str:
    r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    sha = r.stdout.strip() or "nocommit"
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    return sha + ("-dirty" if dirty else "")


def rmse(y, p) -> float:
    y, p = np.asarray(y, float), np.asarray(p, float)
    return float(np.sqrt(np.mean((y - p) ** 2)))


def folds(month: pd.Series):
    """Yield (name, train_mask, valid_mask) for the Jan-2025 and Jul-2025 hold-outs."""
    m = pd.to_datetime(month).dt.date
    for name, d in HOLDOUTS.items():
        yield name, (m != d).to_numpy(), (m == d).to_numpy()


def breakdown(df: pd.DataFrame, pred_col: str = "pred") -> dict:
    """RMSE overall / per airport / NM-matched vs not / flagged vs clean. df needs y, airport, flags."""
    out = {"rmse": rmse(df.y, df[pred_col]), "n": len(df)}
    out["airport"] = {a: rmse(g.y, g[pred_col]) for a, g in df.groupby("airport")}
    for c in FLAG_COLS:
        if c in df:
            m = df[c].fillna(False).astype(bool)
            out[c] = {"true": (rmse(df.y[m], df[pred_col][m]) if m.any() else None, int(m.sum())),
                      "false": (rmse(df.y[~m], df[pred_col][~m]), int((~m).sum()))}
    return out


def report_md(exp_id: str, title: str, results: dict[str, pd.DataFrame], meta: dict, pred_col="pred") -> str:
    """results: fold name -> validation frame with y, pred, airport, flags, mvt_id."""
    lines = [f"# {exp_id}: {title}", ""]
    lines += [f"- {k}: {v}" for k, v in meta.items()] + [""]
    combined = pd.concat(results.values())
    rows = []
    for name, df in list(results.items()) + [("combined", combined)]:
        b = breakdown(df, pred_col)
        m = df.y <= 3 * 3600
        sq = (df[pred_col] - df.y) ** 2
        rows.append({"fold": name, "n": b["n"], "rmse": round(b["rmse"], 2),
                     "rmse_y≤3h": round(float(np.sqrt(sq[m].mean())), 2),
                     "tail_sq_share": round(float(sq[~m].sum() / sq.sum()), 3),
                     **{a: round(v, 1) for a, v in b["airport"].items()}})
    lines += ["## RMSE overall and per airport", "", pd.DataFrame(rows).to_markdown(index=False), ""]
    flag_rows = []
    for name, df in list(results.items()) + [("combined", combined)]:
        b = breakdown(df, pred_col)
        for c in FLAG_COLS:
            if c in b:
                (rt, nt), (rf, nf) = b[c]["true"], b[c]["false"]
                flag_rows.append({"fold": name, "flag": c, "n_true": nt,
                                  "rmse_true": None if rt is None else round(rt, 1), "n_false": nf,
                                  "rmse_false": round(rf, 1)})
    lines += ["## Flagged vs clean / NM-matched vs unmatched", "",
              pd.DataFrame(flag_rows).to_markdown(index=False), ""]
    e = combined.assign(err=combined[pred_col] - combined.y, sq=(combined[pred_col] - combined.y) ** 2)
    tot = e.sq.sum()
    srt = e.sq.sort_values(ascending=False).to_numpy()
    k1 = max(1, len(srt) // 100)
    lines += [f"Share of squared error: top 1% rows = {srt[:k1].sum() / tot:.1%}; "
              f"top 20 rows = {srt[:20].sum() / tot:.1%}.", ""]
    cols = [c for c in ["mvt_id", "airport", "month", "runway", "stand", "y", pred_col, "err", "f_no_nm_match",
                        "f_block_eq_sched"] if c in e]
    lines += ["## Top-20 rows by squared error (combined)", "",
              e.nlargest(20, "sq")[cols].round({"y": 1, pred_col: 1, "err": 1}).to_markdown(index=False), ""]
    return "\n".join(lines)


def write_report(exp_id: str, text: str) -> None:
    d = REPORTS / "experiments"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{exp_id}.md").write_text(text)
