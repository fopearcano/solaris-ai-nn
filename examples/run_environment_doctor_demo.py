#!/usr/bin/env python3
"""Environment doctor demo: pass, missing-optional warning, missing-required blocker.

    python examples/run_environment_doctor_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_doctor_demo

Runs the real environment doctor (read-only), then demonstrates how a missing optional
dependency is a warning and a missing required command is a blocker using the dependency
and command-registry result classes with synthetic findings.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_packaging import (
    DependencyCheck,
    DependencyCheckResult,
    DependencyFinding,
    DependencyKind,
    TesterEnvironmentDoctor,
)
from solaris_ai_nn.tester_packaging.command_registry_check import (
    CommandCheckResult,
    RegisteredCommand,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_doctor_demo")
    args = ap.parse_args()

    print("environment doctor demo")
    # 1. Real environment doctor (read-only).
    doc = TesterEnvironmentDoctor(
        tester_state_dir=args.tester_state_dir).check()
    print(f"  real environment doctor : {doc.overall_health} "
          f"(blockers {len(doc.blockers)})")
    print(f"  real dependency check   : passed="
          f"{DependencyCheck().check().passed}")

    # 2. Missing optional dependency -> warning.
    warn = DependencyCheckResult(python_ok=True)
    warn.findings.append(DependencyFinding(
        "psutil", DependencyKind.EXTERNAL_FEEDER_OPTIONAL, available=False))
    print(f"  missing optional dep    : passed={warn.passed} "
          f"(warnings {len(warn.warnings)})")

    # 3. Missing required command -> blocker.
    cmd = CommandCheckResult()
    cmd.commands.append(RegisteredCommand("tester-demo", required=True,
                                          registered=False))
    print(f"  missing required command: passed={cmd.passed} "
          f"(missing {cmd.missing_required})")
    print("note: the doctor is read-only -- it never auto-fixes, installs, runs "
          "shell, accesses the network, or opens a browser.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
