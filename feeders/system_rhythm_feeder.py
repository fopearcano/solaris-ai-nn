#!/usr/bin/env python3
"""System rhythm feeder -- write simple local machine-rhythm features.

This feeder is OUTSIDE Solaris. It writes Sensory Event Envelopes describing
harmless local machine rhythm: the current time-of-day phase, a process-uptime
proxy, a disk-free estimate, and a file count in a configured folder. It performs
no privileged operations, no process/OS control, no shell, and no network --
standard library only.

    python feeders/system_rhythm_feeder.py --out .solaris_ai_nn_live/feeds/sys.jsonl \
        --count-folder .
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
import uuid


def make_envelope(count_folder: str, source_id: str = "system_rhythm") -> dict:
    now = time.time()
    # Time-of-day phase as a [0, 1) cyclic feature (no calendar, no locale).
    seconds_in_day = now % 86400.0
    phase = seconds_in_day / 86400.0
    features = {
        "time_phase_sin": round(math.sin(2 * math.pi * phase), 4),
        "time_phase_cos": round(math.cos(2 * math.pi * phase), 4),
        "uptime_proxy_s": round(time.monotonic(), 2),
    }
    try:
        usage = os.statvfs(count_folder if os.path.isdir(count_folder) else ".")
        features["disk_free_ratio"] = round(
            usage.f_bavail / max(1, usage.f_blocks), 4)
    except (OSError, AttributeError):
        pass
    if os.path.isdir(count_folder):
        try:
            features["file_count"] = float(len(os.listdir(count_folder)))
        except OSError:
            pass
    return {
        "event_id": f"LFE_{uuid.uuid4().hex[:10]}",
        "source_id": source_id,
        "feeder_id": "system_rhythm_feeder",
        "feeder_mode": "local_system_rhythm",
        "modality": "machine_rhythm",
        "timestamp": now,
        "features": features,
        "provenance": {"source_id": source_id,
                       "feeder_id": "system_rhythm_feeder",
                       "feeder_mode": "local_system_rhythm"},
        "read_only": True,
        "source_mutable_by_solaris": False,
        "trust_level": "trusted_local_script",
        "contamination_flags": [],
        "safety_flags": ["no_privileged_operations"],
        "metadata": {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="System rhythm feeder")
    parser.add_argument("--out", required=True, help="output JSONL path")
    parser.add_argument("--count-folder", default=".")
    parser.add_argument("--source-id", default="system_rhythm")
    args = parser.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    envelope = make_envelope(args.count_folder, args.source_id)
    with open(args.out, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(envelope) + "\n")
    print(f"appended system rhythm envelope to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
