#!/usr/bin/env python3
"""World model demo: a bounded signal-only run grows the knowledge graph.

    python examples/run_world_model_demo.py --steps 200

A patterned stimulus stream (with reactions) runs through the ordinary
ContinuousRunner with the world model enabled. The graph accumulates
stimulus patterns, signal types, actions, reactions, contexts, associations,
and candidate causal relations -- all inspectable, all persisted under the
state directory. No production pruning, no claims of understanding.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
from solaris_ai_nn.signals import canonical as C
from solaris_ai_nn.world_model import WorldModelQueryInterface


def main() -> None:
    parser = argparse.ArgumentParser(description="World model demo")
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/world_model_demo")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    payloads = ["light", "noise", "food"]

    def provider(step):
        if step <= (2 * args.steps) // 3:
            return C.Stimulus(payload=payloads[step % 3], intensity=0.5)
        return None  # silence at the end: absence patterns enter the graph

    def reaction(result, stim):
        return 1.0 if result["suggested_action"] == "approach" else -0.5

    runner = ContinuousRunner(
        state_dir=args.state_dir, max_steps=args.steps, seed=args.seed,
        vocabulary=payloads,
        stimulus_provider=provider, reaction_provider=reaction,
        enable_world_model=True)
    runner.run()
    builder = runner.world_model
    summary = builder.world_model_summary()

    print("=" * 70)
    print("Solaris-AI-NN -- world model demo (observed structure only)")
    print("=" * 70)
    print(f"graph nodes:        {summary['graph_node_count']}")
    print(f"graph edges:        {summary['graph_edge_count']}")
    print(f"node types:         {builder.graph.node_counts_by_type()}")
    strongest = summary["strongest_association"]
    if strongest:
        print(f"strongest assoc.:   {strongest['source']!r} -> "
              f"{strongest['target']!r} ({strongest['kind']}, "
              f"{strongest['count']}x)")
    top = summary["top_causal_candidate"]
    if top:
        print(f"top causal cand.:   {top['source']!r} -> {top['target']!r} "
              f"(confidence {top['confidence']}, "
              f"{top['evidence_count']} obs)")
    print(f"unknown nodes:      {summary['unknown_node_count']}")
    print(f"evidence ratio:     {summary['evidence_ratio']}")
    print()
    queries = WorldModelQueryInterface(builder=builder)
    for question in ("what does the world model know?",
                     "what is the strongest association?",
                     "what is still unknown?"):
        print(f"Q: {question}")
        print(f"A: {queries.answer(question).text[:160]}")
        print()
    print(f"artifacts: {args.state_dir}/world_model.json (.dot/.mmd/"
          "_report.md alongside)")


if __name__ == "__main__":
    main()
