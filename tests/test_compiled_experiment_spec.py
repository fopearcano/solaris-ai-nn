"""Compiled experiment spec: serializes, non-goals present, no code mutation."""

from __future__ import annotations

from solaris_ai_nn.experiment_compiler import (
    ArchitectureProposalReader,
    ExperimentSpecStatus,
    ExperimentSpecType,
    compile_spec,
)


def _spec(proposal):
    return compile_spec(ArchitectureProposalReader().read(proposal))


def test_spec_serializes():
    spec = _spec({"proposal_id": "p1", "target": "revise_metabolism_thresholds",
                  "proposal": "raise overload threshold"})
    d = spec.to_dict()
    assert d["spec_id"] == "exp_p1"
    assert d["spec_type"] == ExperimentSpecType.METABOLISM_VARIANT
    assert d["tests_required"] and d["docs_required"]


def test_non_goals_present():
    spec = _spec({"proposal_id": "p1", "target": "revise_cognition_limits",
                  "proposal": "raise limit"})
    joined = " ".join(spec.non_goals).lower()
    assert "do not modify source files automatically" in joined
    assert "do not let solaris rewrite itself" in joined


def test_no_source_modification_capability():
    spec = _spec({"proposal_id": "p1", "target": "revise_sensorium_profiles",
                  "proposal": "broaden diet"})
    d = spec.to_dict()
    assert d["modifies_code"] is False
    assert d["creates_branch"] is False
    assert d["opens_pr"] is False


def test_unsafe_spec_is_blocked():
    spec = _spec({"proposal_id": "p2", "target": "actuate robot", "safe": False})
    assert spec.spec_type == ExperimentSpecType.BLOCKED
    assert spec.status == ExperimentSpecStatus.BLOCKED_BY_SAFETY
    assert spec.blocked is True


def test_inconclusive_spec_is_retest_only():
    spec = _spec({"proposal_id": "p3", "target": "revise_cognition",
                  "inconclusive": True, "missing_evidence": ["more runs"]})
    assert spec.spec_type == ExperimentSpecType.RETEST_ONLY
    assert spec.status == ExperimentSpecStatus.BLOCKED_BY_MISSING_EVIDENCE
