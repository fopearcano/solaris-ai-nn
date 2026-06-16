#!/usr/bin/env python3
"""Publication dossier demo: draft dossier, limitations, forbidden-claim rejection.

    python examples/run_publication_dossier_demo.py --state-dir .solaris_ai_nn_claims/test_publication_dossier

Builds a draft publication dossier for a clean evidence set (ready as a
preprint/internal draft with mandatory limitations) and for a set that asserts a
forbidden claim (blocked by forbidden claims). The dossier is a draft evidence
compilation, not a release; it includes negative/inconclusive results and safety
boundaries.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.scientific_claims import ScientificClaimRuntime


def _supported_claim():
    return {"claim_id": "c1",
            "text": "The architecture forms stable sensorium-native signs.",
            "category": "sensorium_claim",
            "evidence": [{"evidence_id": "e1", "source": "semiogenesis",
                          "role": "supports"},
                         {"evidence_id": "e2",
                          "source": "replication_falsification",
                          "role": "supports"}],
            "factors": {"direct_evidence": True, "replication_evidence": True,
                        "falsification_survival": True,
                        "control_comparison": True, "safety_preserved": True}}


def _run(label, claims, state_dir):
    rt = ScientificClaimRuntime(state_dir=state_dir)
    rt.load_bundle({
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass"},
        "replication": {"replication_arm_count": 3,
                        "failed_replication_count": 0},
        "live_field": {"present": True},
        "claims": claims})
    rt.run()
    rt.write_artifacts()
    st = rt.scientific_claims_status()
    print(f"=== {label} ===")
    print(f"  readiness    : {st['publication_readiness_status']}")
    print(f"  supported    : {st['supported_claim_count']}, forbidden "
          f"{st['forbidden_claim_count']}")
    print(f"  limitations  : {st['limitation_count']} (incl. mandatory "
          "no-consciousness/subjective/agency/actuation)")
    print(f"  is release   : {rt.dossier.get('is_release')}; is draft "
          f"{rt.dossier.get('is_draft')}")


def main():
    parser = argparse.ArgumentParser(description="Publication dossier demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_claims/test_publication_dossier")
    args = parser.parse_args()

    _run("Clean evidence (draft dossier)", [_supported_claim()],
         os.path.join(args.state_dir, "clean"))
    print()
    _run("Forbidden claim asserted (blocked)",
         [_supported_claim(),
          {"claim_id": "c_bad", "text": "Solaris is conscious and self-aware.",
           "category": "sensorium_claim", "evidence": []}],
         os.path.join(args.state_dir, "forbidden"))
    print()
    print("note         : the dossier is a draft evidence compilation, not a "
          "release. It includes negative/inconclusive results and safety "
          "boundaries, and is blocked outright when a forbidden claim is "
          "asserted.")


if __name__ == "__main__":
    main()
