#!/usr/bin/env python3
"""Live source-health demo: per-source presence, noise, quarantine, contamination.

    python examples/run_live_source_health_demo.py --state-dir .solaris_ai_nn_live/health_demo

Runs the bounded post-birth observation and prints, per source, the health status
(healthy / noisy / silent / unstable / forbidden), event count, and quarantine rate.
A silent source may be an absence signal, not a failure; an unknown source is not
trusted; a forbidden source blocks stability. Read-only; no learning.
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
    parser = argparse.ArgumentParser(description="Live source-health demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_live/health_demo")
    parser.add_argument("--fixture", type=str,
                        default="sample_observation_events.jsonl")
    args = parser.parse_args()

    setup_state(args.state_dir, args.fixture)
    rt = PostBirthLiveObservationRuntime(state_dir=args.state_dir)
    rt.run()
    health = rt.source_health_summary

    print("=== Live source-health demo ===")
    print(f"  live sources : {health.get('live_source_count', 0)} "
          f"(healthy {health.get('live_healthy_source_count', 0)}, "
          f"noisy {health.get('live_noisy_source_count', 0)}, "
          f"silent {health.get('live_silent_source_count', 0)}, "
          f"forbidden {health.get('live_forbidden_source_count', 0)})")
    print(f"  blocks stability : {health.get('blocks_stability')}")
    print("  per-source:")
    for src in health.get("sources", []):
        print(f"    - {src['source_id']:<32} {src['status']:<22} "
              f"events={src['event_count']:<3} "
              f"quarantine_rate={src['quarantine_rate']:.0%} "
              f"noise={src['noise_score']:.2f}")
    print("note : a silent source may be an absence signal, not a failure; an "
          "unknown source is not trusted; a forbidden source blocks stability. "
          "Read-only; no learning.")


if __name__ == "__main__":
    main()
