#!/usr/bin/env python3
"""operator_pulse external writer (tester utility -- NOT Solaris runtime).

The tester writes a short note as a stimulus event. The operator note is **stimulus
only**: it is never a command, never a teaching label, and never ground truth. This is
an external tester utility: it does not import Solaris and never writes passwords,
secrets, or private data.

    python tools/external_feeders/operator_pulse_writer.py \\
        --out .solaris_ai_nn_live/inbox/operator_pulse.jsonl \\
        --note "hello, this is a stimulus"
"""

from __future__ import annotations

import argparse
import json
import time


def build_events(args):
    payload = {"pulse": 1}
    if args.note:
        # The note is stimulus text only; never a command or ground-truth label.
        payload["note"] = str(args.note)[:280]
    gloss = ""
    if args.intent:
        gloss = (f"DEBUG ONLY (not ground truth): operator intent annotation: "
                 f"{args.intent}")
    return [{
        "event_id": "operator_pulse",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_id": "operator_pulse", "modality": "pulse",
        "channel": "operator/pulse", "read_only": True, "is_command": False,
        "human_label_is_ground_truth": False, "payload": payload,
        "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": False,
                    "is_noisy": False},
        "safety": {"private_data": False, "contains_instruction": False,
                   "contains_secret": False, "allow_learning": False},
        "debug_gloss": gloss, "debug_gloss_is_ground_truth": False,
    }]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="output JSONL path")
    ap.add_argument("--note", default="", help="short operator note (stimulus)")
    ap.add_argument("--intent", default="",
                    help="optional intent annotation (never ground truth)")
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
    print(f"wrote {len(events)} operator_pulse event(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
