#!/usr/bin/env python3
"""Conscience integration health-check demo.

    python examples/run_conscience_health_check.py

Initializes the ``full_developmental_short`` profile, runs a few steps, and
prints the integration health report: whether the spine, bus, registry,
lifecycle, scheduler, and safety invariants are healthy, partial, degraded,
or failed. This is a read-only inspector; it actuates nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.conscience import (
    ConscienceOrchestrator,
    IntegrationHealthMonitor,
    ScenarioProfileRegistry,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Conscience health check")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/conscience_health")
    parser.add_argument("--profile", type=str,
                        default="full_developmental_short")
    parser.add_argument("--steps", type=int, default=20)
    args = parser.parse_args()

    profile = ScenarioProfileRegistry().require(args.profile)
    profile.run_context.state_dir = args.state_dir

    orch = ConscienceOrchestrator(governance_approved=True)
    orch.configure(profile)
    orch.initialize()
    for _ in range(min(args.steps, orch.context.max_steps or args.steps)):
        orch.step()

    report = IntegrationHealthMonitor().check(orch)
    print("=== conscience integration health ===")
    print(f"profile : {args.profile}")
    print(f"overall : {report.overall}")
    for check in report.checks:
        print(f"  - {check.name:<10} {check.status:<8} {check.detail}")
    if report.warnings:
        print(f"warnings: {json.dumps(report.warnings)}")
    else:
        print("warnings: none")


if __name__ == "__main__":
    main()
