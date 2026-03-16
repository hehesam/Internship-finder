"""Run local collector smoke tests.

Usage:
    python tools/test_collectors.py
"""

from __future__ import annotations

from pathlib import Path
import sys


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from internship_bot.main import build_collectors
from internship_bot.config import load_config


def run() -> None:
    config = load_config()
    collectors = build_collectors(config)

    print(f"Collectors configured: {len(collectors)}")
    if not collectors:
        print("No collectors enabled. Check .env toggles and source lists.")
        return

    for collector in collectors:
        try:
            jobs = collector.collect()
        except Exception as error:  # noqa: BLE001
            print(f"[ERROR] {collector.name}: {error}")
            continue

        print(f"[{collector.name}] jobs={len(jobs)}")
        for index, job in enumerate(jobs[:3], start=1):
            print(
                f"  {index}. {job.title} | {job.company} | {job.location or 'Unknown'} | {job.url}"
            )


if __name__ == "__main__":
    print(f"Workspace: {WORKSPACE_ROOT}")
    run()
