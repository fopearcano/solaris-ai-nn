#!/usr/bin/env python3
"""Full developmental short demo: every module in one bounded run.

    python examples/run_full_developmental_short_demo.py

Wires all available modules into a single bounded developmental run via the
``full_developmental_short`` scenario profile, then writes a claim-guarded
full-system report. This profile is governed (opt-in); the demo acknowledges
the governance scope explicitly. The run is simulation-only and bounded, and
no module bypasses executive, safety, or governance.
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
    FullSystemReportBuilder,
    IntegrationHealthMonitor,
    ScenarioProfileRegistry,
)
from solaris_ai_nn.evaluation import metrics as M


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Full developmental short demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/conscience_full")
    parser.add_argument("--output-dir", type=str,
                        default=".solaris_ai_nn_state/conscience_full/reports")
    args = parser.parse_args()

    profile = ScenarioProfileRegistry().require("full_developmental_short")
    profile.run_context.state_dir = args.state_dir
    profile.run_context.artifact_dir = args.output_dir

    # The full-developmental-short profile is governed; acknowledge it.
    orch = ConscienceOrchestrator(governance_approved=True)
    orch.configure(profile)
    orch.initialize()
    orch.run()

    monitor = IntegrationHealthMonitor()
    metrics = M.conscience_metrics(orch.snapshot() | orch.summary())
    report = FullSystemReportBuilder().build_and_write(
        orch, monitor, metrics=metrics, artifact_dir=args.output_dir)

    summary = orch.summary()
    print("=== full developmental short run ===")
    print(f"steps         : {summary['step_count']}")
    print(f"enabled       : {summary['enabled_modules']}")
    print(f"degraded      : {summary['degraded_modules']}")
    print(f"success rate  : {metrics['module_success_rate']}")
    print(f"phase count   : {metrics['spine_phase_count']}")
    print(f"safety viol.  : {metrics['safety_violation_count']}")
    print(f"integration   : {monitor.history[-1].overall}")
    print(f"claim-guarded : safe={report.claim_guard_safe} "
          f"(findings={report.claim_guard_findings})")
    print(f"report        : {report.sections.get('report_paths')}")
    print("note          : bounded, simulation-only; no module is sovereign")


if __name__ == "__main__":
    main()
