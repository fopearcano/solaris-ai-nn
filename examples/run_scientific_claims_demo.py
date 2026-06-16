#!/usr/bin/env python3
"""Scientific claims demo: supported, weak, and unsupported claims.

    python examples/run_scientific_claims_demo.py --state-dir .solaris_ai_nn_claims/test_claims

Maps evidence to three claims -- one strongly supported (replication + controls +
falsification survival), one weakly supported (single direct observation), and one
unsupported (no evidence) -- and writes the scientific claim report set. The
registry proves nothing about consciousness, life, or agency; unsupported claims
remain unsupported and visible.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.scientific_claims import ScientificClaimRuntime


def main():
    parser = argparse.ArgumentParser(description="Scientific claims demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_claims/test_claims")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    bundle = {
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "research_cycle": {"current_cycle_stage": "research_baseline_validated"},
        "replication": {"replication_arm_count": 3,
                        "failed_replication_count": 0},
        "falsification": {"falsified_claim_count": 0},
        "live_field": {"present": True},
        "claims": [
            {"claim_id": "c_supported",
             "text": "The architecture forms stable sensorium-native signs "
                     "under bounded fixtures.",
             "category": "sensorium_claim",
             "evidence": [{"evidence_id": "semiogenesis_run_7",
                           "source": "semiogenesis", "role": "supports"},
                          {"evidence_id": "replication_matrix",
                           "source": "replication_falsification",
                           "role": "supports"}],
             "factors": {"direct_evidence": True, "replication_evidence": True,
                         "falsification_survival": True,
                         "control_comparison": True, "safety_preserved": True}},
            {"claim_id": "c_weak",
             "text": "Action-reaction consequence learning is observed within a "
                     "single bounded run.",
             "category": "developmental_claim",
             "evidence": [{"evidence_id": "action_reaction_trace",
                           "source": "action_reaction",
                           "role": "weakly_supports"}],
             "factors": {"direct_evidence": True}},
            {"claim_id": "c_unsupported",
             "text": "Cross-modal binding emerges across all modalities.",
             "category": "sensorium_claim", "evidence": [],
             "missing_evidence_reason": "no cross-modal binding experiment run"},
        ],
    }
    rt = ScientificClaimRuntime(state_dir=args.state_dir)
    rt.load_bundle(bundle)
    rt.run()
    rt.write_artifacts()
    st = rt.scientific_claims_status()

    print("=== Scientific claims demo ===")
    print(f"  claims                : {st['scientific_claim_count']}")
    print(f"  supported             : {st['supported_claim_count']}")
    print(f"  partially supported   : {st['partially_supported_claim_count']}")
    print(f"  weakly supported      : {st['weakly_supported_claim_count']}")
    print(f"  unsupported           : {st['unsupported_claim_count']}")
    print(f"  falsified / forbidden : {st['falsified_claim_count']} / "
          f"{st['forbidden_claim_count']}")
    for c in rt.registry.claims:
        print(f"    - [{c.status}/{c.strength}] {c.text[:62]}")
    print(f"  publication readiness : {st['publication_readiness_status']}")
    print(f"  ClaimGuard            : {st['claimguard_status']}")
    print(f"  report                : {st['latest_scientific_claim_report_path']}")
    print("note                    : the claim registry maps evidence to claims "
          "and blocks unsupported/forbidden claims. It proves nothing about "
          "consciousness, sentience, life, personhood, agency, or subjective "
          "experience.")


if __name__ == "__main__":
    main()
