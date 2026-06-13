#!/usr/bin/env python3
"""Proto-symbol disambiguation demo: sample to test an ambiguous sign.

    python examples/run_proto_symbol_disambiguation_demo.py

An ambiguous proto-symbol (inconsistent grounding) raises uncertainty. The
sampling policy chooses an action that targets the symbol; we show its
ambiguity before and after. The "after" change is reported honestly -- it
may improve, stay the same, or be reported as no change.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.active_perception import (
    ActivePerceptionReportBuilder,
    ActiveSensingController,
    ExplorationMemory,
    SamplingPolicy,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Proto-symbol disambiguation demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/proto_disambiguation")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    controller = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=args.seed),
        memory=ExplorationMemory(state_dir=args.state_dir))
    before = {
        "step": 0,
        "proto_language": {"symbol_count": 6, "ambiguous_symbol_count": 4,
                           "ambiguous_symbols": ["SIG_LIGHT_0001"]},
        "health_level": "ok", "energy": 0.9,
    }
    decision = controller.select(before)
    result = controller.execute_if_allowed(decision, before)
    after = {
        "step": 1,
        "proto_language": {"symbol_count": 6, "ambiguous_symbol_count": 2},
    }
    record = controller.observe_result(result, before, after)

    print("=" * 70)
    print("Solaris-AI-NN -- proto-symbol disambiguation (sample to test a "
          "sign)")
    print("=" * 70)
    print(f"selected action:     {decision.action.action_type}")
    print(f"target_ref:          {decision.action.target_ref}")
    print(f"ambiguity before:    "
          f"{before['proto_language']['ambiguous_symbol_count']} "
          f"of {before['proto_language']['symbol_count']}")
    print(f"ambiguity after:     "
          f"{after['proto_language']['ambiguous_symbol_count']} "
          f"of {after['proto_language']['symbol_count']}")
    print(f"observed info gain:  {record.observed_information_gain}")
    print(f"outcome:             {record.outcome}")
    print()

    builder = ActivePerceptionReportBuilder(controller)
    paths = builder.save(Path(args.state_dir) / "report.json",
                         Path(args.state_dir) / "report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: sampling tests a sign; whether ambiguity falls is reported "
          "honestly either way. Proto-symbols are internal signs, never "
          "human language, and sampling them is internal/simulation only.")


if __name__ == "__main__":
    main()
