#!/usr/bin/env python3
"""manual_environment external writer (tester utility -- NOT Solaris runtime).

The tester manually enters scalar local-environment values (room temperature, light and
noise level estimates, an optional weather note as a non-ground-truth annotation) which
are written as read-only JSONL events. This is an external tester utility: it does not
import Solaris and never reads a raw microphone, raw camera, or private conversation
text.

    python tools/external_feeders/manual_environment_writer.py \\
        --out .solaris_ai_nn_live/inbox/local_environment_manual.jsonl \\
        --temp-c 21.5 --light 0.6 --noise 0.3 --weather-note "overcast"
"""

from __future__ import annotations

import argparse
import json
import time


def build_events(args):
    payload = {}
    if args.temp_c is not None:
        payload["temp_c"] = float(args.temp_c)
    if args.light is not None:
        payload["light_level"] = float(args.light)
    if args.noise is not None:
        payload["noise_level"] = float(args.noise)
    gloss = ""
    if args.weather_note:
        gloss = (f"DEBUG ONLY (not ground truth): weather note: "
                 f"{args.weather_note}")
    return [{
        "event_id": "local_environment_manual",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_id": "local_environment_manual", "modality": "scalar",
        "channel": "local_environment/manual", "read_only": True,
        "is_command": False, "human_label_is_ground_truth": False,
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
    ap.add_argument("--light", type=float, default=None)
    ap.add_argument("--noise", type=float, default=None)
    ap.add_argument("--weather-note", default="", dest="weather_note")
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
    print(f"wrote {len(events)} environment event(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
