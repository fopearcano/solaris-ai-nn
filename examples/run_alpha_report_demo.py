#!/usr/bin/env python3
"""Alpha report demo: report from artifacts, ClaimGuard warning, safety statement.

    python examples/run_alpha_report_demo.py --state-dir .solaris_ai_nn_alpha/test_report

Runs a bounded alpha assembly and builds the alpha report set, then prints the
ClaimGuard availability (a warning if unavailable) and the safety boundary
statement. The report shows skipped modules and blockers honestly and makes no
consciousness/life/agency claim.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.alpha_system import AlphaResearchOrchestrator


def main():
    parser = argparse.ArgumentParser(description="Alpha report demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_alpha/test_report")
    args = parser.parse_args()

    orch = AlphaResearchOrchestrator(state_dir=args.state_dir, max_ticks=25)
    orch.run()
    out = orch.write_artifacts()
    report = out["report"]
    sections = report["sections"]

    print("=== Alpha report demo ===")
    print("  documents generated:")
    for p in out["documents"]:
        print(f"    {os.path.basename(p)}")
    print(f"  ClaimGuard available : {sections['claimguard_available']}")
    if not sections["claimguard_available"]:
        print("  WARNING: ClaimGuard unavailable; report text was not "
              "claim-scanned.")
    print(f"  ClaimGuard scan safe : {report['claim_guard_safe']}")
    print("  safety boundaries:")
    for c in sections["alpha_profile"]["safety_constraints"]:
        print(f"    - {c}")
    print("  what this does NOT do:")
    for item in sections["what_this_does_not_do"]:
        print(f"    - {item}")
    print("note: the alpha report shows skipped modules and blockers honestly "
          "and makes no consciousness/life/agency claim.")


if __name__ == "__main__":
    main()
