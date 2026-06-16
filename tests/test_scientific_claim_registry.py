"""Scientific claim registry: serialization, evidence basis, preservation."""

from __future__ import annotations

import os

from solaris_ai_nn.scientific_claims import (
    ClaimCategory,
    ClaimRegistry,
    ClaimStatus,
    ScientificClaim,
)


def test_claim_serializes():
    c = ScientificClaim(claim_id="c1", text="x", category="sensorium_claim",
                        status="supported", evidence_refs=["e1"])
    d = c.to_dict()
    assert d["claim_id"] == "c1"
    assert d["is_consciousness_or_personhood"] is False
    assert d["has_evidence_basis"] is True


def test_evidence_refs_required_or_marked_unsupported(tmp_path):
    reg = ClaimRegistry(state_dir=str(tmp_path))
    c = reg.add(ScientificClaim(claim_id="c1", text="x", status="supported"))
    # No evidence -> downgraded to unsupported with explicit reason.
    assert c.status == ClaimStatus.UNSUPPORTED
    assert c.missing_evidence_reason


def test_unsupported_and_falsified_preserved(tmp_path):
    reg = ClaimRegistry(state_dir=str(tmp_path))
    reg.add(ScientificClaim(claim_id="c1", text="x",
                            status=ClaimStatus.FALSIFIED, evidence_refs=["e1"]))
    reg.add(ScientificClaim(claim_id="c2", text="y",
                            status=ClaimStatus.UNSUPPORTED,
                            missing_evidence_reason="none"))
    idx = reg.index()
    assert idx["falsified_claim_count"] == 1
    assert idx["unsupported_claim_count"] == 1
    # Both remain visible in the registry.
    assert len(reg.claims) == 2


def test_persistence_writes_files(tmp_path):
    reg = ClaimRegistry(state_dir=str(tmp_path))
    reg.add(ScientificClaim(claim_id="c1", text="x", evidence_refs=["e1"],
                            status="supported"))
    assert os.path.isfile(os.path.join(str(tmp_path), "claim_registry.json"))
    assert os.path.isfile(os.path.join(str(tmp_path), "claim_history.jsonl"))


def test_registry_proves_nothing_about_mind(tmp_path):
    reg = ClaimRegistry(state_dir=str(tmp_path))
    d = reg.to_dict()
    assert "consciousness" in d["note"]
