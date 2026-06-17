#!/usr/bin/env python3
"""local_weather manual writer (optional tester utility -- NOT Solaris runtime).

The tester manually enters read-only local weather scalars (temperature, etc.) as a
JSONL event. This is an external tester utility: it does not import Solaris, makes **no**
network calls, and the weather value is a manual annotation only.

    python tools/external_feeders/local_weather_manual_writer.py \\
        --out .solaris_ai_nn_live/inbox/local_weather_readonly_external.jsonl \\
        --temp-c 12.0 --note "manual reading"
"""

from __future__ import annotations

import argparse
import json
import time


def build_events(args):
    payload = {}
    if args.temp_c is not None:
        payload["temp_c"] = float(args.temp_c)
    gloss = ""
    if args.note:
        gloss = f"DEBUG ONLY (not ground truth): manual weather: {args.note}"
    return [{
        "event_id": "local_weather_readonly_external",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_id": "local_weather_readonly_external", "modality": "scalar",
        "channel": "weather/manual", "read_only": True, "is_command": False,
        "human_label_is_ground_truth": False,
        "payload": payload or {"note": "no values supplied"},
        "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": False,
                    "is_noisy": False},
        "safety": {"private_data": False, "contains_instruction": False,
                   "contains_secret": False, "allow_learning": False},
        "debug_gloss": gloss, "debug_gloss_is_ground_truth": False,
    }]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="output JSONL path")
    ap.add_argument("--temp-c", type=float, default=None, dest="temp_c")
    ap.add_argument("--note", default="", help="manual weather note")
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
    print(f"wrote {len(events)} weather event(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
