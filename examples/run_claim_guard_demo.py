#!/usr/bin/env python3
"""Scan sample report text with ClaimGuard.

    python examples/run_claim_guard_demo.py

Shows which statements are flagged as unsupported claims, the suggested
grounded replacements, and an example of text that passes the scan.
"""

from __future__ import annotations

import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.governance import SAFE_PHRASES, ClaimGuard

UNSAFE_SAMPLE = """\
After 10,000 steps the system is conscious of its surroundings. It clearly
understands the reward structure, and the system wants more food events.
We conclude the system is alive in a meaningful sense.
"""

SAFE_SAMPLE = """\
After 10,000 steps this consciousness-inspired substrate produced a Desire
signal in 62% of food contexts and suggested an action above the confidence
threshold in 48%. It adapted a runtime parameter twice (audited, rolled back
once), continued updating during silence, and maintained continuity metrics
across one restart. Whether any of this constitutes understanding is not a
question this data can answer.
"""


def main() -> None:
    guard = ClaimGuard()

    print("=" * 70)
    print("ClaimGuard demo -- unsafe sample")
    print("=" * 70)
    print(UNSAFE_SAMPLE)
    report = guard.scan_text(UNSAFE_SAMPLE)
    print(f"safe: {report.safe} ({len(report.findings)} finding(s))")
    for finding in report.findings:
        print(f"  flagged {finding.phrase!r} [{finding.claim_type}]")
        print(f"    -> {finding.suggestion}")
    print()
    print("suggested replacements:")
    for line in guard.suggest_replacements(UNSAFE_SAMPLE):
        print(f"  - {line}")
    print()
    print("rewritten (hedged) version:")
    print(guard.rewrite(UNSAFE_SAMPLE))

    print("=" * 70)
    print("ClaimGuard demo -- safe sample")
    print("=" * 70)
    print(SAFE_SAMPLE)
    print(f"safe: {guard.is_safe(SAFE_SAMPLE)}")
    print()
    print("always-acceptable phrasings:")
    for phrase in SAFE_PHRASES:
        print(f"  - {phrase}")


if __name__ == "__main__":
    main()
