#!/usr/bin/env python3
"""World-model hygiene demo: mark contradictions, preserve evidence.

    python examples/run_world_model_hygiene_demo.py

Builds a world-model context with contradictory, weak, and stale edges, then
proposes hygiene: mark contradictions ambiguous (evidence preserved) and
request a hypothesis test, and weaken decayed edges. Contradiction evidence
is never deleted silently; marking/weakening is preferred over deletion.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.autoregeneration import (
    AutoRegenerationEngine,
    AutoRegenerationReportBuilder,
    RepairPolicy,
    WorldModelHygieneManager,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="World-model hygiene demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/world_model_hygiene")
    args = parser.parse_args()

    ctx = {"world_model": {
        "graph_node_count": 25, "graph_edge_count": 40,
        "contradiction_edges": ["a|contradicts|b", "c|contradicts|d"],
        "weak_edges": ["x|predicts|y"],
        "stale_prediction_edges": ["p|predicts|q"],
        "unsupported_causal_claims": ["m|causes_candidate|n"]}}
    mgr = WorldModelHygieneManager()
    actions = mgr.propose(ctx)
    detected = mgr.findings[-1]

    print("=" * 70)
    print("Solaris-AI-NN -- world-model hygiene (mark/weaken, keep evidence)")
    print("=" * 70)
    print(f"contradiction edges:  {detected['contradiction_edges']}")
    print(f"weak edges:           {detected['weak_edges']}")
    print(f"stale prediction:     {detected['stale_prediction_edges']}")
    print(f"unsupported causal:   {detected['unsupported_causal_claims']}")
    print("proposed hygiene actions:")
    for a in actions:
        print(f"  {a.action_type:28s} {a.target_ref}")
    print(f"hypothesis test requests: {mgr.hypothesis_requests}")
    print()

    engine = AutoRegenerationEngine(
        state_dir=args.state_dir, policy=RepairPolicy(mode="safe_auto_repair"))
    engine.tick(ctx)
    builder = AutoRegenerationReportBuilder(engine)
    paths = builder.save(Path(args.state_dir) / "report.json",
                         Path(args.state_dir) / "report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: contradiction evidence is never deleted silently. Hygiene "
          "marks edges ambiguous or weakens them and requests a hypothesis "
          "test to resolve the contradiction with real evidence.")


if __name__ == "__main__":
    main()
