#!/usr/bin/env python3
"""Manual log feeder -- append environmental text observations as envelopes.

This feeder is OUTSIDE Solaris. An operator runs it to append a line of
environmental text (e.g. "rain started", "fan switched off") as a Sensory Event
Envelope to a local JSONL file. Solaris later reads that file read-only.

The human text is an *environmental stimulus*, never a command. This script uses
the standard library only: no network, no shell, no source control, and it writes
only to its own output file.

    python feeders/manual_log_feeder.py --out .solaris_ai_nn_live/feeds/manual_log.jsonl \
        --text "ambient hum increased"
"""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid


def make_envelope(text: str, source_id: str = "manual_log") -> dict:
    return {
        "event_id": f"LFE_{uuid.uuid4().hex[:10]}",
        "source_id": source_id,
        "feeder_id": "manual_log_feeder",
        "feeder_mode": "manual",
        "modality": "human_textual",
        "timestamp": time.time(),
        "features": {"length": float(len(text)),
                     "token_count": float(len(text.split()))},
        "annotation": text,
        "annotation_status": "human_label_external",
        "provenance": {"source_id": source_id,
                       "feeder_id": "manual_log_feeder", "feeder_mode": "manual"},
        "read_only": True,
        "source_mutable_by_solaris": False,
        "trust_level": "trusted_local_manual",
        "contamination_flags": ["human_label_present"],
        "safety_flags": ["text_is_observation_not_command"],
        "metadata": {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual log feeder")
    parser.add_argument("--out", required=True, help="output JSONL path")
    parser.add_argument("--text", required=True, help="environmental observation")
    parser.add_argument("--source-id", default="manual_log")
    args = parser.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    envelope = make_envelope(args.text, args.source_id)
    with open(args.out, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(envelope) + "\n")
    print(f"appended manual log envelope to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
