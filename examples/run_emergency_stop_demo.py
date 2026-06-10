#!/usr/bin/env python3
"""Demonstrate the emergency stop sentinel during a supervised run.

    python examples/run_emergency_stop_demo.py

A bounded supervised run starts; after the second segment an "operator"
creates the sentinel file ``<state_dir>/EMERGENCY_STOP`` (simulated here by a
wrapped runner factory -- the file is created from outside the runner). The
supervisor notices the sentinel at the next segment boundary, records an
incident and governance audit events, and performs a safe shutdown. The
process is never killed.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.governance import sentinel_path
from solaris_ai_nn.ops import OperationalRunManifest, OperationalSupervisor
from solaris_ai_nn.ops.supervisor import default_runner_factory


def main() -> None:
    parser = argparse.ArgumentParser(description="Emergency stop demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/emergency_demo")
    parser.add_argument("--artifact-dir", type=str, default=".solaris_ai_nn_ops")
    parser.add_argument("--governance-dir", type=str,
                        default=".solaris_ai_nn_governance")
    args = parser.parse_args()

    manifest = OperationalRunManifest(
        mode="bounded", max_steps=200, healthcheck_interval_steps=40,
        state_dir=args.state_dir, artifact_dir=args.artifact_dir,
        operator_notes="emergency stop demo")

    segments = {"n": 0}

    def factory(m, steps):
        segments["n"] += 1
        if segments["n"] == 2:
            # The "operator" pulls the cord mid-run: create the sentinel.
            sentinel = sentinel_path(m.state_dir)
            sentinel.parent.mkdir(parents=True, exist_ok=True)
            sentinel.write_text('{"reason": "demo: operator requested stop"}',
                                encoding="utf-8")
            print(f"[operator] sentinel created: {sentinel}")
        return default_runner_factory(m, steps)

    supervisor = OperationalSupervisor(
        manifest=manifest, runner_factory=factory,
        governance_dir=args.governance_dir)
    status = supervisor.run()

    governance = status.get("governance") or {}
    print("=" * 70)
    print("Solaris-AI-NN -- emergency stop demo")
    print("=" * 70)
    print(f"segments run:        {supervisor._segments_run} "
          f"(of {manifest.max_steps // manifest.healthcheck_interval_steps} "
          "planned)")
    print(f"emergency requested: {governance.get('emergency_stop_requested')}")
    print(f"shutdown graceful:   "
          f"{supervisor.registry.latest_run()['graceful_shutdown']}")
    print("incidents:")
    for row in status["incidents"]:
        print(f"  [{row['severity']}] {row['type']}: {row['message'][:70]}")
    print("governance audit (emergency rows):")
    for row in supervisor.gov_audit.read_all():
        if "emergency" in row["event_type"]:
            print(f"  {row['event_type']}: {row['reason'][:70]}")
    print(f"final checkpoint:    {manifest.state_dir}/latest_checkpoint.json")
    print(f"shutdown evidence:   {supervisor.ops_dir}/shutdown.json")
    # The sentinel stays until the operator clears it deliberately.
    cleared = supervisor.emergency.clear_sentinel()
    print(f"sentinel cleared after review: {cleared}")


if __name__ == "__main__":
    main()
