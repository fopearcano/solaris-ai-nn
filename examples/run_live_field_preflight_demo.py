#!/usr/bin/env python3
"""Live field preflight demo: feeder registry + source validation, no live run.

    python examples/run_live_field_preflight_demo.py --state-dir .solaris_ai_nn_live/test_preflight

Registers a couple of fixture-style feeders, runs the live-field preflight (which
validates feeders/sources but starts nothing), and shows that live mode is blocked
without governance while a fixture fallback remains available. Solaris reads only.
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
    LiveFieldRuntime,
)


def _write_feeder(path, modality, n=6):
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(n):
            fh.write(json.dumps({"modality": modality, "v": 0.6,
                                 "ts": float(i)}) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Live field preflight demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/test_preflight")
    args = parser.parse_args()
    base = args.state_dir
    os.makedirs(base, exist_ok=True)

    registry = LiveFeederRegistry(live_root=base)
    rf = os.path.join(base, "rf_out.jsonl")
    _write_feeder(rf, "alien_rf")
    registry.register(LiveFeederDescriptor(
        feeder_id="rf_feed", source_id="rf", modality="alien_rf",
        mode=LiveFeederMode.EXTERNAL_FEATURE_DROP, output_path=rf))
    registry.register(LiveFeederDescriptor(
        feeder_id="echo_feed", source_id="echo", modality="alien_echo",
        mode=LiveFeederMode.LOCAL_FILE,
        output_path=os.path.join(base, "echo_missing.jsonl")))  # missing
    registry.save()

    runtime = LiveFieldRuntime(state_dir=base, live_root=base, registry=registry)
    preflight = runtime.preflight()

    print("=== Live field preflight demo ===")
    print(f"feeders registered    : {preflight['feeder_count']}")
    print(f"present feeders        : {preflight['present']}")
    print(f"missing feeders        : {preflight['missing']}")
    print(f"live mode allowed      : {preflight['live_mode_allowed']}")
    print(f"fixture fallback       : {preflight['fixture_fallback_available']}")
    blocked = runtime.run(live=True)
    print(f"live run without gov   : refused={blocked.get('refused')} "
          f"({blocked.get('reasons')})")
    print("note                   : preflight starts nothing; live mode needs "
          "governance; Solaris reads only.")


if __name__ == "__main__":
    main()
