#!/usr/bin/env python3
"""Drift recovery demo: stabilize runaway drift, leave adaptation alone.

    python examples/run_drift_recovery_demo.py

Shows the drift recovery classifier on three reports: healthy adaptation (no
repair), runaway drift (stabilization + rollback proposal), and unknown
drift (stabilize and request review). The stabilization proposal becomes a
safe executive ActionCandidate; nothing acts in the real world.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.autoregeneration import (
    AutoRegenerationEngine,
    AutoRegenerationReportBuilder,
    DriftRecoveryManager,
    RepairPolicy,
)
from solaris_ai_nn.autoregeneration.repair_actions import repair_to_candidate


def main() -> None:
    parser = argparse.ArgumentParser(description="Drift recovery demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/drift_recovery")
    args = parser.parse_args()

    mgr = DriftRecoveryManager()
    healthy = mgr.propose({"drift": {"classification": "healthy_slow"}})
    runaway_ctx = {"drift": {"classification": "fast_warning",
                             "drift_velocity": 3.0}}
    runaway = mgr.propose(runaway_ctx)
    unknown = mgr.propose({"drift": {}})

    print("=" * 70)
    print("Solaris-AI-NN -- drift recovery (stabilize runaway, keep "
          "adaptation)")
    print("=" * 70)
    print(f"healthy adaptation -> {len(healthy)} repair(s) "
          f"(adaptation is not repaired away)")
    print(f"runaway drift      -> {[a.action_type for a in runaway]}")
    print(f"unknown drift      -> {[a.action_type for a in unknown]}")
    # The stabilization proposal becomes a safe executive candidate.
    if runaway:
        candidate = repair_to_candidate(runaway[0])
        print(f"as executive candidate: label={candidate.label!r} "
              f"scope={candidate.executable_scope} "
              f"committed={candidate.committed}")
    print()

    engine = AutoRegenerationEngine(
        state_dir=args.state_dir, policy=RepairPolicy(mode="safe_auto_repair"))
    engine.tick({"drift": runaway_ctx["drift"], "mysterium_pressure": 0.5,
                 "state_dir": args.state_dir})
    builder = AutoRegenerationReportBuilder(engine)
    paths = builder.save(Path(args.state_dir) / "report.json",
                         Path(args.state_dir) / "report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: healthy adaptation is not erased as if all drift were bad; "
          "runaway drift is stabilized (and the last plasticity update may "
          "be rolled back); uncertain drift prefers stabilization and a "
          "review request.")


if __name__ == "__main__":
    main()
