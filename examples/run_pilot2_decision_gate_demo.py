#!/usr/bin/env python3
"""Pilot-2 decision gate demo: several outcomes from different inputs.

    python examples/run_pilot2_decision_gate_demo.py --state-dir .solaris_ai_nn_pilot2/test_decision_gate

Drives the Pilot-2 decision gate with mock grounding/reliability inputs to show
repeat / reduce-complexity / extend-soak / revise-membrane outcomes, and that a
Pilot-3 limited-embodiment suggestion (if any) is planning-only. Actuation is
never an enabled action.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot2 import (
    GroundingAnalysis,
    Pilot2DecisionGate,
    SourceReliabilityMonitor,
)


def _grounding(quality):
    ga = GroundingAnalysis()
    if quality == "strong":
        ga.add("proto_symbol", provenance_complete=True, repeated_pattern=True,
               persistent=True, improves_prediction_or_compression=True,
               cross_module_support=True, evidence_refs=["r1"])
    elif quality == "weak":
        ga.add("proto_symbol", provenance_complete=True, repeated_pattern=True,
               evidence_refs=["r1"])
    return ga


def main():
    parser = argparse.ArgumentParser(description="Pilot-2 decision gate demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot2/test_decision_gate")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    gate = Pilot2DecisionGate()
    unsafe = SourceReliabilityMonitor()
    unsafe.observe_poll("bad", success=True, events=10, malformed=9,
                        unsafe=True)

    cases = {
        "extend_read_only_soak": gate.decide(grounding=_grounding("strong")),
        "repeat_with_curated_sources": gate.decide(
            grounding=_grounding("weak")),
        "revise_membrane_unsafe_source": gate.decide(
            grounding=_grounding("strong"), reliability=unsafe),
        "reduce_complexity_over_budget": gate.decide(
            grounding=_grounding("strong"), resource_over_budget=True),
    }

    out = {name: r.to_dict() for name, r in cases.items()}
    path = os.path.join(args.state_dir, "decision_gate.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)

    print("=== Pilot-2 decision gate demo ===")
    for name, r in cases.items():
        plan = " [planning-only]" if r.planning_only else ""
        print(f"  {name:<32} -> {r.recommendation}{plan} "
              f"(blockers={len(r.blockers)})")
    print(f"written : {path}")
    print("note    : actuation is never an enabled action; any Pilot-3 "
          "embodiment is planning-only")


if __name__ == "__main__":
    main()
