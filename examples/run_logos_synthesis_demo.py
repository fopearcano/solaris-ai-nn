#!/usr/bin/env python3
"""LOGOS synthesis demo: propose a bounded resolution, validate, apply/refuse.

    python examples/run_logos_synthesis_demo.py

Detects tensions, proposes synthesis candidates, runs them through the
safety validator and resolution policy, and shows which were applied,
preserved, or refused. Synthesis is proposed, not assumed true; safety and
governance remain authoritative.
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
    SynthesisEngine,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="LOGOS synthesis demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/logos_synthesis")
    args = parser.parse_args()

    engine = LogosComplexityEngine(
        state_dir=args.state_dir,
        policy=ResolutionPolicy(mode="balanced_resolution"))
    ctx = {
        "world_model": {"contradiction_edges": ["a|contradicts|b"],
                        "prediction_accuracy": 0.3},
        "proto_language": {"symbol_count": 30, "ambiguous_symbol_count": 12,
                           "ambiguous_symbols": ["ABS_0005"]},
        "mysterium_pressure": 0.6, "homeostasis": {"conflict_count": 1},
        "state_dir": args.state_dir,
    }
    # Show candidate proposal for the first tension.
    tensions = engine.fracture.scan(ctx)
    synth = SynthesisEngine()
    print("=" * 70)
    print("Solaris-AI-NN -- LOGOS synthesis (proposed, not assumed true)")
    print("=" * 70)
    if tensions:
        first = tensions[0]
        candidates = synth.propose(first, ctx)
        print(f"tension: {first.tension_type} "
              f"({first.polarity_a} vs {first.polarity_b})")
        print("synthesis candidates:")
        for c in candidates:
            print(f"  {c.synthesis_type:28s} risk={c.expected_risk} "
                  f"reversible={c.reversible}")

    out = engine.tick(ctx)
    snap = engine.snapshot()
    print(f"\nresolved this cycle:  {out['resolved']}")
    print(f"synthesis applied:    {snap['synthesis']['applied_total']}")
    print(f"synthesis refused:    {snap['synthesis']['refused_total']}")
    print(f"tensions preserved:   "
          f"{snap['opposition_memory']['preserved_count']}")
    print()

    builder = LogosComplexityReportBuilder(engine)
    paths = builder.save(Path(args.state_dir) / "report.json",
                         Path(args.state_dir) / "report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: a synthesis candidate proposes a bounded resolution; it is "
          "reversible and low-risk where possible, and safety/governance/the "
          "executive remain authoritative. Some tensions stay unresolved.")


if __name__ == "__main__":
    main()
