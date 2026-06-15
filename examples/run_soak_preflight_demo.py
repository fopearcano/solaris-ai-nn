#!/usr/bin/env python3
"""Soak preflight demo: validate readiness without starting the run.

    python examples/run_soak_preflight_demo.py --state-dir .solaris_ai_nn_soak/test_preflight

Demonstrates preflight checks, a live-mode stage blocked without governance, and
a missing-optional-module warning. Preflight never starts the run. The soak
protocol studies structural development; it does not prove life or consciousness.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.developmental_soak import DevelopmentalSoakRuntime


def main():
    parser = argparse.ArgumentParser(description="Soak preflight demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_soak/test_preflight")
    args = parser.parse_args()

    # 1. Fixture preflight: required modules present, run not started.
    rt = DevelopmentalSoakRuntime(state_dir=args.state_dir, max_ticks=4,
                                  max_runtime_s=15.0)
    pf = rt.run_preflight()

    # 2. Live mode requested without governance -> live checks BLOCKED.
    live = DevelopmentalSoakRuntime(
        state_dir=os.path.join(args.state_dir, "live"), max_ticks=4,
        max_runtime_s=15.0, allow_live_read_only=True,
        require_governance_for_live=True, governance_approved=False)
    live_pf = live.run_preflight(source_paths=[])

    print("=== Soak preflight demo ===")
    print(f"fixture preflight passed : {pf['passed']} "
          f"(pass {pf['pass_count']}, fail {pf['fail_count']}, "
          f"warn {pf['warn_count']})")
    print(f"started the run          : {pf['started_run']} (preflight never "
          "starts the run)")
    print(f"live preflight blocked   : {live_pf['blocked_count']} live "
          f"check(s) blocked -> {live_pf['live_blocked_checks']}")
    warns = [r['check_id'] for r in pf['results'] if r['status'] == 'warn']
    print(f"optional-module warnings : {warns or 'none'}")
    print("note                     : preflight validates readiness only; the "
          "soak studies structural development, not life or consciousness.")


if __name__ == "__main__":
    main()
