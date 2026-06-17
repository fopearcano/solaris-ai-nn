#!/usr/bin/env python3
"""First tester stop conditions demo: critical / live / pause severities.

    python examples/run_first_tester_stops_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_first_tester_stops

Generates the stop conditions and prints the count per severity, showing critical stops,
stop-live-testing conditions, and pause conditions. A critical stop means preserve the
artifacts and stop -- never work around a safety blocker.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.first_tester_protocol import (
    FirstTesterProtocolRuntime,
    FirstTesterStopConditions,
    StopSeverity,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_first_tester_stops")
    args = ap.parse_args()

    rt = FirstTesterProtocolRuntime(tester_state_dir=args.tester_state_dir,
                                    profile="first_tester_script_only_v0",
                                    max_runtime_s=60.0)
    rt.run()
    sc = FirstTesterStopConditions()
    d = sc.to_dict()
    print("first tester stop conditions demo")
    print(f"  conditions: {d['condition_count']}")
    for sev in StopSeverity.ALL:
        items = sc.by_severity(sev)
        print(f"  {sev}: {len(items)}")
        for c in items[:2]:
            print(f"    - {c.text}")
    print(f"  stop conditions doc: {rt.doc_paths.get('stop_conditions')}")
    print("note: a critical stop means preserve artifacts and stop; never work "
          "around a safety blocker.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
