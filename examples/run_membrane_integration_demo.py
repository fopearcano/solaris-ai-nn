#!/usr/bin/env python3
"""Membrane integration demo: load impressions, build ancestry, audit a clean pipeline.

    python examples/run_membrane_integration_demo.py --state-dir .solaris_ai_nn_live/integ_demo

Stages a clean membrane pipeline (impressions + proto-concept/sign/cognition referencing
impression ancestry) into a state dir, runs the membrane integration runtime, and
prints ancestry, bypass findings, and the pipeline-audit status. Raw events remain
audit material; downstream artifacts should preserve impression ancestry.
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

from solaris_ai_nn.membrane_integration import MembraneIntegrationRuntime

_FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "membrane_integration", "sample_membrane_pipeline")


def stage_pipeline(state_dir: str, *, include_bypass: bool = False) -> None:
    """Stage membrane impressions + downstream memories into the state dir."""
    def _w(rel, src):
        path = os.path.join(state_dir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        shutil.copy(os.path.join(_FIX, src), path)

    _w("membrane/impressions/SENSORY_IMPRESSIONS.jsonl",
       "sensory_impressions.jsonl")
    os.makedirs(os.path.join(state_dir, "membrane", "reports"), exist_ok=True)
    with open(os.path.join(state_dir, "membrane", "reports",
                           "ENVIRONMENTAL_MEMBRANE_REPORT.json"), "w") as fh:
        json.dump({"sections": {}}, fh)
    concept = "bypass_concept.json" if include_bypass else "proto_concept.json"
    _w("ontogenesis/concepts/LIVE_CONCEPT_MEMORY.json", concept)
    _w("semiogenesis/signs/LIVE_SIGN_MEMORY.json", "sign_record.json")
    _w("cognition/traces/LIVE_COGNITION_MEMORY.json", "cognition_trace.json")


def main():
    parser = argparse.ArgumentParser(description="Membrane integration demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/integ_demo")
    args = parser.parse_args()

    stage_pipeline(args.state_dir)
    rt = MembraneIntegrationRuntime(args.state_dir, require_membrane=True,
                                    require_impressions=True)
    rt.run()
    st = rt.integration_status()

    print("=== Membrane integration demo ===")
    print(f"  run id              : {st['integration_run_id']}")
    print(f"  blocked             : {st['integration_blocked']}")
    print(f"  membrane present    : {st['membrane_present']}; impressions: "
          f"{st['impression_count']}")
    print(f"  ancestry chains     : {st['ancestry_chain_count']} (with "
          f"impression ancestry {st['with_impression_ancestry']}, missing "
          f"{st['missing_ancestry']})")
    print(f"  bypass findings     : {st['bypass_finding_count']} (critical "
          f"{st['critical_bypass_count']})")
    print(f"  pipeline status     : {st['pipeline_status']}")
    print(f"  recommended action  : {rt.recommended_next_action()}")
    print(f"  starts feeders/net  : {st['starts_feeders']} / "
          f"{st['accesses_network']}")
    print("note                  : membrane integration is an architectural "
          "audit/enforcement layer. Raw events remain audit material; downstream "
          "modules consume sensory impressions. No consciousness/life/agency "
          "claim is made.")


if __name__ == "__main__":
    main()
