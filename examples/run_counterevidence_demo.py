#!/usr/bin/env python3
"""Counterevidence demo: fixture overfit, passive-parser equivalence, missing live.

    python examples/run_counterevidence_demo.py --state-dir .solaris_ai_nn_claims/test_counterevidence

Detects counterevidence from an evidence bundle: fixture overfit risk, passive-
parser equivalence, missing live data, a failed replication, and a falsification
failure. Counterevidence is as visible as evidence; blocking counterevidence
(falsification, safety regression, ClaimGuard failure) blocks a claim.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.scientific_claims import CounterEvidenceAnalyzer


def main():
    parser = argparse.ArgumentParser(description="Counterevidence demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_claims/test_counterevidence")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    bundle = {
        "sensorium_differentiation": {"fixture_overfit_risk": True,
                                      "passive_parser_equivalent": True,
                                      "label_contamination_risk": True},
        "missing_live_data": True,
        "replication": {"failed_replication_count": 1},
        "falsification": {"falsified_claim_count": 1},
        "missing_artifacts": ["soak_dossier"],
        "operator_uncertainty": "operator notes the sample is small",
    }
    records = CounterEvidenceAnalyzer().detect(bundle, claim_ref="c_dev")
    summary = CounterEvidenceAnalyzer.summary(records)

    print("=== Counterevidence demo ===")
    print(f"  counterevidence : {summary['counterevidence_count']} "
          f"(blocking {summary['blocking_counterevidence_count']})")
    for r in summary["records"]:
        flag = " (BLOCKS claim)" if r["blocks_claim"] else ""
        print(f"    - {r['counter_type']}: {r['detail']}{flag}")
    print("note            : counterevidence is as visible as evidence and is "
          "never ignored for being inconvenient. Blocking counterevidence "
          "(falsification, safety regression, ClaimGuard failure) blocks a "
          "claim outright.")


if __name__ == "__main__":
    main()
