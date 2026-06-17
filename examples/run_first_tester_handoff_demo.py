#!/usr/bin/env python3
"""First tester handoff demo: safe / review / do-not-share artifact classes.

    python examples/run_first_tester_handoff_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_first_tester_handoff

Generates the handoff guide and prints the artifacts grouped by privacy level, showing
that raw live inbox files and private payloads are not safe to share by default and that
sharing is manual only.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.first_tester_protocol import (
    FirstTesterArtifactHandoff,
    FirstTesterProtocolRuntime,
    HandoffPrivacyLevel,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_first_tester_handoff")
    args = ap.parse_args()

    rt = FirstTesterProtocolRuntime(tester_state_dir=args.tester_state_dir,
                                    profile="first_tester_handoff_only_v0",
                                    max_runtime_s=60.0)
    rt.run()
    h = FirstTesterArtifactHandoff()
    print("first tester handoff demo")
    print(f"  manual-only: {h.to_dict()['manual_only']}; uploads: "
          f"{h.to_dict()['uploads']}")
    print("  review before share:")
    for a in h.by_privacy(HandoffPrivacyLevel.REVIEW_BEFORE_SHARE)[:4]:
        print(f"    - {a.name}")
    print("  do not share / private:")
    for a in (h.by_privacy(HandoffPrivacyLevel.DO_NOT_SHARE)
              + h.by_privacy(HandoffPrivacyLevel.CONTAINS_PRIVATE_DATA))[:4]:
        print(f"    - {a.name}")
    print(f"  handoff guide: {rt.doc_paths.get('handoff_guide')}")
    print("note: handoff is manual only; raw live inbox files and private "
          "payloads are not safe to share by default; nothing is uploaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
