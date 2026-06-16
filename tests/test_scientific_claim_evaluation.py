"""Scientific claims <-> Evaluation: metrics computed; protocols return results."""

from __future__ import annotations

import tempfile

import pytest

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_NAMES = (
    "scientific_claims", "scientific_claims_protocol", "claim_registry_protocol",
    "theory_ledger_protocol", "evidence_mapping_protocol",
    "claim_strength_protocol", "counterevidence_protocol",
    "forbidden_claim_detection", "publication_dossier",
    "scientific_claim_safety",
)


def test_metrics_computed():
    metrics = M.scientific_claims_metrics({
        "scientific_claim_count": 3, "supported_claim_count": 1,
        "falsified_claim_count": 1, "publication_readiness_status": "inconclusive"})
    assert metrics["present"] is True
    assert metrics["scientific_claim_count"] == 3
    assert metrics["publication_readiness_status_count"] == 1
    assert metrics["is_consciousness_or_personhood"] is False


def test_metrics_absent():
    assert M.scientific_claims_metrics(None)["present"] is False


def test_protocols_registered():
    for name in _NAMES:
        assert name in PROTOCOLS


@pytest.mark.parametrize("name", _NAMES)
def test_protocol_returns_result(name):
    r = ExperimentRegistry()
    m = r.build_manifest("scientific_claims", {"state_dir": tempfile.mkdtemp()})
    result = PROTOCOLS[name](m)
    assert result.success, result.error
    assert "scientific_claims" in result.metrics


def test_feature_flag_set():
    r = ExperimentRegistry()
    m = r.build_manifest("scientific_claims")
    assert m.enabled_features.get("scientific_claims") is True
