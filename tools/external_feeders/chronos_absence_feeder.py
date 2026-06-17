#!/usr/bin/env python3
"""chronos_absence external feeder (tester utility -- NOT Solaris runtime).

Writes a chronos tick event and, optionally, an absence/silence marker, into a JSONL
file. This is an external tester utility: it does not import Solaris, is run manually by
the tester/operator, and never schedules itself, runs a daemon, executes shell, or
automates the OS.

    python tools/external_feeders/chronos_absence_feeder.py \\
        --out .solaris_ai_nn_live/inbox/chronos_absence.jsonl
"""

from __future__ import annotations

import argparse
import json
import time


def _event(event_id, channel, payload, *, is_absence=False, gloss=""):
    return {
        "event_id": event_id,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_id": "chronos_absence", "modality": "chronos",
        "channel": channel, "read_only": True, "is_command": False,
        "human_label_is_ground_truth": False, "payload": dict(payload),
        "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": is_absence,
                    "is_noisy": False},
        "safety": {"private_data": False, "contains_instruction": False,
                   "contains_secret": False, "allow_learning": False},
        "debug_gloss": gloss, "debug_gloss_is_ground_truth": False,
    }


def build_events(args):
    events = [_event("chronos_tick", "time/tick", {"tick": int(time.time())},
                     gloss="DEBUG ONLY (not ground truth): wall-clock tick")]
    if args.absence_reason:
        events.append(_event(
            "chronos_absence", "time/absence", {"absence": True},
            is_absence=True,
            gloss=f"DEBUG ONLY (not ground truth): {args.absence_reason}"))
    return events


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="output JSONL path")
    ap.add_argument("--absence-reason", default="",
                    help="optional manual absence/silence reason")
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
    print(f"wrote {len(events)} chronos event(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
