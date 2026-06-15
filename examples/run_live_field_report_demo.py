#!/usr/bin/env python3
"""Live field report demo: report-only mode with corrupt/missing sources.

    python examples/run_live_field_report_demo.py --state-dir .solaris_ai_nn_live/test_report

Registers a present feeder, a missing feeder, and a corrupt feeder file, runs a
bounded read-only ingestion, and writes the live field report -- showing that
corrupt and missing sources are recorded, not hidden. No hardware is controlled.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_field import (
    LiveFeederDescriptor,
    LiveFeederMode,
    LiveFeederRegistry,
    LiveFieldReportBuilder,
    LiveFieldRuntime,
)


def main():
    parser = argparse.ArgumentParser(description="Live field report demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/test_report")
    args = parser.parse_args()
    base = args.state_dir
    os.makedirs(base, exist_ok=True)

    registry = LiveFeederRegistry(live_root=base)
    good = os.path.join(base, "rf_out.jsonl")
    with open(good, "w", encoding="utf-8") as fh:
        for i in range(6):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.7,
                                 "ts": float(i)}) + "\n")
    corrupt = os.path.join(base, "echo_out.jsonl")
    with open(corrupt, "w", encoding="utf-8") as fh:
        fh.write('{"modality":"alien_echo","boundary":1.0,"ts":0}\n')
        fh.write("{not valid json\n")  # a corrupt line
    registry.register(LiveFeederDescriptor(
        feeder_id="rf_feed", source_id="rf", modality="alien_rf",
        mode=LiveFeederMode.LOCAL_FILE, output_path=good))
    registry.register(LiveFeederDescriptor(
        feeder_id="echo_feed", source_id="echo", modality="alien_echo",
        mode=LiveFeederMode.LOCAL_FILE, output_path=corrupt))
    registry.register(LiveFeederDescriptor(
        feeder_id="vib_feed", source_id="vib", modality="alien_vibration",
        mode=LiveFeederMode.LOCAL_FILE,
        output_path=os.path.join(base, "vib_missing.jsonl")))  # missing
    registry.save()

    runtime = LiveFieldRuntime(state_dir=base, live_root=base, registry=registry)
    runtime.run(live=False)
    out = LiveFieldReportBuilder(runtime).build()
    paths = LiveFieldReportBuilder(runtime).write()

    print("=== Live field report demo ===")
    corrupt_missing = out["sections"]["corrupt_or_missing_sources"]
    print(f"corrupt sources       : {corrupt_missing['corrupt']}")
    print(f"missing feeders       : {corrupt_missing['missing_feeders']}")
    print(f"claim-guard safe      : {out['claim_guard_safe']}")
    print(f"report                : {paths['markdown']}")
    print("note                  : corrupt/missing sources are recorded, never "
          "hidden; no hardware controlled; no source modified.")


if __name__ == "__main__":
    main()
