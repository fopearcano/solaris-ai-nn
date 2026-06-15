#!/usr/bin/env python3
"""Manual log feeder -- operator environmental text -> envelopes (observation).

OUTSIDE Solaris. Appends operator-provided environmental lines (from --text or an
input file) as human-textual Sensory Event Envelopes. The text is a sensory
*stimulus*, never a command, never ground truth. Stdlib only: no network, no
shell, no hardware.

    python feeders_sdk/manual_log_feeder.py --out out/manual.jsonl --text "rain started"
"""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid


def make_envelope(text: str, source_id: str = "manual_log") -> dict:
    return {
        "event_id": f"FSE_{uuid.uuid4().hex[:10]}",
        "feeder_id": "manual_log_feeder", "source_id": source_id,
        "source_kind": "manual_log", "modality": "human_textual",
        "timestamp": time.time(),
        "features": {"length": float(len(text)),
                     "token_count": float(len(text.split()))},
        "annotation": text, "annotation_status": "human_label_external",
        "provenance": {"source_id": source_id, "feeder_id": "manual_log_feeder"},
        "read_only": True, "source_mutable_by_solaris": False,
        "trust_level": "local_manual",
        "privacy_flags": ["contains_human_text", "no_raw_private_content"],
        "contamination_flags": ["human_label_present"],
        "safety_flags": ["text_is_observation_not_command"],
        "schema_version": "feeder-sdk/1.0", "metadata": {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual log feeder")
    parser.add_argument("--out", required=True)
    parser.add_argument("--text", default=None)
    parser.add_argument("--input-file", default=None)
    parser.add_argument("--source-id", default="manual_log")
    args = parser.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    lines = []
    if args.text:
        lines.append(args.text)
    if args.input_file and os.path.isfile(args.input_file):
        with open(args.input_file, "r", encoding="utf-8", errors="replace") as fh:
            lines.extend(ln.rstrip("\n") for ln in fh if ln.strip())
    if not lines:
        lines = ["(no observation provided)"]
    with open(args.out, "a", encoding="utf-8") as fh:
        for text in lines:
            fh.write(json.dumps(make_envelope(text, args.source_id)) + "\n")
    print(f"manual_log_feeder wrote {len(lines)} envelope(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
