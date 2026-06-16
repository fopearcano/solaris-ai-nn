"""Independent review <-> Evaluation: metrics computed; protocols return results."""

from __future__ import annotations

import tempfile

import pytest

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_NAMES = (
    "independent_review", "independent_review_protocol",
    "review_manifest_protocol", "artifact_sanitizer_protocol",
    "reviewer_pack_protocol", "reproducibility_challenge_protocol",
    "reviewer_question_protocol", "adversarial_review_protocol",
    "audit_matrix_protocol", "response_ledger_protocol",
    "review_readiness_protocol", "independent_review_safety",
)


def test_metrics_computed():
    metrics = M.independent_review_metrics({
        "independent_review_artifact_count": 22,
        "sanitizer_finding_count": 1, "alternative_explanation_count": 15,
        "review_readiness_status": "ready_for_internal_review"})
    assert metrics["present"] is True
    assert metrics["independent_review_artifact_count"] == 22
    assert metrics["alternative_explanation_count"] == 15
    assert metrics["is_consciousness_or_personhood"] is False


def test_metrics_absent():
    assert M.independent_review_metrics(None)["present"] is False


def test_protocols_registered():
    for name in _NAMES:
        assert name in PROTOCOLS


@pytest.mark.parametrize("name", _NAMES)
def test_protocol_returns_result(name):
    r = ExperimentRegistry()
    m = r.build_manifest("independent_review", {"state_dir": tempfile.mkdtemp()})
    result = PROTOCOLS[name](m)
    assert result.success, result.error
    assert "independent_review" in result.metrics


def test_feature_flag_set():
    r = ExperimentRegistry()
    m = r.build_manifest("independent_review")
    assert m.enabled_features.get("independent_review") is True
