#!/usr/bin/env python3
"""Auto-regeneration diagnostics demo: detect degradation, mutate nothing.

    python examples/run_autoregeneration_diagnostics_demo.py

Builds a context with several mock degradation signals (memory bloat, symbol
explosion, world-model contradiction, runaway drift, Mysterium saturation)
and runs the diagnostics in ``observe_only`` mode: it detects and ranks
degradation but applies no repair. Regeneration repairs runtime state, never
source code.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.autoregeneration import (
    AutoRegenerationEngine,
    AutoRegenerationReportBuilder,
    RepairPolicy,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auto-regeneration diagnostics demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/autoreg_diagnostics")
    args = parser.parse_args()

    engine = AutoRegenerationEngine(
        state_dir=args.state_dir, policy=RepairPolicy(mode="observe_only"))
    ctx = {
        "memory": {"over_budget": ["hot"]},
        "proto_language": {"symbol_count": 800, "ambiguous_symbol_count": 50},
        "world_model": {"graph_node_count": 30, "graph_edge_count": 40,
                        "contradiction_edges": ["a|contradicts|b"],
                        "prediction_accuracy": 0.2},
        "drift": {"classification": "fast_warning", "drift_velocity": 3.0},
        "mysterium_pressure": 0.97,
        "state_dir": args.state_dir,
    }
    out = engine.tick(ctx)
    degradation = out["degradation"]

    print("=" * 70)
    print("Solaris-AI-NN -- auto-regeneration diagnostics (detect, not "
          "mutate)")
    print("=" * 70)
    print(f"repair policy mode:   {engine.policy.mode}")
    print(f"degradation signals:  {degradation['signal_count']}")
    print(f"worst severity:       {degradation['worst_severity']}")
    print("degradation by type:")
    for dtype, count in sorted(degradation["counts_by_type"].items()):
        print(f"  {dtype:34s} {count}")
    print(f"repairs proposed:     {out['proposed']} (observe-only)")
    print(f"repairs applied:      "
          f"{engine.repair_memory.snapshot()['applied_count']}")
    print()

    builder = AutoRegenerationReportBuilder(engine)
    paths = builder.save(Path(args.state_dir) / "autoregeneration_report.json",
                         Path(args.state_dir) / "autoregeneration_report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: diagnostics are low-compute and non-mutating. Auto-"
          "regeneration repairs runtime state (memory, registries, edges, "
          "bounded parameters, metadata) only -- never source code, "
          "dependencies, Git, the OS, or the network.")


if __name__ == "__main__":
    main()
