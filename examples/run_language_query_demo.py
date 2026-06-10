#!/usr/bin/env python3
"""Run a short session, then answer fixed deterministic internal queries.

    python examples/run_language_query_demo.py --steps 100

No natural-language parsing beyond normalized string matching; no LLM.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.soak_continuity import ACTIONS, WORLD, _make_providers
from solaris_ai_nn.language.query import QueryInterface
from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner

QUERIES = [
    "what happened last?",
    "why was the last action suggested?",
    "what changed in the substrate?",
    "what habit is strongest?",
    "what happened during silence?",
    "did the system restart?",
    "what was pruned?",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Language query demo")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/language_query_demo")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    stimulus_provider, reaction_provider = _make_providers()
    runner = ContinuousRunner(
        state_dir=args.state_dir, max_steps=args.steps,
        checkpoint_interval_steps=max(25, args.steps // 2), seed=args.seed,
        action_labels=ACTIONS, vocabulary=list(WORLD.keys()) + ["I exist!"],
        stimulus_provider=stimulus_provider, reaction_provider=reaction_provider,
        silence_threshold=3, enable_language=True,
        prune_interval_steps=max(30, args.steps // 3),
    )
    runner.run()

    context = runner._language_context()
    qi = QueryInterface(engine=runner.bridge.explanation_engine)

    print("=" * 70)
    print(f"Solaris-AI-NN -- language query demo ({args.steps} steps)")
    print("=" * 70)
    for query in QUERIES:
        result = qi.answer(query, context)
        marker = "ok " if result.answered else "n/a"
        print(f"[{marker}] {query}")
        print(f"      {result.text}")
    print("-" * 70)
    print("All answers are deterministic renderings of recorded state; no LLM.")


if __name__ == "__main__":
    main()
