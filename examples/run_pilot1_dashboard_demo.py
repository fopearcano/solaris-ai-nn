#!/usr/bin/env python3
"""Pilot-1 dashboard demo: mock observability -> dashboard.md / dashboard.json.

    python examples/run_pilot1_dashboard_demo.py --state-dir .solaris_ai_nn_pilot1/test_dashboard

Feeds a few mock observation events into the observability collector and
renders the text/Markdown/JSON health dashboard. No web server; no real run.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.pilot1 import (
    FailureModeDetector,
    PilotConfig,
    PilotHealthDashboard,
    PilotObservabilityCollector,
    ResourceBudgetMonitor,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pilot-1 dashboard demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot1/test_dashboard")
    args = parser.parse_args()

    cfg = PilotConfig(base_dir=args.state_dir)
    cfg.environment().ensure()
    obs = PilotObservabilityCollector(base_dir=args.state_dir)
    for i in range(5):
        obs.heartbeat()
        obs.observe(snapshot={"structural_change_score": 0.05 * i,
                              "proto_symbol_count": i,
                              "bus_message_count": 10 * i,
                              "uptime_ratio": 1.0})
    env = cfg.environment()
    resource = ResourceBudgetMonitor(
        state_dir=env.state_dir, artifact_dir=env.artifact_dir,
        log_dir=env.log_dir, report_dir=args.state_dir)
    resource.estimate()
    failure = FailureModeDetector()
    failure.detect(obs.latest)

    dash = PilotHealthDashboard(base_dir=args.state_dir)
    state = dash.build_state(observability=obs, resource=resource,
                             failure_detector=failure, config=cfg,
                             extra={"module_health": "ok",
                                    "developmental_epoch": "infancy"})
    paths = dash.write(state)

    print("=== Pilot-1 dashboard demo ===")
    print(f"events written : {obs.stream.count}")
    print(f"dashboard md   : {paths['markdown']}")
    print(f"dashboard json : {paths['json']}")
    print(f"exit rec       : {state.exit_recommendation}")


if __name__ == "__main__":
    main()
