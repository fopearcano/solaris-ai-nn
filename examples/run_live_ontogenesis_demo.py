#!/usr/bin/env python3
"""Live ontogenesis demo: feature extraction, recurrence, candidates, birth gate.

    python examples/run_live_ontogenesis_demo.py --state-dir .solaris_ai_nn_live/onto_demo

Sets up approved governance, a feeder registry, a (demo) birth certificate, and a
sample inbox of stable recurring patterns; runs the post-birth observation to produce
an observation stability gate; then runs the bounded first live ontogenesis runtime
and prints feature/recurrence/candidate counts, born proto-concepts, the birth-gate
status, and the recommended next phase. Nothing is learned; no semiogenesis is
enabled; Solaris never controls the source.
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

_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "live_ontogenesis")


def setup_state(state_dir: str, fixture: str) -> None:
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
    src = os.path.join(_FIXTURES, fixture)
    if os.path.isfile(src):
        shutil.copy(src, os.path.join(state_dir, "inbox", "ontogenesis.jsonl"))
    # Produce an observation stability gate for ontogenesis to consume.
    PostBirthLiveObservationRuntime(state_dir=state_dir).run()


def main():
    parser = argparse.ArgumentParser(description="Live ontogenesis demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/onto_demo")
    parser.add_argument("--fixture", type=str,
                        default="sample_stable_patterns.jsonl")
    parser.add_argument("--allow-limited-birth", action="store_true",
                        default=True, dest="allow_limited_birth")
    args = parser.parse_args()

    setup_state(args.state_dir, args.fixture)
    rt = FirstLiveOntogenesisRuntime(
        state_dir=args.state_dir, allow_limited_birth=args.allow_limited_birth,
        operator_note="bounded first live ontogenesis (demo)")
    result = rt.run()
    st = rt.ontogenesis_status()

    print("=== First live ontogenesis demo ===")
    print(f"  run id              : {st['ontogenesis_run_id']}")
    print(f"  blocked             : {result['blocked']}")
    for b in result["blockers"]:
        print(f"    blocker           : {b}")
    print(f"  accepted events     : {result['accepted_event_count']}")
    print(f"  feature vectors     : {st['live_feature_vector_count']}")
    print(f"  recurrence patterns : {st['live_recurrence_pattern_count']}")
    print(f"  candidates          : {st['live_candidate_count']} (stable "
          f"{st['live_stable_candidate_count']}, born "
          f"{st['live_born_proto_concept_count']}, contaminated "
          f"{st['live_contaminated_candidate_count']}, source-artifact "
          f"{st['live_source_artifact_candidate_count']})")
    print(f"  birth gate status   : {st['live_birth_gate_status']}")
    print(f"  recommended phase   : {st['recommended_next_phase']}")
    print(f"  concept memory      : {st['latest_concept_memory_path']}")
    print(f"  semiogenesis/action : {st['enables_semiogenesis']} / "
          f"{st['enables_action_reaction']}")
    print(f"  starts feeders/net  : {st['starts_feeders']} / "
          f"{st['accesses_network']}")
    print("note                  : operational live read-only ontogenesis. "
          "Proto-concepts are feature-stability records; nothing is learned, no "
          "semiogenesis is enabled, and no claim of consciousness, life, or "
          "agency is made.")


if __name__ == "__main__":
    main()
