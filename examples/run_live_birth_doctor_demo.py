#!/usr/bin/env python3
"""Live birth doctor demo: missing/SAFE-OFF blocker, approved pass, forbidden block.

    python examples/run_live_birth_doctor_demo.py --state-dir .solaris_ai_nn_live/test_doctor

Runs the live doctor in three situations: a SAFE-OFF governance (disabled/
unapproved -> blocked), an operator-approved governance (-> pass), and a governance
that places a forbidden source in allowed_sources (-> blocked). The doctor is
read-only; it never starts feeders or accesses the network.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_birth import (
    LiveReadOnlyBirthRuntime,
    approved_governance,
    feeder_registry_template,
    governance_template,
)


def _write_gov(state_dir, gov):
    os.makedirs(os.path.join(state_dir, "governance"), exist_ok=True)
    os.makedirs(os.path.join(state_dir, "feeders"), exist_ok=True)
    with open(os.path.join(state_dir, "governance",
                           "LIVE_READONLY_GOVERNANCE.json"), "w") as fh:
        json.dump(gov, fh)
    with open(os.path.join(state_dir, "feeders", "FEEDER_REGISTRY.json"),
              "w") as fh:
        json.dump(feeder_registry_template(), fh)


def _doctor(label, state_dir, gov):
    LiveReadOnlyBirthRuntime(state_dir=state_dir).initialize()
    _write_gov(state_dir, gov)
    summary = LiveReadOnlyBirthRuntime(state_dir=state_dir).run_doctor()
    print(f"  {label}: governance={summary['governance_status']} "
          f"passed={summary['governance_passed']}")
    for b in summary["blockers"]:
        print(f"      blocker: {b}")


def main():
    parser = argparse.ArgumentParser(description="Live birth doctor demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/test_doctor")
    args = parser.parse_args()

    print("=== Live birth doctor demo ===")
    _doctor("SAFE-OFF governance", os.path.join(args.state_dir, "off"),
            governance_template())
    _doctor("operator-approved governance", os.path.join(args.state_dir, "ok"),
            approved_governance())
    forbidden = approved_governance()
    forbidden["allowed_sources"] = forbidden["allowed_sources"] + ["raw_camera"]
    _doctor("forbidden source in allowed", os.path.join(args.state_dir, "bad"),
            forbidden)
    print("note: the doctor is read-only; it never starts feeders, accesses the "
          "network, runs a shell, or calls Git/GitHub.")


if __name__ == "__main__":
    main()
