#!/usr/bin/env python3
"""Symbol hygiene demo: tend the proto-symbol ecology, never rename it.

    python examples/run_symbol_hygiene_demo.py

Builds a proto-symbol context with explosion, duplicates, stale, ungrounded,
and ambiguous symbols, then proposes hygiene actions: mark stale, merge
duplicates, request disambiguation. Symbols are internal signs, never human
words; nothing is renamed and stable symbols are never deleted.
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
    SymbolHygieneManager,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Symbol hygiene demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/symbol_hygiene")
    args = parser.parse_args()

    ctx = {"proto_language": {
        "symbol_count": 600,
        "stale_symbols": ["ABS_0001", "SIG_0007"],
        "duplicate_symbols": ["NEED_0002|NEED_0003"],
        "ungrounded_symbols": ["UNK_0009"],
        "ambiguous_symbols": ["SIG_0005"]}}
    mgr = SymbolHygieneManager()
    actions = mgr.propose(ctx)
    detected = mgr.findings[-1]

    print("=" * 70)
    print("Solaris-AI-NN -- symbol hygiene (mark/merge, never rename)")
    print("=" * 70)
    print(f"symbol count:         {detected['symbol_count']} "
          f"(explosion: {detected['explosion']})")
    print(f"stale symbols:        {detected['stale_symbols']}")
    print(f"duplicate symbols:    {detected['duplicate_symbols']}")
    print(f"ungrounded symbols:   {detected['ungrounded_symbols']}")
    print(f"ambiguous symbols:    {detected['ambiguous_symbols']}")
    print("proposed hygiene actions:")
    for a in actions:
        print(f"  {a.action_type:26s} {a.target_ref}  ({a.reason})")
    print(f"disambiguation requests: {mgr.disambiguation_requests}")
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
    print("note: symbols are internally generated signs, not human language. "
          "Hygiene marks stale / merges duplicates / requests "
          "disambiguation; it never renames a symbol with a human word and "
          "never deletes a stable symbol without archive.")


if __name__ == "__main__":
    main()
