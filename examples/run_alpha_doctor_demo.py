#!/usr/bin/env python3
"""Alpha doctor demo: pass, optional-missing warning, strict blocker behavior.

    python examples/run_alpha_doctor_demo.py --state-dir .solaris_ai_nn_alpha/test_doctor

Runs the read-only Alpha doctor (system check) and prints each result. It then
shows how strict mode treats a blocker (using a synthetic missing-required-module
registry so the demo is self-contained). The doctor executes nothing, requires no
live mode, network, or Git/GitHub, and makes no consciousness/life/agency claim.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.alpha_system import (
    AlphaModuleRegistry,
    AlphaModuleStatus,
    AlphaSystemCheck,
    default_alpha_profile,
)


def main():
    parser = argparse.ArgumentParser(description="Alpha doctor demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_alpha/test_doctor")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    profile = default_alpha_profile()
    registry = AlphaModuleRegistry.build()

    print("=== Alpha doctor demo ===")
    checker = AlphaSystemCheck()
    checker.run(state_root=args.state_dir, profile=profile, registry=registry)
    summary = checker.summary()
    for r in summary["results"]:
        print(f"  [{r['severity']}] {r['name']}: {r['detail']}")
    print(f"  -> {summary['pass_count']} pass, {summary['warning_count']} "
          f"warning(s), {summary['blocker_count']} blocker(s), passed="
          f"{summary['passed']}")

    # Show the strict blocker path with a synthetic missing required module.
    print("\n  strict-mode blocker illustration:")
    for r in registry.records:
        if r.key == "evaluation":
            r.status = AlphaModuleStatus.MISSING
    blocked = AlphaSystemCheck()
    blocked.run(state_root=args.state_dir, profile=profile, registry=registry)
    bsummary = blocked.summary()
    print(f"    blockers now: {bsummary['blocker_count']} (strict mode would "
          f"return nonzero exit)")
    print("note: the doctor runs read-only checks only; nothing is executed and "
          "no live mode, network, Git/GitHub, or feeder access is required.")


if __name__ == "__main__":
    main()
