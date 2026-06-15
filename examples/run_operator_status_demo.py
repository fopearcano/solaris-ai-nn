#!/usr/bin/env python3
"""Operator status demo: status board + profile summary + safety summary.

    python examples/run_operator_status_demo.py --state-dir .solaris_ai_nn_operator/test_status

Builds the operator status board (ClaimGuard-scanned) from the local profile
catalog and any provided status, prints a profile summary and a safety summary,
and writes STATUS_BOARD.md / .json. The console coordinates; it grants no
real-world authority and cannot bypass governance or safety.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.operator_console import (
    OperatorConsoleConfig,
    OperatorStatusBoard,
    ProfileCatalog,
)


def main():
    parser = argparse.ArgumentParser(description="Operator status demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_operator/test_status")
    args = parser.parse_args()

    cfg = OperatorConsoleConfig(state_dir=args.state_dir)
    cfg.ensure_dirs()
    catalog = ProfileCatalog()
    # A mock safety status (no live safety run attached in this demo).
    safety = {"status": "ok", "red_team_status": "ok",
              "assurance_status": "compiled", "unresolved_blocker_count": 0}
    board = OperatorStatusBoard(config=cfg, catalog=catalog, safety_status=safety)
    result = board.write()
    snap = result["snapshot"]

    print("=== Operator status demo ===")
    print(f"console mode          : {snap.console_mode}")
    print(f"available profiles    : {snap.available_profile_count}")
    print(f"blocked profiles      : {snap.blocked_profile_count}")
    print(f"safety status         : {snap.latest_safety_status}")
    print(f"unresolved blockers   : {snap.unresolved_safety_blocker_count}")
    print(f"recommended next      : {snap.recommended_next_action}")
    print(f"claim-guard safe      : {snap.claim_guard_safe}")
    print(f"status board          : {result['markdown']}")
    print("note                  : local coordination only; no real-world "
          "authority.")


if __name__ == "__main__":
    main()
