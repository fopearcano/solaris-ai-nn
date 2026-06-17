#!/usr/bin/env python3
"""Tester live samples demo: safe accept, unsafe quarantine, mixed partial.

    python examples/run_tester_live_samples_demo.py \\
        --state-dir .solaris_ai_nn_live/test_live_samples \\
        --tester-state-dir .solaris_ai_nn_tester/live/test_live_samples

Validates the safe/unsafe/mixed event packs using the same checks Live Birth applies,
showing that safe events accept, unsafe events quarantine, and mixed events partially
accept and partially quarantine.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_live_readonly import (
    SafeEventPackBuilder,
    SafeEventPackValidator,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir",
                    default=".solaris_ai_nn_live/test_live_samples")
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/live/test_live_samples")
    args = ap.parse_args()

    res = SafeEventPackValidator(strict=True).validate_pack(
        SafeEventPackBuilder().build())
    print("tester live samples demo")
    print(f"  safe accepted    : {res['safe']['accepted_count']}/"
          f"{res['safe']['event_count']}")
    print(f"  unsafe quarantined: {res['unsafe']['quarantined_count']}/"
          f"{res['unsafe']['event_count']}")
    print("  unsafe reasons   :")
    for q in res["unsafe"]["quarantined"][:10]:
        print(f"    - {q['event_id']}: {q['quarantine_reason']}")
    print(f"  mixed partial    : accepted {res['mixed']['accepted_count']}, "
          f"quarantined {res['mixed']['quarantined_count']}")
    print("note: debug gloss and human labels are not ground truth; unsafe "
          "events are quarantined, never learned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
