"""Hard spending guard for Modal runs (user condition 2026-10-05: total Modal spend must never exceed $500).

Committed = billed usage since START_MONTH (`modal billing summary --json`, gross `metered_cost`, i.e. before credits)
          + worst-case cost of every job launched in the last PENDING_DAYS (counted again even if already billed:
            billing lags, double counting only makes the guard stricter)
A launch is refused when committed + the new job's worst case > CAP_USD, or when billing cannot be read.
Worst case = timeout × (physical cores × CPU rate + GiB × memory rate) + LAUNCH_OVERHEAD_USD (image build, storage).
Rates from https://modal.com/pricing (read 2026-10-05): CPU $0.0000131 / physical core / s, memory
$0.00000222 / GiB / s (standard functions).

  python scripts/modal/budget.py status
"""
import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "logs" / "modal" / "ledger.csv"
HARD_LIMIT_USD = 500.0   # the user's limit — never to be reached
CAP_USD = 400.0          # internal cap: $100 margin below the hard limit for billing lag and estimate error
CPU_RATE = 0.0000131     # $ / physical core / s
MEM_RATE = 0.00000222    # $ / GiB / s
LAUNCH_OVERHEAD_USD = 1.0
PENDING_DAYS = 3
START_MONTH = (2026, 10)
FIELDS = ["run_id", "launched_at", "cpu", "memory_gib", "timeout_s", "worst_case_usd", "cmd"]


def _modal(*args) -> str:
    env = {**os.environ, "PYENV_VERSION": os.environ.get("PYENV_VERSION", "3.13.15")}
    r = subprocess.run(["modal", *args], capture_output=True, text=True, env=env, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"modal {' '.join(args)} failed: {r.stderr.strip()[:300]}")
    return r.stdout


def billed_usd(now: datetime | None = None) -> float:
    """Gross metered usage summed over every month since START_MONTH (raises if billing cannot be read)."""
    now = now or datetime.now(timezone.utc)
    y, m = START_MONTH
    total = 0.0
    while (y, m) <= (now.year, now.month):
        js = json.loads(_modal("billing", "summary", "--for", f"{y:04d}-{m:02d}", "--json"))
        total += float(js["metered_cost"])
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return total


def worst_case_usd(cpu: float, memory_gib: float, timeout_s: int) -> float:
    return timeout_s * (cpu * CPU_RATE + memory_gib * MEM_RATE) + LAUNCH_OVERHEAD_USD


def _ledger() -> list[dict]:
    if not LEDGER.exists():
        return []
    with open(LEDGER) as f:
        return list(csv.DictReader(f))


def pending_usd(now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    cut = now - timedelta(days=PENDING_DAYS)
    return sum(float(r["worst_case_usd"]) for r in _ledger() if datetime.fromisoformat(r["launched_at"]) >= cut)


def committed_usd() -> tuple[float, float]:
    return billed_usd(), pending_usd()


def authorize(run_id: str, cpu: float, memory_gib: float, timeout_s: int, cmd: str) -> float:
    """Record the launch in the ledger if it fits under CAP_USD; raise SystemExit otherwise."""
    assert CAP_USD < HARD_LIMIT_USD
    wc = worst_case_usd(cpu, memory_gib, timeout_s)
    try:
        billed, pending = committed_usd()
    except Exception as e:  # cannot verify spending → never launch
        raise SystemExit(f"BUDGET GUARD: billing unreadable ({e}); launch refused")
    total = billed + pending + wc
    if total > CAP_USD:
        raise SystemExit(f"BUDGET GUARD: billed ${billed:.2f} + pending ${pending:.2f} + this job ${wc:.2f} = "
                         f"${total:.2f} > cap ${CAP_USD:.0f} (hard limit ${HARD_LIMIT_USD:.0f}); launch refused")
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    new = not LEDGER.exists()
    with open(LEDGER, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({"run_id": run_id, "launched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "cpu": cpu, "memory_gib": memory_gib, "timeout_s": timeout_s, "worst_case_usd": round(wc, 4),
                    "cmd": cmd})
    print(f"budget ok: billed ${billed:.2f} + pending ${pending:.2f} + this job ≤ ${wc:.2f} = ${total:.2f} "
          f"≤ cap ${CAP_USD:.0f}")
    return wc


if __name__ == "__main__":
    if sys.argv[1:] != ["status"]:
        raise SystemExit(__doc__)
    billed, pending = committed_usd()
    print(f"billed since {START_MONTH[0]}-{START_MONTH[1]:02d}: ${billed:.2f}; pending worst case (last "
          f"{PENDING_DAYS} d): ${pending:.2f}; committed ${billed + pending:.2f}; cap ${CAP_USD:.0f}; "
          f"hard limit ${HARD_LIMIT_USD:.0f}")
