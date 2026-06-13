#!/usr/bin/env python3
"""Hypothesis falsification demo: support then falsify, carefully.

    python examples/run_hypothesis_falsification_demo.py

Generates a prediction hypothesis candidate, runs a bounded test that
supports it (nursery-simulated evidence raises confidence in a bounded
step), then a test that contradicts it (falsifying evidence lowers
confidence and marks it falsified). One success does not prove it; one clear
failure can falsify it.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.hypothesis import (
    EvidenceLedger,
    EvidenceRecord,
    EvidenceType,
    FalsificationEngine,
    HypothesisMemory,
    HypothesisReportBuilder,
)
from solaris_ai_nn.hypothesis import HypothesisEngine
from solaris_ai_nn.hypothesis.hypotheses import Hypothesis, HypothesisType


def main() -> None:
    parser = argparse.ArgumentParser(description="Hypothesis falsification "
                                                 "demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/hypothesis_falsification")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    engine = HypothesisEngine(state_dir=args.state_dir)
    hypothesis = Hypothesis(
        type=HypothesisType.PREDICTION,
        statement="prediction candidate: pattern A may predict a positive "
                  "reaction",
        expected_observation="positive reaction follows pattern A",
        alternative_observation="no positive reaction follows pattern A",
        confidence=0.5, target_ref="pattern_A")
    engine.memory.add(hypothesis)
    falsifier = FalsificationEngine()
    ledger: EvidenceLedger = engine.runner.evidence_ledger

    print("=" * 70)
    print("Solaris-AI-NN -- hypothesis falsification (careful, bounded)")
    print("=" * 70)
    print(f"hypothesis:        {hypothesis.statement}")
    print(f"start confidence:  {hypothesis.confidence}")

    support = EvidenceRecord(
        hypothesis_id=hypothesis.hypothesis_id,
        evidence_type=EvidenceType.NURSERY_SIMULATED,
        source_scope="nursery_simulation",
        observation="a positive reaction followed pattern A in the nursery")
    ledger.record(support)
    res_s = falsifier.evaluate(hypothesis, support)
    falsifier.update_confidence(hypothesis, res_s)
    print(f"after support:     verdict={res_s.verdict} "
          f"confidence={hypothesis.confidence} status={hypothesis.status}")

    falsify = EvidenceRecord(
        hypothesis_id=hypothesis.hypothesis_id,
        evidence_type=EvidenceType.FALSIFYING,
        source_scope="nursery_simulation",
        observation="pattern A occurred but no positive reaction followed")
    ledger.record(falsify)
    res_f = falsifier.evaluate(hypothesis, falsify)
    falsifier.update_confidence(hypothesis, res_f)
    print(f"after falsifier:   verdict={res_f.verdict} "
          f"confidence={hypothesis.confidence} status={hypothesis.status}")
    engine.memory.record_status(hypothesis, detail=res_f.verdict)
    engine.memory.save_state()
    print()

    builder = HypothesisReportBuilder(engine)
    paths = builder.save(Path(args.state_dir) / "report.json",
                         Path(args.state_dir) / "report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: one success rarely proves a hypothesis and one failure can "
          "falsify it; confidence moves in small bounded steps. The system "
          "has not proven the relation.")


if __name__ == "__main__":
    main()
