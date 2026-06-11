#!/usr/bin/env python3
"""Memory layer demo: hot -> warm -> cold -> fossil, evidence preserved.

    python examples/run_memory_layer_demo.py

Raw events flood hot memory; the consolidation policy compresses routine
events into warm summaries, preserves important ones at higher
resolution, fossilizes identity/safety events, and the compression report
shows that nothing was silently destroyed.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental import (
    ConsolidationPolicy,
    MemoryLayerManager,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Memory layer demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/memory_layers")
    args = parser.parse_args()

    manager = MemoryLayerManager(state_dir=args.state_dir)
    print("=" * 70)
    print("Solaris-AI-NN -- memory layer demo (raw events never grow "
          "forever)")
    print("=" * 70)

    # Events that matter happen early, then routine traffic ages them
    # out of the recent window -- which is when preservation matters.
    manager.add_hot({"warning": "boundary violation blocked",
                     "boundary": "pilot_input"},
                    kind="boundary_violation", importance=1.0)
    manager.add_hot({"identity": "restart gap recovered",
                     "continuity": 0.96},
                    kind="identity_continuity", importance=1.0)
    manager.add_hot({"mysterium": "pressure spike after prediction miss",
                     "pressure": 0.8},
                    kind="mysterium_spike", importance=0.8)
    for i in range(150):
        manager.add_hot({"step": i, "stimulus": f"p{i % 3}"},
                        kind="routine_event")
    before = manager.state()
    print(f"after intake:  hot={before.hot_count} "
          f"warm={before.warm_count} cold={before.cold_count} "
          f"fossil={before.fossil_count} "
          f"(raw events seen: {before.raw_events_seen})")

    policy = ConsolidationPolicy(hot_keep_recent=25)
    report = policy.apply(manager)
    after = manager.state()
    print(f"after policy:  hot={after.hot_count} warm={after.warm_count} "
          f"cold={after.cold_count} fossil={after.fossil_count}")
    print()
    print("compression report:")
    print(f"  input events:        {report.input_count}")
    print(f"  kept hot:            {report.kept_hot}")
    print(f"  compressed to warm:  {report.to_warm}")
    print(f"  preserved important: {report.to_cold} "
          f"({', '.join(report.preserved_important[:4])})")
    print(f"  fossilized:          {report.to_fossil}")
    print(f"  compression ratio:   {report.compression_ratio}")
    print(f"  evidence summary:    {report.evidence_summary[:80]}")
    print()
    print("movement audit (every transfer on the record):")
    for movement in manager.movement_log[-4:]:
        print(f"  {movement['from']:>6} -> {movement['to']:<7} "
              f"x{movement['count']:<4} "
              f"{movement['evidence_summary'][:60]}")
    print()
    print(f"fossil archive: {manager.fossil_path} (append-only)")
    print("note: compression preserves evidence summaries; deletion "
          "never silently destroys evidence, and fossils keep "
          "transformation milestones indefinitely.")


if __name__ == "__main__":
    main()
