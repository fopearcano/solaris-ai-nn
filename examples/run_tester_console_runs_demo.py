#!/usr/bin/env python3
"""Tester console runs demo: a run index with fixture/live/membrane runs + latest marker.

    python examples/run_tester_console_runs_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_console_runs

Stages a fixture run plus a synthetic membrane report, builds the console, and prints
the run index showing the run records and the latest-run marker. Old runs are preserved.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_console import TesterConsoleRuntime
from solaris_ai_nn.tester_fixture_spine import TesterFixtureDemoRuntime


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_console_runs")
    args = ap.parse_args()
    base = args.tester_state_dir
    live = os.path.join(base, "live")

    TesterFixtureDemoRuntime(state_dir=base, profile="fixture_tester_v0").run()
    # Synthetic membrane report so the run index has a membrane run too.
    os.makedirs(os.path.join(live, "membrane", "reports"), exist_ok=True)
    json.dump({"membrane_impression_count": 4, "source_pressure_status":
               "balanced"},
              open(os.path.join(live, "membrane", "reports",
                                "ENVIRONMENTAL_MEMBRANE_REPORT.json"), "w"))

    rt = TesterConsoleRuntime(state_dir=live, tester_state_dir=base,
                              console_dir=os.path.join(base, "console"),
                              html=False)
    rt.run()
    idx = rt.run_index.to_dict()
    print("tester console runs demo")
    print(f"  runs   : {idx['run_count']}; latest: {idx['latest_run_id']}")
    print(f"  by type: {idx['by_type']}")
    for r in idx["runs"]:
        print(f"    - {r['run_id']} [{r['run_type']}] {r['status']}"
              + ("  (latest)" if r["latest"] else ""))
    print("note: old runs are preserved; the latest run is marked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
