#!/usr/bin/env python3
"""Tester fixture demo: run the full fixture-only known-good organismic rehearsal.

    python examples/run_tester_fixture_demo.py --state-dir .solaris_ai_nn_tester/demo

Runs the bounded, fixture-only tester demo (validation/quarantine -> environmental
membrane -> sensory impressions -> membrane-integration audit -> observation ->
optional ontogenesis/semiogenesis/cognition -> claim/safety scan), builds a local
artifact bundle, and prints the golden-run, reproducibility, and regression results.
No live data is required; nothing is published or uploaded.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_fixture_spine import TesterFixtureDemoRuntime


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", default=".solaris_ai_nn_tester/demo")
    ap.add_argument("--profile", default="fixture_tester_v0")
    args = ap.parse_args()

    rt = TesterFixtureDemoRuntime(state_dir=args.state_dir, profile=args.profile)
    result = rt.run()
    st = rt.tester_status()
    print("tester fixture demo")
    print(f"  run id              : {st['tester_run_id']} ({st['tester_profile']})")
    print(f"  fixture-only        : {st['fixture_only']} "
          f"(requires live data: {st['requires_live_data']})")
    print(f"  fixture events      : {st['fixture_event_count']} "
          f"(quarantined {st['fixture_quarantined_count']})")
    print(f"  membrane impressions: {st['membrane_impression_count']}")
    print(f"  golden run          : {st['golden_run_status']}")
    print(f"  reproducibility     : {st['reproducibility_status']}")
    print(f"  regression          : {st['regression_status']}")
    print(f"  skipped stages      : "
          f"{', '.join(st['skipped_optional_stages']) or 'none'}")
    print(f"  tester report       : {result['tester_report']}")
    print(f"  tester bundle       : {result['tester_bundle']}")
    print(f"  next action         : {rt.recommended_next_action()}")
    print("note                  : a fixture-only known-good rehearsal. No live "
          "data, feeders, hardware, network, Git, publish, or feedback training. "
          "No consciousness/life/agency claim is made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
