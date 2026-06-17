#!/usr/bin/env python3
"""project_artifact external feeder (tester utility -- NOT Solaris runtime).

Writes safe project-artifact presence/change events for a selected directory: file
existence, file count, newest modified timestamp, and total size -- never file content.
This is an external tester utility: it does not import Solaris, never reads secrets,
never runs Git/GitHub, never scans the whole repository, and never ingests source code.

    python tools/external_feeders/project_artifact_feeder.py \\
        --out .solaris_ai_nn_live/inbox/project_artifact_field.jsonl \\
        --dir docs
"""

from __future__ import annotations

import argparse
import json
import os
import time


def _summarize(directory, max_files):
    count = 0
    newest = 0.0
    total_size = 0
    if os.path.isdir(directory):
        # Only the selected directory (no full-repo scan, no recursion by default).
        for name in sorted(os.listdir(directory))[:max_files]:
            path = os.path.join(directory, name)
            if os.path.isfile(path):
                count += 1
                stat = os.stat(path)
                total_size += stat.st_size
                newest = max(newest, stat.st_mtime)
    return {"artifact_dir": directory, "file_count": count,
            "total_size_bytes": total_size,
            "newest_mtime_utc": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(newest)) if newest else ""}


def build_events(args):
    payload = _summarize(args.dir, args.max_files)
    return [{
        "event_id": "project_artifact_field",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_id": "project_artifact_field", "modality": "field",
        "channel": "project/artifact", "read_only": True, "is_command": False,
        "human_label_is_ground_truth": False, "payload": payload,
        "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": False,
                    "is_noisy": False},
        "safety": {"private_data": False, "contains_instruction": False,
                   "contains_secret": False, "allow_learning": False},
        "debug_gloss": "DEBUG ONLY (not ground truth): artifact presence/count "
                       "only; no file content",
        "debug_gloss_is_ground_truth": False,
    }]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="output JSONL path")
    ap.add_argument("--dir", default="docs",
                    help="selected project directory to summarize (no content)")
    ap.add_argument("--max-files", type=int, default=200, dest="max_files")
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
    print(f"wrote {len(events)} project_artifact event(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
