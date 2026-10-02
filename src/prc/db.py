"""DuckDB connection and SQL runner. All cleaning happens in SQL (CLAUDE.md §8)."""
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from prc.paths import CHECKS, DB, ROOT, SQL


def connect(path: Path | str = DB, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(path), read_only=read_only)
    con.execute("SET TimeZone = 'UTC'")
    con.execute(f"SET file_search_path = '{ROOT}'")
    try:
        con.execute("LOAD spatial")
    except duckdb.Error:
        pass  # only needed by sql/40_adsb; `INSTALL spatial` once (README)
    return con


def sql_files(stage: str) -> list[Path]:
    return sorted((SQL / stage).glob("*.sql"))


def _requires_ok(sql_text: str) -> bool:
    """`-- requires-glob: <pattern>` header lines: skip the file when no file matches (optional external data)."""
    for line in sql_text.splitlines():
        if line.startswith("-- requires-glob:"):
            if not list(ROOT.glob(line.split(":", 1)[1].strip())):
                return False
    return True


def run_stage(con, stage: str, verbose: bool = True, prefix: str = "") -> None:
    for f in sql_files(stage):
        if prefix and not f.name.startswith(prefix):
            continue
        if not _requires_ok(f.read_text()):
            if verbose:
                print(f"  {f.relative_to(ROOT)}  (skipped: required external files absent)")
            continue
        t0 = datetime.now()
        con.execute(f.read_text())
        if verbose:
            print(f"  {f.relative_to(ROOT)}  ({(datetime.now() - t0).total_seconds():.1f}s)")


def save_check(con, name: str, sql: str, note: str = "", max_rows: int = 500):
    """Run a verification query and save SQL + output to reports/checks/<name>.md and .csv."""
    df = con.sql(sql).df()
    CHECKS.mkdir(parents=True, exist_ok=True)
    df.to_csv(CHECKS / f"{name}.csv", index=False)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    body = [f"# Check: {name}", "", f"Run at {stamp} (UTC), duckdb {duckdb.__version__}.", ""]
    if note:
        body += [note, ""]
    body += ["```sql", sql.strip(), "```", "", f"{len(df)} rows" + (f" (first {max_rows} shown)" if len(df) > max_rows else ""), ""]
    body += [df.head(max_rows).to_markdown(index=False), ""]
    (CHECKS / f"{name}.md").write_text("\n".join(body))
    return df
