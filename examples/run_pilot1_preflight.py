#!/usr/bin/env python3
"""Pilot-1 preflight demo: health, governance, safety, and directory checks.

    python examples/run_pilot1_preflight.py --state-dir .solaris_ai_nn_pilot1/test_preflight

Runs the bounded preflight checks that must pass before any soak: pilot-safety
validation, the governance pilot scope, module availability, and that the
pilot directories exist. Writes a preflight report. It starts no run.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.conscience import ConscienceModuleRegistry
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.pilot1 import (
    PilotConfig,
    PilotMode,
    PilotProtocol,
    PilotSafetyValidator,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pilot-1 preflight")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot1/test_preflight")
    args = parser.parse_args()

    cfg = PilotConfig(mode=PilotMode.PLAN_ONLY, base_dir=args.state_dir)
    cfg.environment().ensure()
    safety = PilotSafetyValidator()
    gov = GovernancePolicy()
    registry = ConscienceModuleRegistry().detect(cfg.enabled_modules())

    checks = {
        "config_safe": safety.validate_config(cfg).safe,
        "pilot1_enabled": gov.is_enabled("enable_pilot1"),
        "emergency_stop_intact":
            safety.validate_emergency_stop_intact(False).safe,
        "directories_exist": all(os.path.isdir(d)
                                 for d in cfg.environment().all_dirs()),
        "core_modules_available": "governance" in registry.available(),
    }
    passed = all(checks.values())

    protocol = PilotProtocol(config=cfg, governance=gov)
    protocol.enter_phase("preflight")
    protocol.complete_phase("preflight", passed,
                            detail="preflight checks executed")

    report = {"pilot_id": cfg.pilot_id, "checks": checks, "passed": passed,
              "missing_modules": registry.missing()}
    report_path = os.path.join(args.state_dir, "preflight_report.json")
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)

    print("=== Pilot-1 preflight ===")
    for name, ok in checks.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print(f"preflight passed: {passed}")
    print(f"report          : {report_path}")


if __name__ == "__main__":
    main()
