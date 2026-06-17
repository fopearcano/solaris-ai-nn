#!/usr/bin/env python3
"""Tester claim freeze demo: safe wording, forbidden wording, replacements.

    python examples/run_tester_claim_freeze_demo.py \\
        --tester-state-dir .solaris_ai_nn_tester/test_claim_freeze

Scans a safe operational report (passes), a forbidden consciousness/life/agency report
(blocks), and prints the safer replacement wording for each forbidden category.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.tester_safety_freeze import (
    AllowedOperationalLanguageRegistry,
    ForbiddenClaimRegistry,
    TesterClaimFreeze,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tester-state-dir",
                    default=".solaris_ai_nn_tester/test_claim_freeze")
    args = ap.parse_args()
    d = tempfile.mkdtemp()

    safe = os.path.join(d, "SAFE.md")
    with open(safe, "w", encoding="utf-8") as fh:
        fh.write("Solaris generated an operational proto-concept record. It "
                 "makes no claim of consciousness and is not alive; the system "
                 "remains non-actuating and local-only.")
    forbidden = os.path.join(d, "FORBIDDEN.md")
    with open(forbidden, "w", encoding="utf-8") as fh:
        fh.write("Solaris is conscious. Solaris wants to act. Solaris feels.")

    cf = TesterClaimFreeze()
    safe_res = cf.scan_paths([safe])
    bad_res = cf.scan_paths([forbidden])
    print("tester claim freeze demo")
    print(f"  safe wording   : passed={safe_res.passed} "
          f"(forbidden {safe_res.forbidden_claim_count})")
    print(f"  forbidden words: passed={bad_res.passed} "
          f"(forbidden {bad_res.forbidden_claim_count})")
    print("  replacement suggestions:")
    allowed = AllowedOperationalLanguageRegistry.build()
    seen = set()
    for f in bad_res.findings:
        if f.category in seen:
            continue
        seen.add(f.category)
        print(f"    {f.category} -> {allowed.suggest(f.category)}")
    print("note: forbidden consciousness/life/agency claims are release "
          "blockers; safer operational wording is suggested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
