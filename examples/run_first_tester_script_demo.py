#!/usr/bin/env python3
"""First tester session script demo: fixture-first, optional live-read-only.

    python examples/run_first_tester_script_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_first_tester_script

Generates the session script and prints a quick structural check: the fixture demo comes
before any live-read-only step, live-read-only is optional, and the script contains no
upload/publish/release commands.
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
    FirstTesterSessionScript,
    SessionPhase,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_first_tester_script")
    args = ap.parse_args()

    rt = FirstTesterProtocolRuntime(tester_state_dir=args.tester_state_dir,
                                    profile="first_tester_script_only_v0",
                                    max_runtime_s=60.0)
    rt.run()
    text = FirstTesterSessionScript().build_text().lower()
    print("first tester session script demo")
    print(f"  phases           : {len(SessionPhase.ALL)}")
    print(f"  fixture-first    : "
          f"{text.index('fixture demo') < text.index('live-read-only')}")
    print(f"  live optional    : {'optional' in text}")
    print(f"  no upload/publish: "
          f"{'upload' not in text and 'publish' not in text}")
    print(f"  session script   : {rt.doc_paths.get('session_script')}")
    print("note: the fixture demo precedes live-read-only; live-read-only is "
          "optional and governance-gated; Solaris never starts feeders.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
