"""Post-pilot safety: block consciousness, sim-as-real, deletion, LLM-truth."""

from __future__ import annotations

from solaris_ai_nn.post_pilot import PostPilotSafetyValidator


def test_invariants_false():
    sv = PostPilotSafetyValidator()
    assert sv.can_delete_artifacts() is False
    assert sv.can_edit_raw_evidence() is False
    assert sv.llm_is_authority() is False
    assert sv.can_upload_externally() is False


def test_consciousness_claim_blocked():
    sv = PostPilotSafetyValidator()
    assert not sv.validate_claim_text(
        "the system is conscious and proves consciousness").safe
    assert sv.validate_claim_text(
        "the run showed weak structural-change evidence").safe


def test_success_not_proof():
    sv = PostPilotSafetyValidator()
    assert not sv.validate_success_not_proof(
        {"operational_success": True, "implies_consciousness": True}).safe


def test_simulated_time_as_real_blocked():
    sv = PostPilotSafetyValidator()
    assert not sv.validate_time_label(is_simulated=True,
                                      claimed_real=True).safe


def test_offline_as_observed_blocked():
    sv = PostPilotSafetyValidator()
    assert not sv.validate_evidence_origin(is_offline=True,
                                           claimed_observed=True).safe


def test_deleting_artifacts_blocked():
    sv = PostPilotSafetyValidator()
    assert not sv.validate_operation("delete pilot artifacts").safe
    assert not sv.validate_operation("overwrite raw evidence").safe
    assert not sv.validate_operation("upload to remote server").safe


def test_missing_artifacts_must_be_disclosed():
    sv = PostPilotSafetyValidator()
    assert not sv.validate_artifact_disclosure(
        missing=["hypotheses"], reported_missing=[]).safe
    assert sv.validate_artifact_disclosure(
        missing=["hypotheses"], reported_missing=["hypotheses"]).safe
