#!/usr/bin/env python3
"""Phase-2 decision gate demo: several outcomes from different inputs.

    python examples/run_phase2_decision_gate_demo.py --state-dir .solaris_ai_nn_pilot1/test_phase2_gate

Drives the decision gate with mock analysis inputs to show how it reaches
repeat_pilot1, revise_architecture, ready_for_pilot2, and archive-style
outcomes. The gate evaluates operational/evidence proxies only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.post_pilot import (
    GrowthClassification,
    Phase2DecisionGate,
    RegressionReport,
    RegressionSeverity,
)
from solaris_ai_nn.post_pilot.accumulation_vs_growth import (
    GrowthDiscriminationResult,
)
from solaris_ai_nn.post_pilot.trace_audit import TraceAuditResult


def _growth(cls):
    return GrowthDiscriminationResult(final_classification=cls)


def _trace(score):
    return TraceAuditResult(traceability_score=score)


def _exit(success):
    class _E:
        pass
    e = _E()
    e.success = success
    return e


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase-2 decision gate demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot1/test_phase2_gate")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    gate = Phase2DecisionGate()
    critical = RegressionReport(overall_severity=RegressionSeverity.CRITICAL)
    clean = RegressionReport(overall_severity=RegressionSeverity.NONE)

    cases = {
        "ready_for_pilot2": gate.decide(
            exit_decision=_exit(True),
            growth=_growth(GrowthClassification.MODERATE_GROWTH),
            regression=clean, trace_audit=_trace(0.9)),
        "repeat_pilot1": gate.decide(
            exit_decision=_exit(False),
            growth=_growth(GrowthClassification.INCONCLUSIVE),
            regression=clean, trace_audit=_trace(0.7)),
        "revise_architecture": gate.decide(
            growth=_growth(GrowthClassification.REGRESSION),
            regression=critical, trace_audit=_trace(0.6)),
        "blocked_by_safety": gate.decide(
            exit_decision=_exit(True),
            growth=_growth(GrowthClassification.MODERATE_GROWTH),
            regression=clean, trace_audit=_trace(0.9),
            safety_incident_count=2),
    }

    print("=== Phase-2 decision gate ===")
    out = {}
    for name, result in cases.items():
        out[name] = result.to_dict()
        print(f"  {name:<22} -> {result.recommendation} "
              f"(conf={result.confidence}, blockers={len(result.blockers)})")
    path = os.path.join(args.state_dir, "phase2_decision_gate.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)
    print(f"written: {path}")


if __name__ == "__main__":
    main()
