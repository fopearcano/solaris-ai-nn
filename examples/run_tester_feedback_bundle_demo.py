#!/usr/bin/env python3
"""Tester feedback bundle demo: local bundle generation + redaction report.

    python examples/run_tester_feedback_bundle_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_feedback_bundle

Ingests the sample bug + safety concern, builds the local feedback bundle, and prints
the manifest including the redaction count. The bundle is local only -- nothing is
uploaded or published.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_feedback import TesterFeedbackRuntime


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_feedback_bundle")
    args = ap.parse_args()
    samples = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "tester_feedback")

    for sample in ("sample_bug_report.json", "sample_safety_concern.json"):
        TesterFeedbackRuntime(tester_state_dir=args.tester_state_dir,
                              ingest_path=os.path.join(samples, sample)).run()
    rt = TesterFeedbackRuntime(tester_state_dir=args.tester_state_dir,
                               build_bundle=True)
    rt.run()
    m = rt.bundle.manifest.to_dict() if rt.bundle else {}
    print("tester feedback bundle demo")
    print(f"  bundle dir : {m.get('bundle_dir')}")
    print(f"  entries    : {m.get('entry_count', 0)}")
    print(f"  redactions : {m.get('redaction_count', 0)}")
    print(f"  local only : {m.get('local_only')}")
    print(f"  uploaded/published: {m.get('uploaded')} / {m.get('published')}")
    print("note: the feedback bundle is local-only; nothing is zipped "
          "automatically, uploaded, or published.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
