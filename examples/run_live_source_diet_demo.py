#!/usr/bin/env python3
"""Live source-diet demo: the balance of the live field (read-only).

    python examples/run_live_source_diet_demo.py --state-dir .solaris_ai_nn_live/diet_demo

Runs the bounded post-birth observation and prints the source diet: per-source
proportions, the dominance score, the operator-pulse and human-text proportions, and
the overall balance verdict. No source should silently dominate; the operator pulse
is stimulus, not the primary source; human text must not become the primary
ontology. Recommendations are report-only; nothing is learned.
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
    parser = argparse.ArgumentParser(description="Live source-diet demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/diet_demo")
    parser.add_argument("--fixture", type=str,
                        default="sample_observation_events.jsonl")
    args = parser.parse_args()

    setup_state(args.state_dir, args.fixture)
    rt = PostBirthLiveObservationRuntime(state_dir=args.state_dir)
    rt.run()
    d = rt.source_diet

    print("=== Live source-diet demo ===")
    print(f"  total events        : {d.get('total_events', 0)}")
    print(f"  balance             : {d.get('balance')}")
    print(f"  dominant source     : {d.get('dominant_source') or 'none'}")
    print(f"  dominance score     : "
          f"{d.get('live_source_diet_dominance_score', 0.0)}")
    print(f"  operator pulse prop.: "
          f"{d.get('live_operator_pulse_dominance_score', 0.0)}")
    print(f"  human text prop.    : {d.get('human_text_proportion', 0.0)}")
    print("  by source:")
    for sid, prop in sorted(d.get("by_source", {}).items(),
                            key=lambda kv: -kv[1]):
        print(f"    - {sid:<32} {prop:.0%}")
    if d.get("findings"):
        print("  findings:")
        for f in d["findings"]:
            print(f"    - {f['finding']}: {f['detail']}")
    print("note : no source should silently dominate; operator pulse is "
          "stimulus, not the primary source; human text must not become the "
          "primary ontology. Report-only; nothing is learned.")


if __name__ == "__main__":
    main()
