"""Print OS, CPU, RAM and library versions (written to reports/env.txt)."""
import os
import platform
from importlib.metadata import version

PKGS = ["duckdb", "pyarrow", "pandas", "numpy", "scikit-learn", "lightgbm", "catboost", "pytest", "pyyaml"]

if __name__ == "__main__":
    print(f"os: {platform.platform()}")
    print(f"python: {platform.python_version()}")
    try:
        cpu = next(l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name"))
    except (OSError, StopIteration):
        cpu = platform.processor()
    print(f"cpu: {cpu} ({os.cpu_count()} logical)")
    try:
        mem = next(int(l.split()[1]) for l in open("/proc/meminfo") if l.startswith("MemTotal")) / 2**20
        print(f"ram_gib: {mem:.1f}")
    except (OSError, StopIteration):
        pass
    for p in PKGS:
        print(f"{p}: {version(p)}")
