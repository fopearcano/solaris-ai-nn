#!/usr/bin/env python3
"""Minimal conscience-spine demo: one bounded end-to-end run.

    python examples/run_conscience_minimal_demo.py

Runs the ``minimal_smoke`` scenario profile through the unified conscience
orchestrator: the smallest spine that still goes Stimulus -> Push -> Desire
-> ActionCandidate/ActionSuggestion -> Reaction -> Memory/.../Inner MAP. The
run is bounded, simulation-only, and never actuates the real world; no module
is sovereign.
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
    parser = argparse.ArgumentParser(description="Minimal conscience demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/conscience_minimal")
    parser.add_argument("--steps", type=int, default=12)
    args = parser.parse_args()

    profile = ScenarioProfileRegistry().require("minimal_smoke")
    profile.run_context.state_dir = args.state_dir
    profile.run_context.max_steps = args.steps

    orch = ConscienceOrchestrator()
    orch.configure(profile)
    orch.initialize()
    orch.run()

    health = IntegrationHealthMonitor().check(orch)
    summary = orch.summary()
    print("=== minimal conscience run ===")
    print(f"profile      : {summary['profile']}")
    print(f"mode         : {summary['mode']} ({summary['authority']})")
    print(f"steps        : {summary['step_count']}")
    print(f"enabled      : {summary['enabled_modules']}")
    print(f"bus messages : {summary['bus_message_count']}")
    print(f"phase counts : {json.dumps(summary['counts'])}")
    print(f"integration  : {health.overall}")
    print(f"note         : {summary['authority_note']}")


if __name__ == "__main__":
    main()
