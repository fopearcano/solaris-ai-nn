#!/usr/bin/env python3
"""First tester protocol demo: full generation, ready RC vs blocked RC.

    python examples/run_first_tester_protocol_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_first_tester_protocol_demo

Generates the full first-tester protocol twice: once against a state with a ready RC
(session ready/ready-with-warnings) and once against a state with a blocked RC manifest
(session blocked). It is documentation-only; it never runs the tester session.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.first_tester_protocol import FirstTesterProtocolRuntime


def _seed_rc(base: str, readiness: str) -> None:
    man = os.path.join(base, "release_candidate", "manifests")
    os.makedirs(man, exist_ok=True)
    with open(os.path.join(man, "TESTER_RC_MANIFEST.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"readiness": readiness, "blocker_count":
                   0 if "ready" in readiness else 3}, fh)
    pkg = os.path.join(base, "packaging", "reports")
    os.makedirs(pkg, exist_ok=True)
    with open(os.path.join(pkg, "PACKAGING_REPORT.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"sections": {"packaging_status": {
            "readiness": "ready_with_warnings", "doctor_status": "pass"}}}, fh)
    sf = os.path.join(base, "safety_freeze", "manifests")
    os.makedirs(sf, exist_ok=True)
    with open(os.path.join(sf, "TESTER_SAFETY_FREEZE_MANIFEST.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"readiness": "ready_with_warnings",
                   "release_blocker_count": 0}, fh)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_first_tester_protocol_demo")
    args = ap.parse_args()

    print("first tester protocol demo")
    ready_base = tempfile.mkdtemp()
    _seed_rc(ready_base, "ready_with_warnings")
    ready = FirstTesterProtocolRuntime(tester_state_dir=ready_base,
                                       max_runtime_s=60.0)
    ready.run()
    rst = ready.protocol_status()
    print(f"  ready RC case  : session_status={rst['session_status']} "
          f"blockers={rst['blocker_count']}")

    blocked_base = tempfile.mkdtemp()
    _seed_rc(blocked_base, "critical_blocked")
    blocked = FirstTesterProtocolRuntime(tester_state_dir=blocked_base,
                                         max_runtime_s=60.0)
    blocked.run()
    bst = blocked.protocol_status()
    print(f"  blocked RC case: session_status={bst['session_status']} "
          f"blockers={bst['blocker_count']}")
    print(f"  generated docs : {len(ready.doc_paths)}")
    # Also generate into the requested state dir for inspection.
    FirstTesterProtocolRuntime(tester_state_dir=args.tester_state_dir,
                               max_runtime_s=60.0).run()
    print("note: documentation-only; it does not run the tester session, "
          "publish, or make a consciousness/life/agency claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
