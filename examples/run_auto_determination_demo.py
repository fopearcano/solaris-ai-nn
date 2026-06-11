#!/usr/bin/env python3
"""Auto-determination demo: Being / Not-Being as an operational metric.

    python examples/run_auto_determination_demo.py

Phase 1: healthy continuity (fresh heartbeat, clean checkpoints) -- Being
pressure dominates and the implication is "continue". Phase 2: trouble
(stale heartbeat, restart gap, critical incident, exhaustion) -- Not-Being
pressure rises and the engine recommends review, then safe shutdown. The
recommendation is data: only the ops supervisor/watchdog acts on stops.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.homeostasis import (
    HomeostasisQueryInterface,
    HomeostaticRegulator,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-determination demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/auto_det_demo")
    args = parser.parse_args()

    regulator = HomeostaticRegulator(state_dir=args.state_dir)
    now = time.time()

    print("=" * 70)
    print("Solaris-AI-NN -- auto-determination demo (operational metric)")
    print("=" * 70)
    print(f"{'phase':28s} {'being':>7s} {'not-being':>10s} "
          f"{'tension':>8s}  implication")
    scenarios = [
        ("healthy continuity", {
            "lifecycle": {"last_heartbeat_ts": now,
                          "last_checkpoint_ts": now},
            "telemetry": {"unexpected_deaths": 0,
                          "brain_death_gap_seconds": 0.0, "steps": 200},
            "health_level": "ok",
            "valence_events": [{"kind": "checkpoint_ok"}]}),
        ("stale heartbeat", {
            "lifecycle": {"last_heartbeat_ts": now - 120,
                          "last_checkpoint_ts": now - 60},
            "telemetry": {"unexpected_deaths": 0,
                          "brain_death_gap_seconds": 0.0, "steps": 400},
            "health_level": "warning"}),
        ("restart gap + warning", {
            "lifecycle": {"last_heartbeat_ts": now - 200,
                          "last_checkpoint_ts": now - 400},
            "telemetry": {"unexpected_deaths": 1,
                          "brain_death_gap_seconds": 45.0, "steps": 500},
            "health_level": "warning",
            "valence_events": [{"kind": "restart_gap"}]}),
        ("critical incident + exhaustion", {
            "lifecycle": {"last_heartbeat_ts": now - 300,
                          "last_checkpoint_ts": now - 900},
            "telemetry": {"unexpected_deaths": 2,
                          "brain_death_gap_seconds": 120.0, "steps": 600},
            "health_level": "critical", "critical_incident": True,
            "embodiment": {"energy": 0.5, "max_energy": 10.0,
                           "exhausted": True},
            "valence_events": [{"kind": "checkpoint_failed"}]}),
    ]
    for label, context in scenarios:
        result = regulator.update(context)
        tension = result.tension
        print(f"{label:28s} {tension.being_pressure:7.2f} "
              f"{tension.not_being_pressure:10.2f} "
              f"{tension.tension:8.2f}  {tension.action_implication}")
    print()
    auto = regulator.auto.state
    print(f"review recommendations:    {auto.review_recommendations}")
    print(f"shutdown recommendations:  {auto.shutdown_recommendations}")
    print()
    queries = HomeostasisQueryInterface(regulator)
    print("Q: what is the auto-determination state?")
    print(f"A: {queries.answer('what is the auto-determination state?').text}")
    print()
    print("Q: why did the system recommend safe shutdown?")
    print(f"A: {queries.answer('why did the system recommend safe shutdown?').text[:320]}")
    print()
    print(f"persisted: {args.state_dir}/auto_determination.json")
    regulator.save_state()


if __name__ == "__main__":
    main()
