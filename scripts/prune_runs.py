#!/usr/bin/env python3
"""
Reclaim disk from data/runs/.

A reproduction keeps three kinds of artifact per project:

  * the results -- logs, outputs, the evidence ledger and its snapshots, the report.
    Tiny (a few MB across every project) and not reproducible after the fact, so never
    touched here.
  * the workspace -- the checked-out repository, plus `.site`, the packages installed
    into it. `.site` is a byproduct of the offline install.
  * the wheelhouse -- wheels downloaded for that project. A torch-based project carries
    around 3 GB of them.

The last two are regenerable by re-running provisioning, and together they were 90% of a
33 GB data/runs. This prunes them for finished projects and removes run directories whose
project row no longer exists, while leaving anything still in flight alone.

Prints what it would remove; pass --apply to actually remove it.
"""

import argparse
import json
import shutil
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# Regenerable by re-provisioning; safe to drop once a project has finished.
REGENERABLE = ("wheelhouse", "workspace/.site", "pip_tmp")


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def project_phases(db_path: Path) -> dict:
    """project id -> phase, read straight from the JSON so one bad row cannot break the scan."""
    phases = {}
    if not db_path.exists():
        return phases
    conn = sqlite3.connect(db_path)
    try:
        for pid, state_json in conn.execute("SELECT id, state_json FROM projects"):
            phase = None
            if state_json:
                try:
                    phase = json.loads(state_json).get("phase")
                except Exception:
                    phase = None
            phases[pid] = phase
    finally:
        conn.close()
    return phases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true",
                        help="actually delete (default: report only)")
    parser.add_argument("--runs-root", default=str(REPO_ROOT / "data" / "runs"))
    parser.add_argument("--db", default=str(REPO_ROOT / "data" / "rerun.db"))
    args = parser.parse_args()

    runs_root = Path(args.runs_root)
    if not runs_root.is_dir():
        print(f"no runs directory at {runs_root}")
        return 0

    phases = project_phases(Path(args.db))
    orphans, regenerable, kept = [], [], 0

    for entry in sorted(runs_root.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name not in phases:
            orphans.append(entry)
            continue
        if phases[entry.name] != "DONE":
            kept += 1  # still in flight or parked at a human gate: leave it entirely alone
            continue
        for rel in REGENERABLE:
            target = entry.joinpath(*rel.split("/"))
            if target.exists():
                regenerable.append(target)

    orphan_bytes = sum(dir_size(p) for p in orphans)
    regen_bytes = sum(dir_size(p) for p in regenerable)

    print(f"runs root            : {runs_root}")
    print(f"unfinished, untouched: {kept} projects")
    print(f"orphaned run dirs    : {len(orphans)} ({orphan_bytes / 1e9:.1f} GB)")
    print(f"regenerable artifacts: {len(regenerable)} ({regen_bytes / 1e9:.1f} GB)")
    print(f"reclaimable total    : {(orphan_bytes + regen_bytes) / 1e9:.1f} GB")

    if not args.apply:
        print("\nreport only; re-run with --apply to delete")
        return 0

    for path in orphans + regenerable:
        shutil.rmtree(path, ignore_errors=True)
    print(f"\ndeleted {len(orphans) + len(regenerable)} paths")
    return 0


if __name__ == "__main__":
    sys.exit(main())
