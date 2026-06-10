#!/usr/bin/env python3
"""Health monitoring demo: a short run plus one simulated warning.

Runs a bounded session, takes a clean health reading, then intentionally
simulates a stale-heartbeat condition so the warning path (health report +
incident log) is demonstrated end to end -- finishing safely.
"""

from __future__ import annotations

import os
import sys
import time

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.ops import HealthMonitor, IncidentLog
from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner

STATE_DIR = ".solaris_ai_nn_state/healthcheck_demo"
OPS_DIR = ".solaris_ai_nn_ops/healthcheck_demo"


def main() -> None:
    runner = ContinuousRunner(state_dir=STATE_DIR, max_steps=60,
                              checkpoint_interval_steps=30, seed=7)
    runner.run()
    monitor = HealthMonitor()
    incidents = IncidentLog(os.path.join(OPS_DIR, "incidents.jsonl"),
                            run_id=runner.run_id, session_id=runner.session_id)

    base = {
        "now": time.time(),
        "lifecycle": runner.lifecycle.snapshot() | {
            "alive": True, "last_checkpoint_ts": runner._last_checkpoint_ts},
        "telemetry": runner.telemetry.report(),
        "substrate": runner.bridge.substrate.metrics().to_dict(),
        "state_dir": STATE_DIR,
    }
    clean = monitor.check(base)
    print("=" * 70)
    print("Solaris-AI-NN -- healthcheck demo")
    print("=" * 70)
    print(f"clean reading:  level={clean.level} "
          f"({len(clean.checks)} checks, {len(clean.issues())} issues)")

    # Intentionally simulate ONE warning condition: a stale heartbeat.
    stale = dict(base)
    stale["lifecycle"] = dict(base["lifecycle"])
    stale["lifecycle"]["last_heartbeat_ts"] = time.time() - 120.0
    stale["expect_progress"] = False  # no new steps ran; that's expected here
    report = monitor.check(stale)
    print(f"simulated stale heartbeat: level={report.level}")
    for issue in report.issues():
        print(f"  [{issue.status}] {issue.domain}/{issue.name}: {issue.detail}")
        incidents.record("health_warning", "warning", issue.detail,
                         related_metric=f"{issue.domain}/{issue.name}",
                         suggested_debug_step="verify the loop is advancing "
                                              "and heartbeats are emitted")
    print("-" * 70)
    print(f"incidents logged: {len(incidents.list_incidents())} "
          f"-> {incidents.path}")
    print(report.to_markdown())
    print("-" * 70)
    print("The warning was SIMULATED for demonstration; the run itself was")
    print("healthy and finished safely.")
    incidents.close()


if __name__ == "__main__":
    main()
