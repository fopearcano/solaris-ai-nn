#!/usr/bin/env python3
"""Live cognition demo: signs -> traces -> anticipations -> prediction assessment.

    python examples/run_live_cognition_demo.py --state-dir .solaris_ai_nn_live/cog_demo

Sets up governance, a feeder registry, a (demo) birth certificate, and a sample event
stream; runs observation, ontogenesis, and semiogenesis to produce stable private
signs; then runs the bounded first live cognition runtime and prints eligible-sign /
trace counts, anticipations, internal simulations, prediction assessment, mean
uncertainty, and the readiness-gate status. No action is enabled; signs are private;
Solaris never controls the source.
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
from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime
from solaris_ai_nn.live_semiogenesis import FirstLiveSemiogenesisRuntime
from solaris_ai_nn.live_cognition import FirstLiveCognitionRuntime

_ONTO_FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "live_ontogenesis", "sample_stable_patterns.jsonl")


def setup_state(state_dir: str) -> None:
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state_dir, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state_dir, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state_dir, "feeders", "FEEDER_REGISTRY.json"), "w"))
    cert = os.path.join(state_dir, "certificates", "BIRTH_CERTIFICATE_demo.md")
    if not os.path.isfile(cert):
        with open(cert, "w") as fh:
            fh.write("# Birth certificate (demo)\n\n_Operational, not biological._\n")
    if os.path.isfile(_ONTO_FIXTURE):
        shutil.copy(_ONTO_FIXTURE, os.path.join(state_dir, "inbox", "ev.jsonl"))
    PostBirthLiveObservationRuntime(state_dir=state_dir).run()
    FirstLiveOntogenesisRuntime(state_dir=state_dir,
                                allow_limited_birth=True).run()
    FirstLiveSemiogenesisRuntime(state_dir=state_dir,
                                 allow_limited_birth=True).run()


def main():
    parser = argparse.ArgumentParser(description="Live cognition demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/cog_demo")
    parser.add_argument("--profile", type=str,
                        default="live_cognition_anticipation_limited_v0")
    args = parser.parse_args()

    setup_state(args.state_dir)
    rt = FirstLiveCognitionRuntime(
        state_dir=args.state_dir, profile=args.profile,
        operator_note="bounded first live cognition (demo)")
    result = rt.run()
    st = rt.cognition_status()

    print("=== First live cognition demo ===")
    print(f"  run id              : {st['cognition_run_id']}")
    print(f"  blocked             : {result['blocked']}")
    for b in result["blockers"]:
        print(f"    blocker           : {b}")
    print(f"  eligible signs      : {st['live_eligible_sign_count']}")
    print(f"  cognition traces    : {st['live_cognition_trace_count']} (active "
          f"{st['live_active_trace_count']}, useful "
          f"{st['live_useful_trace_count']}, contaminated "
          f"{st['live_contaminated_trace_count']})")
    print(f"  anticipations       : {st['live_anticipation_count']}")
    print(f"  internal simulations: {st['live_internal_simulation_count']}")
    print(f"  prediction assess   : {st['live_prediction_assessment_count']} "
          f"(matched {st['live_prediction_matched_count']}, contradicted "
          f"{st['live_prediction_contradicted_count']})")
    print(f"  mean uncertainty    : {st['live_uncertainty_mean']}")
    print(f"  readiness gate      : {st['live_cognition_readiness_status']}")
    print(f"  recommended phase   : {st['recommended_next_phase']}")
    print(f"  cognition memory    : {st['latest_cognition_memory_path']}")
    print(f"  enables action / signs=lang / traces=reasoning : "
          f"{st['enables_action']} / {st['signs_are_language_understanding']} / "
          f"{st['traces_prove_reasoning']}")
    print("note                  : operational live read-only cognition. "
          "Cognition traces are sign-based anticipation/relation records; no "
          "action is enabled, no reasoning/language/understanding is claimed, "
          "and no claim of consciousness, life, or agency is made.")


if __name__ == "__main__":
    main()
