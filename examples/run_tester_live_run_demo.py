#!/usr/bin/env python3
"""Tester live run demo: local sample inbox -> birth -> membrane -> integration -> obs.

    python examples/run_tester_live_run_demo.py \\
        --state-dir .solaris_ai_nn_live/test_live_run \\
        --tester-state-dir .solaris_ai_nn_tester/live/test_live_run

Initializes the live state, simulates the tester's manual governance approval (so the
pipeline can run), copies the safe sample events into the local inbox, then runs Live
Birth -> Environmental Membrane -> Membrane Integration -> Live Observation and
generates the reports + bundle. Solaris starts no feeder.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_live_readonly import (
    GovernanceTemplateBuilder,
    TesterLiveReadOnlyRuntime,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", default=".solaris_ai_nn_live/test_live_run")
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/live/test_live_run")
    args = ap.parse_args()

    # Init writes the SAFE-OFF template; the tester then approves by hand. Here we
    # simulate that manual approval so the demo can exercise the live pipeline.
    TesterLiveReadOnlyRuntime(
        state_dir=args.state_dir, tester_state_dir=args.tester_state_dir,
        profile="tester_live_init_only_v0").run()
    gov = GovernanceTemplateBuilder().build().to_dict()
    gov.update(live_readonly_enabled=True, operator_approved=True,
               approved_by="Tester (demo)", approved_at_utc="2026-06-17T00:00:00Z")
    gov_dir = os.path.join(args.state_dir, "governance")
    os.makedirs(gov_dir, exist_ok=True)
    with open(os.path.join(gov_dir, "LIVE_READONLY_GOVERNANCE.json"), "w",
              encoding="utf-8") as fh:
        json.dump(gov, fh, indent=2)

    rt = TesterLiveReadOnlyRuntime(
        state_dir=args.state_dir, tester_state_dir=args.tester_state_dir,
        write_templates=False, copy_safe_samples_to_inbox=True,
        run_birth=True, run_membrane=True, run_integration=True,
        run_observation=True)
    result = rt.run()
    st = rt.tester_live_status()
    print("tester live run demo")
    print(f"  governance        : {st['governance_status']}")
    print(f"  live doctor       : {st['live_doctor_status']}")
    print(f"  membrane impressions: {st['membrane_impression_count']}")
    print(f"  quarantined       : {st['quarantine_count']}")
    print(f"  integration       : "
          f"{rt.integration_status.get('pipeline_status')}")
    print(f"  observation       : "
          f"{rt.observation_status.get('live_observation_enabled')}")
    print(f"  solaris controls feeders: {st['solaris_controls_any_feeder']}")
    print(f"  report            : {result['tester_live_report']}")
    print(f"  bundle            : {result['tester_live_bundle']}")
    print("note: external feeders are manual; Solaris started/controlled none.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
