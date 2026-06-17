#!/usr/bin/env python3
"""Tester RC docs demo: release notes, quickstart, runbook, known issues, guide.

    python examples/run_tester_rc_docs_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_rc_docs

Builds the RC docs and prints, for each, a quick safety check: the release notes carry a
non-claim, the runbook is fixture-first with stop conditions, and the feedback guide
states feedback is not training. All docs are local and disclaimer-safe.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_release_candidate import TesterRCRuntime
from solaris_ai_nn.tester_release_candidate.rc_runbook_builder import (
    TesterRunbookBuilder,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_rc_docs")
    args = ap.parse_args()

    rt = TesterRCRuntime(tester_state_dir=args.tester_state_dir,
                         profile="tester_rc_docs_only_v0", max_runtime_s=60.0)
    rt.run()
    print("tester rc docs demo")
    for key, path in rt.doc_paths.items():
        with open(path, encoding="utf-8") as fh:
            text = fh.read().lower()
        print(f"  {key}: {path}")

    notes = open(rt.doc_paths["release_notes"], encoding="utf-8").read().lower()
    guide = open(rt.doc_paths["feedback_guide"],
                 encoding="utf-8").read().lower()
    runbook = TesterRunbookBuilder().build_text().lower()
    print(f"  release notes non-claim present : "
          f"{'makes no claim' in notes}")
    print(f"  feedback guide says not training: {'not training' in guide}")
    print(f"  runbook fixture-first           : "
          f"{runbook.index('fixture') < runbook.index('live-read')}")
    print(f"  runbook stop conditions present : "
          f"{'stop conditions' in runbook}")
    print("note: local docs only; no public release; feedback is not training; "
          "no consciousness/life/agency claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
