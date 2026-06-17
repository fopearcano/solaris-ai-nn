#!/usr/bin/env python3
"""Membrane pipeline audit demo: pass, pass-with-warnings, blocked, fallback.

    python examples/run_membrane_pipeline_audit_demo.py --state-dir .solaris_ai_nn_live/audit_demo

Runs the pipeline audit for a clean pipeline (pass) and a missing-ancestry pipeline in
strict mode (blocked), and prints each stage's status.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.membrane_integration import MembraneIntegrationRuntime
from run_membrane_integration_demo import stage_pipeline


def _audit(state_dir, include_bypass, profile):
    stage_pipeline(state_dir, include_bypass=include_bypass)
    rt = MembraneIntegrationRuntime(state_dir, profile=profile)
    rt.run()
    return rt


def main():
    parser = argparse.ArgumentParser(
        description="Membrane pipeline audit demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/audit_demo")
    args = parser.parse_args()

    print("=== Membrane pipeline audit demo ===")
    clean = _audit(args.state_dir + "/clean", False, "live_integration_audit_v0")
    print(f"  clean pipeline overall : {clean.audit.overall_status}")
    blocked = _audit(args.state_dir + "/blocked", True,
                     "live_integration_enforced_v0")
    print(f"  bypass pipeline overall: {blocked.audit.overall_status}")
    for stg in blocked.audit.to_dict()["stages"]:
        print(f"    - {stg['stage']}: {stg['status']}")
    print("note: the audit walks the live perceptual pipeline stage by stage; "
          "fallback, missing artifacts, and bypasses are all visible.")


if __name__ == "__main__":
    main()
