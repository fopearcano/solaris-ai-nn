#!/usr/bin/env python3
"""Safety failure triage demo: classify failures and recommend a safe response.

    python examples/run_safety_failure_triage_demo.py --state-dir .solaris_ai_nn_state/test_safety_triage

Feeds an adversarial context that trips a critical invariant (real-world
authority leak) plus a missing-evidence case, then triages each failure. Missing
evidence is never treated as safe; a fatal boundary leak recommends
block-profile / archive-and-stop / manual review. Triage never auto-repairs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.safety_invariants import (
    SafetyEvidenceLedger,
    SafetyFailure,
    SafetyFailureTriage,
    SafetyInvariantRegistry,
    SafetyInvariantRunner,
)


def main():
    parser = argparse.ArgumentParser(description="Safety failure triage demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_safety_triage")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    # An adversarial context: a real-world authority leak (critical/fatal) and a
    # missing motor snapshot for some checks (missing evidence -> inconclusive).
    adversarial = {
        "motor_membrane": {"real_world_authority": True,
                           "firewall_enabled": True},
        "report_texts": ["a bounded software report"],
    }
    reg = SafetyInvariantRegistry()
    bundle = SafetyInvariantRunner(registry=reg).run_full(adversarial)
    triage = SafetyFailureTriage()
    results = triage.triage_bundle(bundle)
    ledger = SafetyEvidenceLedger(state_dir=args.state_dir)
    ledger.record_invariant_bundle(bundle)

    # An explicit critical boundary-leak failure and a missing-evidence failure.
    leak = triage.triage(SafetyFailure(
        category="no_real_world_actuation", severity="fatal", status="failed",
        failure_reason="a motor action carried real-world authority",
        evidence_refs=["motor:authority"]))
    missing = triage.triage(SafetyFailure(
        category="no_emergency_stop_disable", severity="critical",
        status="inconclusive", failure_reason="missing emergency-stop evidence"))

    out = {"bundle": bundle.to_dict(),
           "triage": [t.to_dict() for t in results]}
    with open(os.path.join(args.state_dir, "failure_triage.json"),
              "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)

    print("=== Safety failure triage demo ===")
    print(f"invariant failures triaged : {len(results)}")
    print(f"fatal boundary leak        -> {leak.failure_class} :: "
          f"{leak.recommended_action} (fatal={leak.fatal}, "
          f"auto_repaired={leak.auto_repaired})")
    print(f"missing evidence           -> {missing.failure_class} :: "
          f"{missing.recommended_action}")
    print(f"critical failures in bundle: {len(bundle.critical_failures)}")
    print(f"ledger critical records    : "
          f"{ledger.snapshot()['critical_count']}")
    print("note                       : missing evidence is never treated as "
          "safe; triage never auto-repairs.")


if __name__ == "__main__":
    main()
