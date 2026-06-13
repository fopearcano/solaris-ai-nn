#!/usr/bin/env python3
"""Complexity regulation demo: inert, productive, and overloaded bands.

    python examples/run_complexity_regulation_demo.py

Runs the complexity regulator on three contexts -- inert (near-zero change),
productive (the bounded middle), and overloaded (critical/very high pressure)
-- and shows the band and recommendation for each. Complexity is an
operational regulation signal, not a consciousness or life score.
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
    ComplexityRegulator,
    LogosComplexityEngine,
    LogosComplexityReportBuilder,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Complexity regulation demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/complexity_regulation")
    args = parser.parse_args()

    reg = ComplexityRegulator()
    inert = reg.estimate({"proto_language": {"symbol_count": 0},
                          "stagnation_status": "inert",
                          "mysterium_pressure": 0.0})
    productive = reg.estimate({
        "proto_language": {"symbol_count": 40, "ambiguous_symbol_count": 8},
        "world_model": {"graph_node_count": 20, "graph_edge_count": 30},
        "mysterium_pressure": 0.3, "hypothesis": {"hypothesis_count": 20}})
    overloaded = reg.estimate({
        "proto_language": {"symbol_count": 900, "ambiguous_symbol_count":
                           400},
        "world_model": {"graph_node_count": 10, "graph_edge_count": 200,
                        "contradiction_edges": ["a|c|b"]},
        "mysterium_pressure": 0.95, "memory": {"over_budget": ["hot"]},
        "autoregeneration": {"latest_degradation_severity": "critical"}})

    print("=" * 70)
    print("Solaris-AI-NN -- complexity regulation (inert / productive / "
          "overloaded)")
    print("=" * 70)
    for label, state in (("inert", inert), ("productive", productive),
                         ("overloaded", overloaded)):
        print(f"{label:12s} -> band={state.band:18s} "
              f"score={state.pressure.score:.3f} "
              f"recommend={state.recommendation}")
    print()

    engine = LogosComplexityEngine(state_dir=args.state_dir)
    engine.tick({"proto_language": {"symbol_count": 40,
                                    "ambiguous_symbol_count": 8},
                 "mysterium_pressure": 0.3, "state_dir": args.state_dir})
    builder = LogosComplexityReportBuilder(engine)
    paths = builder.save(Path(args.state_dir) / "report.json",
                         Path(args.state_dir) / "report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: too little complexity can mean an inert/dead system; too "
          "much means overload; productive complexity is the bounded middle. "
          "This is not a consciousness or life score.")


if __name__ == "__main__":
    main()
