#!/usr/bin/env python3
"""machine_body external feeder (tester utility -- NOT Solaris runtime).

Writes simple, safe machine scalar state (cpu/memory/disk percent) as a read-only JSONL
event. This is an external tester utility: it does not import Solaris and is run
manually. It uses psutil only if it is already installed (optional); otherwise it falls
back to a minimal disk-free reading for the current project path. It never lists
process command lines or usernames, never scans the whole filesystem, and never
controls hardware/GPU/fans or runs a shell.

    python tools/external_feeders/machine_body_feeder.py \\
        --out .solaris_ai_nn_live/inbox/machine_body.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import time


def _safe_scalars():
    """Collect only safe, non-private machine scalars."""
    scalars = {}
    try:
        import psutil  # optional; only used if already installed
        scalars["cpu_percent"] = round(float(psutil.cpu_percent(interval=0.0)),
                                        1)
        scalars["memory_percent"] = round(
            float(psutil.virtual_memory().percent), 1)
    except Exception:
        # Fallback: disk free percent for the current project path only.
        pass
    try:
        usage = shutil.disk_usage(os.getcwd())
        scalars["disk_free_percent"] = round(
            100.0 * usage.free / usage.total, 1)
    except Exception:
        scalars.setdefault("disk_free_percent", 0.0)
    return scalars


def build_events(args):
    scalars = {} if args.no_collect else _safe_scalars()
    return [{
        "event_id": "machine_body_scalar",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_id": "machine_body", "modality": "scalar",
        "channel": "machine_body/scalar", "read_only": True,
        "is_command": False, "human_label_is_ground_truth": False,
        "payload": scalars or {"load": 0.0},
        "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": False,
                    "is_noisy": False},
        "safety": {"private_data": False, "contains_instruction": False,
                   "contains_secret": False, "allow_learning": False},
        "debug_gloss": "DEBUG ONLY (not ground truth): safe machine scalars",
        "debug_gloss_is_ground_truth": False,
    }]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="output JSONL path")
    ap.add_argument("--no-collect", action="store_true",
                    help="emit a placeholder scalar instead of reading the host")
    ap.add_argument("--dry-run", action="store_true",
                    help="print events; do not write")
    args = ap.parse_args()

    events = build_events(args)
    if args.dry_run:
        for ev in events:
            print(json.dumps(ev))
        return 0
    with open(args.out, "a", encoding="utf-8") as fh:
        for ev in events:
            fh.write(json.dumps(ev))
            fh.write("\n")
    print(f"wrote {len(events)} machine_body event(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
