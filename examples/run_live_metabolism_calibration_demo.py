#!/usr/bin/env python3
"""Live metabolism-calibration demo: report-only threshold recommendations.

    python examples/run_live_metabolism_calibration_demo.py --state-dir .solaris_ai_nn_live/metab_demo

Runs the bounded post-birth observation and prints the report-only perceptual
metabolism calibration: recommended thresholds (max event rate, max payload, novelty
pressure, repetition / silence tolerance, quarantine / overload / deprivation
thresholds) and per-signal weights (operator pulse, human text, debug gloss, scalar,
absence). Nothing is applied: no feeder, governance, configuration, or learning
state is written or changed. This is descriptive metabolism, not understanding.
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
    json.dump(approved_governance(), open(os.path.join(
        state_dir, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state_dir, "feeders", "FEEDER_REGISTRY.json"), "w"))
    open(os.path.join(state_dir, "certificates", "BIRTH_CERTIFICATE_demo.md"),
         "w").write("# Birth certificate (demo)\n")
    src = os.path.join(_FIXTURES, fixture)
    if os.path.isfile(src):
        shutil.copy(src, os.path.join(state_dir, "inbox", "observation.jsonl"))


def main():
    parser = argparse.ArgumentParser(
        description="Live metabolism-calibration demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/metab_demo")
    parser.add_argument("--fixture", type=str,
                        default="sample_observation_events.jsonl")
    parser.add_argument("--profile", type=str,
                        default="first_day_metabolism_24h_v0")
    args = parser.parse_args()

    setup_state(args.state_dir, args.fixture)
    rt = PostBirthLiveObservationRuntime(state_dir=args.state_dir,
                                         profile=args.profile)
    rt.run()
    m = rt.metabolism

    print("=== Live perceptual metabolism calibration demo (report-only) ===")
    print(f"  confidence          : {m.get('calibration_confidence')}")
    print(f"  recommendations     : {m.get('recommendation_count', 0)} "
          f"(applied={m.get('applied')})")
    print("  recommended thresholds:")
    for rec in m.get("recommendations", []):
        unit = f" {rec['unit']}" if rec.get("unit") else ""
        print(f"    - {rec['name']:<32} {rec['recommended_value']}{unit}")
    print("  per-signal weights:")
    for name, weight in m.get("source_weights", {}).items():
        print(f"    - {name:<20} {weight}")
    if m.get("findings"):
        print("  findings:")
        for f in m["findings"]:
            print(f"    - {f}")
    print("note : all thresholds are report-only and are NOT applied; no feeder, "
          "governance, configuration, or learning state is written or changed. "
          "This is descriptive metabolism, not understanding.")


if __name__ == "__main__":
    main()
