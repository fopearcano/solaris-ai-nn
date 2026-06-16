"""Review assimilation <-> Evaluation: metrics computed; protocols return results."""

from __future__ import annotations

import tempfile

import pytest

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_NAMES = (
    "review_assimilation", "review_assimilation_protocol",
    "feedback_manifest_protocol", "objection_classifier_protocol",
    "reproduction_outcome_protocol", "claim_impact_protocol",
    "theory_impact_protocol", "evidence_gap_map_protocol",
    "review_driven_experiment_protocol", "claim_revision_protocol",
    "publication_readiness_revision_protocol", "review_assimilation_safety",
)


def test_metrics_computed():
    metrics = M.review_assimilation_metrics({
        "reviewer_objection_count": 3, "valid_objection_count": 1,
        "claim_falsification_count": 1,
        "publication_readiness_impact": "block_publication"})
    assert metrics["present"] is True
    assert metrics["reviewer_objection_count"] == 3
    assert metrics["trains_model"] is False
    assert metrics["is_consciousness_or_personhood"] is False


def test_metrics_absent():
    assert M.review_assimilation_metrics(None)["present"] is False


def test_protocols_registered():
    for name in _NAMES:
        assert name in PROTOCOLS


@pytest.mark.parametrize("name", _NAMES)
def test_protocol_returns_result(name):
    r = ExperimentRegistry()
    m = r.build_manifest("review_assimilation", {"state_dir": tempfile.mkdtemp()})
    result = PROTOCOLS[name](m)
    assert result.success, result.error
    assert "review_assimilation" in result.metrics


def test_feature_flag_set():
    r = ExperimentRegistry()
    m = r.build_manifest("review_assimilation")
    assert m.enabled_features.get("review_assimilation") is True
