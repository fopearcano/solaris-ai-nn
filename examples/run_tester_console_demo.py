#!/usr/bin/env python3
"""Tester console demo: build the static console from a fixture run.

    python examples/run_tester_console_demo.py \\
        --state-dir .solaris_ai_nn_live/test_console_demo \\
        --tester-state-dir .solaris_ai_nn_tester/test_console_demo \\
        --console-dir .solaris_ai_nn_tester/test_console_demo/console

Runs a fixture tester demo so there are artifacts to summarize, then builds the static
Markdown + offline HTML console and prints where the dashboard was written. The console
is read-only and opens nothing for you.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_console import TesterConsoleRuntime
from solaris_ai_nn.tester_fixture_spine import TesterFixtureDemoRuntime


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", default=".solaris_ai_nn_live/test_console_demo")
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_console_demo")
    ap.add_argument("--console-dir",
                    default=".solaris_ai_nn_tester/test_console_demo/console")
    args = ap.parse_args()

    # Stage a fixture run so the console has something to discover.
    TesterFixtureDemoRuntime(state_dir=args.tester_state_dir,
                             profile="fixture_tester_v0").run()

    rt = TesterConsoleRuntime(
        state_dir=args.state_dir, tester_state_dir=args.tester_state_dir,
        console_dir=args.console_dir)
    result = rt.run()
    print("tester console demo")
    print(f"  overall health  : {result['overall_health']}")
    print(f"  safety          : {result['safety_status']} "
          f"(blockers {result['blocker_count']})")
    print(f"  artifacts found : {result['artifact_count']}")
    print(f"  INDEX.md        : {result['latest_console_index_path']}")
    print(f"  INDEX.html      : {result['latest_console_html_path']}")
    print(f"  next action     : {result['latest_next_action']}")
    print("note: the console is read-only and opens nothing for you; open the "
          "generated files yourself. A green dashboard is operational status, "
          "not evidence of inner life.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
