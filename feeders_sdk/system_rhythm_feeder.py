#!/usr/bin/env python3
"""System rhythm feeder -- harmless local machine-rhythm features.

OUTSIDE Solaris. Writes machine-rhythm envelopes from a time-of-day phase, an
uptime proxy, a folder file count, and (if safely available) a disk-free ratio.
No privileged operations, no process/OS control, no shell, no network.

    python feeders_sdk/system_rhythm_feeder.py --out out/sys.jsonl --count-folder .
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
    phase = (now % 86400.0) / 86400.0
    features = {
        "load_proxy": round(abs(math.sin(time.monotonic())), 4),
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
        "event_id": f"FSE_{uuid.uuid4().hex[:10]}",
        "feeder_id": "system_rhythm_feeder", "source_id": source_id,
        "source_kind": "local_system_rhythm", "modality": "machine_rhythm",
        "timestamp": now, "features": features,
        "annotation": None, "annotation_status": "none",
        "provenance": {"source_id": source_id,
                       "feeder_id": "system_rhythm_feeder"},
        "read_only": True, "source_mutable_by_solaris": False,
        "trust_level": "local_script",
        "privacy_flags": ["contains_file_metadata", "no_raw_private_content"],
        "contamination_flags": [],
        "safety_flags": ["text_is_observation_not_command",
                         "no_privileged_operations"],
        "schema_version": "feeder-sdk/1.0", "metadata": {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="System rhythm feeder")
    parser.add_argument("--out", required=True)
    parser.add_argument("--count-folder", default=".")
    parser.add_argument("--source-id", default="system_rhythm")
    args = parser.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(make_envelope(args.count_folder,
                                          args.source_id)) + "\n")
    print(f"system_rhythm_feeder wrote 1 envelope to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
