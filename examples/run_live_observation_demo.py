#!/usr/bin/env python3
"""Live observation demo: bounded post-birth observation, no learning.

    python examples/run_live_observation_demo.py --state-dir .solaris_ai_nn_live/obs_demo

Sets up approved governance, a feeder registry, a (demo) birth certificate, and a
sample inbox, then runs the bounded post-birth live read-only observation runtime
and prints the window count, source health/diet summary, load (overload/deprivation)
status, the report-only metabolism calibration confidence, and the advisory
stability decision with its recommended next phase. Nothing is learned; Solaris
never controls the source.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime

_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "live_observation")


def setup_state(state_dir: str, fixture: str) -> None:
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state_dir, sub), exist_ok=True)
    with open(os.path.join(state_dir, "governance",
                           "LIVE_READONLY_GOVERNANCE.json"), "w") as fh:
        json.dump(approved_governance(), fh)
    with open(os.path.join(state_dir, "feeders", "FEEDER_REGISTRY.json"),
              "w") as fh:
        json.dump(feeder_registry_template(), fh)
    cert = os.path.join(state_dir, "certificates", "BIRTH_CERTIFICATE_demo.md")
    if not os.path.isfile(cert):
        with open(cert, "w") as fh:
            fh.write("# Birth certificate (demo)\n\n_Operational, not biological._\n")
    src = os.path.join(_FIXTURES, fixture)
    if os.path.isfile(src):
        shutil.copy(src, os.path.join(state_dir, "inbox", "observation.jsonl"))


def main():
    parser = argparse.ArgumentParser(description="Live observation demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/obs_demo")
    parser.add_argument("--fixture", type=str,
                        default="sample_observation_events.jsonl")
    parser.add_argument("--observation-window-minutes", type=int, default=30,
                        dest="observation_window_minutes")
    args = parser.parse_args()

    setup_state(args.state_dir, args.fixture)
    rt = PostBirthLiveObservationRuntime(
        state_dir=args.state_dir,
        observation_window_minutes=args.observation_window_minutes,
        operator_note="bounded post-birth live observation (demo)")
    result = rt.run()
    st = rt.observation_status()

    print("=== Post-birth live observation demo ===")
    print(f"  run id              : {st['observation_run_id']}")
    print(f"  blocked             : {result['blocked']}")
    print(f"  observation windows : {st['live_observation_window_count']}")
    print(f"  accepted events     : "
          f"{st['live_observation_accepted_event_count']}")
    print(f"  quarantine rate     : "
          f"{st['live_observation_quarantine_rate']:.0%}")
    print(f"  sources             : {st['live_healthy_source_count']} healthy / "
          f"{st['live_source_count']} total")
    print(f"  source diet balance : {st['live_source_diet_balance']}")
    print(f"  load status         : {st['live_load_status']}")
    print(f"  metabolism conf.    : {st['metabolism_calibration_confidence']}")
    print(f"  stability status    : {st['live_stability_status']}")
    print(f"  recommended phase   : {st['live_recommended_next_phase']}")
    print(f"  first-day record    : {st['first_day_record_path']}")
    print(f"  observation report  : {st['latest_observation_report_path']}")
    print(f"  learns / starts feed: {st['learns']} / {st['starts_feeders']}")
    print("  next recommended phases (not executed):")
    for p in rt.next_phase_recommendations():
        print(f"    - {p['phase']}: {p['detail']}")
    print("note                  : this is operational live read-only "
          "observation. Nothing is learned, no concept is formed, and no claim "
          "of consciousness, life, or agency is made.")


if __name__ == "__main__":
    main()
