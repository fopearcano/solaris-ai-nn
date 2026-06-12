#!/usr/bin/env python3
"""Proto-language demo: signs born from a simulated developmental run.

    python examples/run_proto_language_demo.py --steps 500

A bounded simulated-time developmental run with proto-language enabled:
repeated experience earns internal symbols, sequences and proto-syntactic
regularities are probed, symbol births fossilize, and a ClaimGuard-scanned
proto-language report closes the run. No human feedback, no LLM, no
human-language claim anywhere.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental import DevelopmentalRuntime
from solaris_ai_nn.protolanguage import (
    ProtoLanguageQueryInterface,
    ProtoLanguageReportBuilder,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Proto-language demo")
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/proto_language")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    runtime = DevelopmentalRuntime(
        state_dir=args.state_dir, simulated_time=True,
        time_acceleration=3600.0, max_steps=args.steps,
        consolidation_interval_steps=100, seed=args.seed,
        enable_proto_language=True)
    runtime.run()
    layer = runtime.protolanguage
    summary = layer.summary()

    print("=" * 70)
    print("Solaris-AI-NN -- proto-language demo (internal signs, not "
          "human language)")
    print("=" * 70)
    print(f"steps run:            {args.steps} (simulated time)")
    print(f"symbols emerged:      {summary['symbol_count']} "
          f"({summary['stable_symbol_count']} stable, "
          f"{summary['ambiguous_symbol_count']} ambiguous)")
    print(f"symbol sequences:     {summary['sequence_count']}")
    print(f"proto-syntax rules:   {summary['proto_syntax_rule_count']}")
    print("sample tokens:")
    for symbol in sorted(layer.registry.symbols.values(),
                         key=lambda s: s.token)[:6]:
        print(f"  {symbol.token:28s} observed "
              f"{symbol.observation_count}x  "
              f"({symbol.debug_label[:48]})")
    proto_milestones = [m.type for m in
                        runtime.milestones.registry.milestones
                        if "symbol" in m.type or "proto" in m.type]
    print(f"proto-language milestones: {proto_milestones}")
    print()
    builder = ProtoLanguageReportBuilder(layer)
    paths = builder.save(Path(args.state_dir) / "proto_language_report.json",
                         Path(args.state_dir) / "proto_language_report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    queries = ProtoLanguageQueryInterface(layer)
    for question in ("what symbols emerged?", "is this human language?"):
        print(f"Q: {question}")
        print(f"A: {queries.answer(question).text[:150]}")
        print()
    print("note: symbols are internal operational signs grounded in "
          "recorded structure; repetition earned them and utility must "
          "keep them -- no teacher, no LLM, no understanding claim.")


if __name__ == "__main__":
    main()
