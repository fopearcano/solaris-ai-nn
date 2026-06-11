#!/usr/bin/env python3
"""Identity continuity demo: anchors across four runtime situations.

    python examples/run_identity_continuity_demo.py

Four phases: a clean start, a checkpoint restore (continuity is
checkpoint-mediated), a restart gap (score drops, warning recorded), and a
mismatched run-id anchor (uncertainty reported, never papered over).
Identity here means operational runtime continuity -- nothing more.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.ego import IdentityState


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Identity continuity demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/"
                                "identity_continuity_demo")
    args = parser.parse_args()

    anchors = {
        "run_id": "run-2026-001", "session_id": "session-1",
        "substrate_identity": "esn", "state_path": "/state/run-2026-001",
        "inner_map_signature": "map-v1",
        "governance_policy_signature": "policy-v1",
    }
    identity = IdentityState()

    print("=" * 70)
    print("Solaris-AI-NN -- identity continuity demo (runtime continuity, "
          "not personhood)")
    print("=" * 70)

    phases = [
        ("clean start", dict(anchors)),
        ("checkpoint restore", dict(anchors, session_id="session-2",
                                    restored_from_checkpoint=True)),
        ("restart gap", dict(anchors, session_id="session-3",
                             restart_gap_detected=True)),
        ("mismatched anchor", dict(anchors, session_id="session-4",
                                   run_id="run-2026-OTHER")),
    ]
    for name, context in phases:
        score = identity.update(context)
        print(f"phase: {name}")
        print(f"  continuity score: {score.score:.2f}   "
              f"confidence: {identity.identity_confidence:.2f}")
        if score.mismatched:
            print(f"  mismatched anchors: {score.mismatched}")
        for warning in score.warnings:
            print(f"  warning: {warning[:90]}")
        print()

    print(f"total mismatches: {identity.mismatch_count}")
    print(f"unresolved warnings: {len(identity.identity_warnings)}")
    out = Path(args.state_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "identity_state.json", "w", encoding="utf-8") as fh:
        json.dump(identity.to_dict(), fh, indent=2, default=str)
    print(f"identity state saved: {out / 'identity_state.json'}")
    print()
    print("note: anchors that mismatch produce reported uncertainty -- "
          "the system never asserts an unqualified continuous identity.")


if __name__ == "__main__":
    main()
