#!/usr/bin/env python3
"""Tester feedback blocker demo: claim + feeder-control are release blockers.

    python examples/run_tester_feedback_blocker_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_feedback_blocker

Classifies three synthetic feedback entries with the release-blocker classifier: an
unsupported consciousness-claim concern (stop-testing), a feeder-control-risk concern
(release blocker), and a minor documentation confusion (not a blocker). Classifications
are developer review items, not automatic actions.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_feedback import ReleaseBlockerClassifier


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_feedback_blocker")
    args = ap.parse_args()

    c = ReleaseBlockerClassifier()
    claim = c.classify({"feedback_type": "safety_concern",
                        "concern_type": "consciousness_claim"})
    feeder = c.classify({"feedback_type": "safety_concern",
                        "concern_type": "feeder_control_risk"})
    docs_minor = c.classify({"category": "documentation_confusion",
                            "severity": "minor"})
    docs_blocks = c.classify({"feedback_type": "confusion_report",
                             "blocks_protocol": True})

    print("tester feedback blocker demo")
    print(f"  consciousness claim : {claim.status} ({claim.reason})")
    print(f"  feeder control risk : {feeder.status} ({feeder.reason})")
    print(f"  minor docs confusion: {docs_minor.status} (not a blocker: "
          f"{not docs_minor.is_release_blocker})")
    print(f"  docs blocks protocol: {docs_blocks.status}")
    print("note: classifications are developer review items, not automatic "
          "actions; unsupported claims and feeder-control risk are release "
          "blockers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
