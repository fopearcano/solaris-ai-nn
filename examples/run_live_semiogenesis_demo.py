#!/usr/bin/env python3
"""Live semiogenesis demo: concepts -> private signs -> utility -> birth gate.

    python examples/run_live_semiogenesis_demo.py --state-dir .solaris_ai_nn_live/semio_demo

Sets up approved governance, a feeder registry, a (demo) birth certificate, and a
sample event stream; runs post-birth observation and first live ontogenesis to
produce stable proto-concepts; then runs the bounded first live semiogenesis runtime
and prints eligible-concept/sign-candidate counts, born private signs, the private-
syntax relation count, the sign-birth-gate status, and the recommended next phase.
No cognition is enabled; signs are private; Solaris never controls the source.
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


def main():
    parser = argparse.ArgumentParser(description="Live semiogenesis demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/semio_demo")
    parser.add_argument("--allow-limited-birth", action="store_true",
                        default=True, dest="allow_limited_birth")
    args = parser.parse_args()

    setup_state(args.state_dir)
    rt = FirstLiveSemiogenesisRuntime(
        state_dir=args.state_dir, allow_limited_birth=args.allow_limited_birth,
        operator_note="bounded first live semiogenesis (demo)")
    result = rt.run()
    st = rt.semiogenesis_status()

    print("=== First live semiogenesis demo ===")
    print(f"  run id              : {st['semiogenesis_run_id']}")
    print(f"  blocked             : {result['blocked']}")
    for b in result["blockers"]:
        print(f"    blocker           : {b}")
    print(f"  eligible concepts   : {st['live_eligible_concept_count']}")
    print(f"  sign candidates     : {st['live_sign_candidate_count']} (stable "
          f"{st['live_stable_sign_candidate_count']}, born "
          f"{st['live_born_sign_count']}, contaminated "
          f"{st['live_contaminated_sign_count']}, label-dependent "
          f"{st['live_label_dependent_sign_count']})")
    print(f"  private syntax rels : {st['live_private_syntax_relation_count']}")
    print(f"  sign utility mean   : {st['live_sign_utility_score_mean']}")
    print(f"  sign birth gate     : {st['live_sign_birth_gate_status']}")
    print(f"  recommended phase   : {st['recommended_next_phase']}")
    print(f"  sign memory         : {st['latest_sign_memory_path']}")
    print(f"  cognition / signs=lang : {st['enables_cognition']} / "
          f"{st['signs_are_language_understanding']}")
    print(f"  starts feeders/net  : {st['starts_feeders']} / "
          f"{st['accesses_network']}")
    print("note                  : operational live read-only semiogenesis. "
          "Private signs are internal reference structures; no cognition is "
          "enabled, no language is claimed, and no claim of consciousness, life, "
          "or agency is made.")


if __name__ == "__main__":
    main()
