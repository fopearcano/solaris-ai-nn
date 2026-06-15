#!/usr/bin/env python3
"""Live field fixture-fallback demo: run the live runtime on fixture feeders.

    python examples/run_live_field_fixture_fallback_demo.py --state-dir .solaris_ai_nn_live/test_fixture_fallback

Builds fixture-style feeder files (no real hardware), runs the bounded live-field
runtime in read-only mode (no governance needed for fixtures), shows source
health, and writes the live field report.
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
    parser = argparse.ArgumentParser(description="Live field fixture fallback")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/test_fixture_fallback")
    args = parser.parse_args()
    base = args.state_dir
    os.makedirs(base, exist_ok=True)

    registry = LiveFeederRegistry(live_root=base)
    for mod, hint in (("rf", "alien_rf"), ("vib", "alien_vibration"),
                      ("text", "human_textual")):
        path = os.path.join(base, f"{mod}_out.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for i in range(8):
                fh.write(json.dumps({"modality": hint, "v": 0.6 + 0.1 * (i % 2),
                                     "ts": float(i)}) + "\n")
        registry.register(LiveFeederDescriptor(
            feeder_id=f"{mod}_feed", source_id=mod, modality=hint,
            mode=LiveFeederMode.FIXTURE_REPLAY, output_path=path))
    registry.save()

    runtime = LiveFieldRuntime(state_dir=base, live_root=base, registry=registry,
                               max_ticks=40)
    result = runtime.run(live=False)
    status = runtime.live_field_status()
    out = LiveFieldReportBuilder(runtime).write()

    print("=== Live field fixture fallback demo ===")
    print(f"ticks run             : {result['ticks_run']}")
    print(f"events ingested       : {result['events_ingested']}")
    print(f"active modalities     : {status['active_modality_count']}")
    print(f"active sources        : {status['active_source_count']}")
    print(f"silent sources        : {status['silent_source_count']}")
    print(f"baseline shifts       : {status['live_baseline_shift_count']}")
    print(f"cross-modal relations : {status['cross_modal_relation_count']}")
    print(f"report                : {out['markdown']}")
    print("note                  : Solaris read fixture feeders only; no "
          "hardware, no source modification, no actuation.")


if __name__ == "__main__":
    main()
