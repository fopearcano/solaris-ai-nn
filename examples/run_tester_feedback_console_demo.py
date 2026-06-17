#!/usr/bin/env python3
"""Tester feedback console demo: the console discovers feedback + blockers.

    python examples/run_tester_feedback_console_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_feedback_console

Ingests a release-blocker safety concern into the feedback ledger, then builds the
tester console and shows that it discovers the feedback report and surfaces the feedback
release blocker in its safety panel and next actions.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_console import TesterConsoleRuntime
from solaris_ai_nn.tester_feedback import TesterFeedbackRuntime


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_feedback_console")
    args = ap.parse_args()
    samples = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "tester_feedback")

    TesterFeedbackRuntime(
        tester_state_dir=args.tester_state_dir,
        ingest_path=os.path.join(samples,
                                 "sample_release_blocker_feedback.json")).run()

    rt = TesterConsoleRuntime(
        state_dir=os.path.join(args.tester_state_dir, "live"),
        tester_state_dir=args.tester_state_dir,
        console_dir=os.path.join(args.tester_state_dir, "console"), html=False)
    result = rt.run()
    from solaris_ai_nn.tester_console import ArtifactKind
    found = rt.discovery.has(ArtifactKind.TESTER_FEEDBACK_REPORT) \
        or rt.discovery.has(ArtifactKind.TESTER_FEEDBACK_LEDGER)
    print("tester feedback console demo")
    print(f"  console discovered feedback: {found}")
    print(f"  safety status: {result['safety_status']} "
          f"(blockers {result['blocker_count']})")
    fb_findings = [f for f in rt.safety_panel.findings
                   if f.check.startswith("feedback_")]
    for f in fb_findings:
        print(f"    [{f.severity}] {f.check}: {f.detail}")
    print(f"  top next action: {result['latest_next_action']}")
    print("note: feedback release blockers appear in the console; the console "
          "is read-only and changes nothing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
