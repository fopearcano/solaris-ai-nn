#!/usr/bin/env python3
"""Tester packaging demo: run the report-only packaging readiness runtime.

    python examples/run_tester_packaging_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_packaging_demo

Runs the dependency check, environment doctor, command registry check, builds the
install guides + quickstart + platform notes, builds the release manifest, and runs the
clean-machine readiness check. It installs nothing and publishes nothing.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_packaging import TesterPackagingRuntime


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_packaging_demo")
    args = ap.parse_args()

    rt = TesterPackagingRuntime(tester_state_dir=args.tester_state_dir)
    result = rt.run()
    print("tester packaging demo")
    print(f"  readiness        : {result['readiness']}")
    print(f"  doctor           : {result['doctor_status']}")
    print(f"  dependency blocks: {result['dependency_blocker_count']}")
    print(f"  missing cmds     : {result['missing_required_command_count']}")
    print(f"  clean machine    : {result['clean_machine_status']}")
    print(f"  release          : {result['release_readiness']}")
    print(f"  report           : {result['latest_packaging_report_path']}")
    print(f"  install guide    : {result['latest_install_guide_path']}")
    print(f"  release manifest : {result['latest_release_manifest_path']}")
    print("note: the packaging runtime is local and report-only -- it installs "
          "nothing, publishes nothing, and creates no releases/tags.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
