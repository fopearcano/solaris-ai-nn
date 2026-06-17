#!/usr/bin/env python3
"""Tester feedback init demo: generate the local forms and initialize the ledger.

    python examples/run_tester_feedback_init_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_feedback_init

Generates the local feedback forms (bug/safety/confusion/suggestion + the main form)
and initializes the append-only ledger. Feedback is local QA evidence only -- not
training, not RLHF, not ground truth, not a command.
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
                    default=".solaris_ai_nn_tester/test_feedback_init")
    args = ap.parse_args()

    rt = TesterFeedbackRuntime(tester_state_dir=args.tester_state_dir,
                               profile="tester_feedback_forms_only_v0",
                               forms_only=True)
    rt.run()
    forms_dir = os.path.join(rt.feedback_dir, "forms")
    print("tester feedback init demo")
    print(f"  forms dir : {forms_dir}")
    for name in sorted(os.listdir(forms_dir)):
        print(f"    - {name}")
    print(f"  ledger    : {rt.ledger.jsonl_path}")
    print("note: feedback is LOCAL QA evidence only -- not training, not RLHF, "
          "not ground truth, not a command. It does not modify Solaris "
          "behaviour or create remote issues.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
