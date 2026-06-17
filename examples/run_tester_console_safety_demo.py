#!/usr/bin/env python3
"""Tester console safety demo: quarantine, membrane-bypass, unsupported-claim blockers.

    python examples/run_tester_console_safety_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_console_safety

Stages synthetic artifacts that trigger safety findings -- a quarantine record, a
critical membrane bypass, and an unsupported scientific claim -- and shows the console
surfacing them in the safety panel and forcing a fix/stop next action.
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


def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_console_safety")
    args = ap.parse_args()
    base = args.tester_state_dir
    live = os.path.join(base, "live")
    claims = os.path.join(base, "claims")

    # Quarantine record.
    _write(os.path.join(live, "quarantine", "q.json"),
           {"quarantined_count": 3})
    # Critical membrane bypass.
    _write(os.path.join(live, "membrane", "integration",
                        "MEMBRANE_INTEGRATION_REPORT.json"),
           {"sections": {"status": {"critical_bypass_count": 2,
                                    "raw_fallback_count": 1}}})
    # Unsupported scientific claim.
    _write(os.path.join(claims, "claim.json"),
           {"forbidden_claim_count": 1, "unsupported_claim_count": 1})

    rt = TesterConsoleRuntime(state_dir=live, tester_state_dir=base,
                              console_dir=os.path.join(base, "console"),
                              claims_dir=claims, html=False)
    result = rt.run()
    sp = rt.safety_panel.to_dict()
    print("tester console safety demo")
    print(f"  safety status   : {sp['safety_status']} "
          f"(blockers {sp['blocker_count']})")
    for f in sp["findings"]:
        if f["severity"] in ("blocker", "warning"):
            print(f"    [{f['severity']}] {f['check']}: {f['detail']}")
    print(f"  top next action : {result['latest_next_action']}")
    print("note: safety findings appear at the top; quarantine/bypass/claims "
          "are never hidden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
