#!/usr/bin/env python3
"""Tester feedback ingest demo: ingest a bug, safety concern, confusion, suggestion.

    python examples/run_tester_feedback_ingest_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_feedback_ingest

Ingests the four sample feedback files into the local append-only ledger and prints the
running counts. Each ingest is local only; nothing is uploaded or turned into a remote
issue.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_feedback import TesterFeedbackRuntime

_SAMPLES = (
    "sample_bug_report.json", "sample_safety_concern.json",
    "sample_confusion_report.json", "sample_suggestion.json",
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_feedback_ingest")
    args = ap.parse_args()
    samples_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "tester_feedback")

    print("tester feedback ingest demo")
    result = None
    for sample in _SAMPLES:
        rt = TesterFeedbackRuntime(
            tester_state_dir=args.tester_state_dir,
            ingest_path=os.path.join(samples_dir, sample))
        result = rt.run()
        print(f"  ingested {sample}: entries now {result['entry_count']}")
    if result:
        print(f"  bugs={result['bug_report_count']} "
              f"safety={result['safety_concern_count']} "
              f"release_blockers={result['release_blocker_count']}")
        print(f"  next action: {result['recommended_next_action']}")
    print("note: feedback is local QA evidence only; nothing is uploaded or "
          "turned into a remote issue.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
