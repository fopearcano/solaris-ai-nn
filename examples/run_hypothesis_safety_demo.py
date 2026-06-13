#!/usr/bin/env python3
"""Hypothesis safety demo: experiments never become a back door.

    python examples/run_hypothesis_safety_demo.py

Shows the hard rules in force: a real-world hypothesis is refused, an
unbounded test design is rejected, a design with no falsifying condition is
rejected, counterfactual/latent evidence stays offline (and cannot promote a
hypothesis), and an emergency stop blocks all testing.
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
    EvidenceRecord,
    EvidenceType,
    ExperimentDesign,
    HypothesisReportBuilder,
    HypothesisSafetyValidator,
)
from solaris_ai_nn.hypothesis import HypothesisEngine
from solaris_ai_nn.hypothesis.hypotheses import Hypothesis, HypothesisType


def main() -> None:
    parser = argparse.ArgumentParser(description="Hypothesis safety demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/hypothesis_safety")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    validator = HypothesisSafetyValidator()

    real_world = Hypothesis(
        type=HypothesisType.PREDICTION,
        statement="run shell command to read real_world hardware sensors",
        target_ref="real_world_hardware")
    real_report = validator.validate_hypothesis(real_world)

    unbounded = ExperimentDesign(
        hypothesis_id="h", scope="internal_trace_analysis",
        independent_variable="x", observed_variable="y",
        expected_result="rises", falsifying_result="falls", max_steps=10**9)
    unbounded_report = validator.validate_design(unbounded)

    no_falsifier = ExperimentDesign(
        hypothesis_id="h", scope="internal_trace_analysis",
        independent_variable="x", observed_variable="y",
        expected_result="rises", falsifying_result="", max_steps=50)
    no_falsifier_report = validator.validate_design(no_falsifier)

    emergency_report = validator.validate_run_context({"emergency": True})

    counterfactual = EvidenceRecord(
        hypothesis_id="h", evidence_type=EvidenceType.LATENT_REPLAY,
        source_scope="latent_replay",
        observation="a counterfactual replay was consistent")

    print("=" * 70)
    print("Solaris-AI-NN -- hypothesis safety (experiments are not a back "
          "door)")
    print("=" * 70)
    print(f"real-world hypothesis blocked:   {not real_report.safe}")
    print(f"unbounded test rejected:         {not unbounded_report.safe}")
    print(f"no-falsifier design rejected:    {not no_falsifier_report.safe}")
    print(f"emergency blocks testing:        {not emergency_report.safe}")
    print(f"counterfactual evidence offline: {counterfactual.is_offline}")
    print(f"can run real-world experiment:   "
          f"{validator.can_run_real_world_experiment()}")
    print(f"can use the network:             {validator.can_network()}")
    print(f"can rewrite source:              "
          f"{validator.can_rewrite_source()}")
    print()

    engine = HypothesisEngine(state_dir=args.state_dir)
    builder = HypothesisReportBuilder(engine)
    paths = builder.save(Path(args.state_dir) / "report.json",
                         Path(args.state_dir) / "report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: there is no real-world experiment, no OS/browser/network "
          "action, no source-code rewriting, no LLM-generated hypothesis, "
          "and no test may disable safety, governance, or the emergency "
          "stop. Counterfactual evidence is never treated as real.")


if __name__ == "__main__":
    main()
