#!/usr/bin/env python3
"""Self-report demo: the self-model in careful words.

    python examples/run_self_report_demo.py

Builds a self-model from a short bounded context, answers the eight ego
queries, and saves the Markdown self-report -- which must pass ClaimGuard
and the identity-claim scan before a single byte is written.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.ego import EgoQueryInterface, SelfModel, SelfReportBuilder


def main() -> None:
    parser = argparse.ArgumentParser(description="Self-report demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/self_report_demo")
    args = parser.parse_args()

    Path(args.state_dir).mkdir(parents=True, exist_ok=True)
    model = SelfModel(state_dir=args.state_dir)
    model.update({"run_id": "self-report-demo", "session_id": "s1",
                  "substrate_identity": "esn",
                  "state_path": args.state_dir, "health_level": "ok",
                  "embodiment": {"energy": 7.5, "max_energy": 10.0,
                                 "position": (3, 4)}})
    for event in ({"source": "homeostasis", "kind": "desire_candidate",
                   "label": "rest"},
                  {"source": "stream", "kind": "stream_line"},
                  {"source": "offline_replay", "kind": "replay_trace"}):
        model.classify_event(event)

    print("=" * 70)
    print("Solaris-AI-NN -- self-report demo (safe wording, scanned "
          "before saving)")
    print("=" * 70)
    queries = EgoQueryInterface(model)
    for question in queries.supported_queries():
        print(f"Q: {question}?")
        print(f"A: {queries.answer(question).text[:160]}")
        print()

    builder = SelfReportBuilder(model)
    paths = builder.save(Path(args.state_dir) / "self_report.json",
                         Path(args.state_dir) / "self_report.md")
    print(f"report: {paths['markdown']} "
          f"(claim guard safe: {paths['claim_guard']['safe']})")
    print()
    print("note: the report says 'operational identity' and 'runtime "
          "continuity' -- never consciousness, soul, or wanting, and "
          "the identity-claim scan would block those words.")


if __name__ == "__main__":
    main()
