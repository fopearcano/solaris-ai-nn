#!/usr/bin/env python3
"""LOGOS fracture demo: detect productive tensions, mutate nothing.

    python examples/run_logos_fracture_demo.py

Builds a context with a world-model contradiction, an ambiguous proto-symbol,
a prediction failure, and high Mysterium, then runs the fracture detector in
observe-only mode: it surfaces the active tensions between opposed internal
poles. A fracture is not an error -- some tensions are productive and will be
preserved.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.logos_complexity import (
    LogosComplexityEngine,
    LogosComplexityReportBuilder,
    ResolutionPolicy,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="LOGOS fracture demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/logos_fracture")
    args = parser.parse_args()

    engine = LogosComplexityEngine(
        state_dir=args.state_dir,
        policy=ResolutionPolicy(mode="observe_only"))
    ctx = {
        "world_model": {"graph_node_count": 20, "graph_edge_count": 35,
                        "contradiction_edges": ["a|contradicts|b"],
                        "prediction_accuracy": 0.2},
        "proto_language": {"symbol_count": 40, "ambiguous_symbol_count": 18,
                           "ambiguous_symbols": ["ABS_0003", "SIG_0007"]},
        "mysterium_pressure": 0.85,
        "homeostasis": {"conflict_count": 1},
        "state_dir": args.state_dir,
    }
    out = engine.tick(ctx)

    print("=" * 70)
    print("Solaris-AI-NN -- LOGOS fracture (tension is productive pressure)")
    print("=" * 70)
    print(f"tensions detected:    {out['tensions']}")
    print(f"complexity band:      {out['complexity_band']}")
    print("active tensions:")
    for t in engine.fracture.last_tensions:
        print(f"  {t.tension_type:28s} {t.polarity_a} vs {t.polarity_b} "
              f"[{t.severity}] -> {t.status}")
    print()

    builder = LogosComplexityReportBuilder(engine)
    paths = builder.save(Path(args.state_dir) / "logos_report.json",
                         Path(args.state_dir) / "logos_report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: LOGOS is a tension engine, not an authority. A fracture is "
          "not an error; it exposes opposition and proposes bounded "
          "resolution paths. No truth is decided here.")


if __name__ == "__main__":
    main()
