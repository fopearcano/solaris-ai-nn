#!/usr/bin/env python3
"""Proto-symbol hypothesis demo: does this sign refer to two patterns?

    python examples/run_proto_symbol_hypothesis_demo.py

An ambiguous proto-symbol seeds a grounding hypothesis candidate ("symbol X
may refer to two different patterns"). The engine tests it via latent replay
(offline) and reports the ambiguity score before and after -- honestly, the
result may be inconclusive because offline support cannot fully promote.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.hypothesis import HypothesisEngine, HypothesisReportBuilder


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Proto-symbol hypothesis demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/hypothesis_proto")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    engine = HypothesisEngine(state_dir=args.state_dir)
    ambiguity_before = 0.6
    ambiguity_after = 0.4
    ctx = {
        "step": 0, "mysterium_pressure": 0.3,
        "proto_language": {"symbol_count": 6, "ambiguous_symbol_count": 4,
                           "ambiguous_symbols": ["SIG_LIGHT_0001"]},
        "before": {"proto_language": {"ambiguity_score": ambiguity_before}},
        "after": {"proto_language": {"ambiguity_score": ambiguity_after}},
        "health_level": "ok",
    }
    out = engine.tick(ctx)
    summary = engine.summary()
    families = engine.memory.family_counts()

    print("=" * 70)
    print("Solaris-AI-NN -- proto-symbol grounding hypothesis")
    print("=" * 70)
    print(f"hypotheses generated:        {out['new_hypotheses']}")
    print(f"grounding hypothesis family: "
          f"{families.get('proto_symbol_grounding_hypothesis', 0)}")
    print(f"ambiguity score before:      {ambiguity_before}")
    print(f"ambiguity score after:       {ambiguity_after}")
    print(f"tests run:                   {summary['tests_run']}")
    print(f"last evidence result:        {summary['last_evidence_result']}")
    snap = engine.snapshot()
    print(f"offline evidence records:    "
          f"{snap['test_runner']['evidence']['offline_count']}")
    print()

    builder = HypothesisReportBuilder(engine)
    paths = builder.save(Path(args.state_dir) / "report.json",
                         Path(args.state_dir) / "report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: the grounding hypothesis is tested by latent replay, so its "
          "evidence is offline and cannot fully promote the hypothesis; a "
          "real/nursery observation would be needed. Proto-symbols are "
          "internal signs, not human language.")


if __name__ == "__main__":
    main()
