#!/usr/bin/env python3
"""Live field comparison demo: live-like stream vs fixture vs passive parser.

    python examples/run_live_field_comparison_demo.py --state-dir .solaris_ai_nn_live/test_comparison

Runs the live-field runtime on a live-like feeder stream and compares it against a
fixture field and a passive event-list parser, reporting the changed-perception
score for each. Negative/inconclusive results are reported honestly.
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
    LiveFieldComparison,
    LiveFieldRuntime,
)


def main():
    parser = argparse.ArgumentParser(description="Live field comparison demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/test_comparison")
    args = parser.parse_args()
    base = args.state_dir
    os.makedirs(base, exist_ok=True)

    registry = LiveFeederRegistry(live_root=base)
    for mod, hint in (("rf", "alien_rf"), ("vib", "alien_vibration")):
        path = os.path.join(base, f"{mod}_out.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for i in range(10):
                # Live-like jitter so the stream is less predictable.
                fh.write(json.dumps({"modality": hint,
                                     "v": 0.6 + 0.2 * ((i * 7) % 3) / 3.0,
                                     "ts": float(i)}) + "\n")
        registry.register(LiveFeederDescriptor(
            feeder_id=f"{mod}_feed", source_id=mod, modality=hint,
            mode=LiveFeederMode.LOCAL_FILE, output_path=path))
    registry.save()

    runtime = LiveFieldRuntime(state_dir=base, live_root=base, registry=registry,
                               max_ticks=40)
    runtime.run(live=False)
    result = LiveFieldComparison(state_dir=os.path.join(base, "cmp")).run(runtime)

    print("=== Live field comparison demo ===")
    print(f"{'arm':>16} | changed | baseline | cross_modal")
    for name, m in result.arms.items():
        print(f"{name:>16} | {m.get('changed_perception_score', 0.0):>7} | "
              f"{m.get('baseline_shift_count', 0):>8} | "
              f"{m.get('cross_modal_relation_count', 0):>11}")
    print(f"live beats passive    : {result.summary.get('live_beats_passive')}")
    print(f"inconclusive          : {result.inconclusive}")
    print(f"negative result       : {result.negative_result}")
    print("note                  : compares internal response structure; no "
          "consciousness claim; live evidence is not overstated.")


if __name__ == "__main__":
    main()
