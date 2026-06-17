#!/usr/bin/env python3
"""Live stability-gate demo: an advisory readiness decision (never an action).

    python examples/run_live_stability_gate_demo.py --state-dir .solaris_ai_nn_live/gate_demo --fixture sample_overload_events.jsonl

Runs the bounded post-birth observation and prints the advisory stability gate:
the readiness status, any blockers and the correction to make first, warnings, and
the recommended next phase. The gate is advisory only -- it starts no phase, changes
no feeder, and enables no learning. A blocked gate is a normal, healthy outcome of
the first hours of observation. Try the overload / deprivation fixtures to see the
gate block.
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
    parser = argparse.ArgumentParser(description="Live stability-gate demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/gate_demo")
    parser.add_argument("--fixture", type=str,
                        default="sample_observation_events.jsonl")
    args = parser.parse_args()

    setup_state(args.state_dir, args.fixture)
    rt = PostBirthLiveObservationRuntime(state_dir=args.state_dir)
    rt.run()
    g = rt.stability

    print("=== Live stability-gate demo (advisory only) ===")
    print(f"  status              : {g.get('live_stability_status')}")
    print(f"  blocked             : {g.get('blocked')}")
    print(f"  ready for metabolism: "
          f"{g.get('ready_for_metabolism_calibration')}")
    print(f"  recommended phase   : {g.get('recommended_next_phase')}")
    print(f"  starts phase / feed : {g.get('starts_any_phase')} / "
          f"{g.get('changes_feeders')} / enables learning "
          f"{g.get('enables_learning')}")
    if g.get("blockers"):
        print("  blockers (with the correction to make first):")
        for b in g["blockers"]:
            print(f"    - {b['blocker']}: {b['detail']}")
            print(f"        -> correct: {b['correction']}")
    if g.get("warnings"):
        print("  warnings:")
        for w in g["warnings"]:
            print(f"    - {w}")
    print("note : the stability gate is advisory only; it starts no phase, "
          "changes no feeder, and enables no learning. A blocked gate is a "
          "normal, healthy early-observation outcome, not a failure or a claim.")


if __name__ == "__main__":
    main()
