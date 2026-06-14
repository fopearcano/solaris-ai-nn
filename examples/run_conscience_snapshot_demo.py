#!/usr/bin/env python3
"""Conscience snapshot demo: one consistent, persisted runtime picture.

    python examples/run_conscience_snapshot_demo.py

Runs a few steps of the ``nursery_short`` profile, builds one consistent
snapshot of the whole runtime (context, spine, bus, registry, lifecycle,
scheduler, safety, and integration health), and persists it to JSON under the
state directory. Snapshots make long, bounded runs inspectable and auditable.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.conscience import (
    ConscienceOrchestrator,
    IntegrationHealthMonitor,
    ScenarioProfileRegistry,
    SnapshotBuilder,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Conscience snapshot demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/conscience_snapshot")
    parser.add_argument("--profile", type=str, default="nursery_short")
    parser.add_argument("--steps", type=int, default=20)
    args = parser.parse_args()

    profile = ScenarioProfileRegistry().require(args.profile)
    profile.run_context.state_dir = args.state_dir

    orch = ConscienceOrchestrator(governance_approved=True)
    orch.configure(profile)
    orch.initialize()
    for _ in range(min(args.steps, orch.context.max_steps or args.steps)):
        orch.step()

    builder = SnapshotBuilder(state_dir=args.state_dir)
    monitor = IntegrationHealthMonitor()
    snap = builder.build_and_persist(orch, monitor, args.state_dir)

    print("=== conscience snapshot ===")
    print(f"snapshot id : {snap.snapshot_id}")
    print(f"run id      : {snap.run_id}")
    print(f"step        : {snap.step}")
    print(f"path        : {snap.payload.get('snapshot_path')}")
    health = snap.payload.get("integration_health") or {}
    print(f"integration : {health.get('overall', 'unknown')}")
    print("note        : a snapshot is a read-only picture; it actuates "
          "nothing")


if __name__ == "__main__":
    main()
