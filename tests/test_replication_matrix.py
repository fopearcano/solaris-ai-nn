"""Replication matrix: built, statuses visible, no empty green dashboard."""

from __future__ import annotations

from solaris_ai_nn.developmental_replication import (
    ReplicationCellStatus,
    ReplicationMatrixBuilder,
)


def test_matrix_built():
    matrix = ReplicationMatrixBuilder().build(
        similarity_results=[{"run_a": "a", "run_b": "b",
                             "scores": {"concept_family_similarity": 0.9,
                                        "boundary_profile_similarity": 0.2}}],
        divergences=[{"run_a": "a", "run_b": "b",
                      "reason": "different_seed", "is_failure": False,
                      "evidence": "seed differs"}],
        falsification_results=[{"test_type": "fixture_overfit_probe",
                                "outcome": "falsified", "claim": "not overfit"}])
    d = matrix.to_dict()
    assert d["cell_count"] >= 3


def test_statuses_visible():
    matrix = ReplicationMatrixBuilder().build(
        similarity_results=[{"run_a": "a", "run_b": "b",
                             "scores": {"concept_family_similarity": 0.9,
                                        "boundary_profile_similarity": 0.2}}],
        divergences=[{"run_a": "a", "run_b": "b", "reason": "different_seed",
                      "is_failure": False, "evidence": ""}],
        falsification_results=[{"test_type": "fixture_overfit_probe",
                                "outcome": "falsified", "claim": "x"}])
    d = matrix.to_dict()
    assert d["replicated_claim_count"] >= 1
    assert d["diverged_claim_count"] >= 1
    assert d["falsified_claim_count"] >= 1
    assert d["falsified_claims"]  # falsified claims are prominent


def test_no_empty_green_dashboard():
    # Empty inputs must not yield an all-green dashboard; it yields inconclusive.
    matrix = ReplicationMatrixBuilder().build()
    d = matrix.to_dict()
    assert d["empty_green_dashboard"] is False
    assert d["inconclusive_claim_count"] >= 1


def test_inconclusive_status_when_no_scores():
    matrix = ReplicationMatrixBuilder().build(
        similarity_results=[{"run_a": "a", "run_b": "b", "scores": {}}])
    statuses = {c["status"] for c in matrix.to_dict()["cells"]}
    assert ReplicationCellStatus.INCONCLUSIVE in statuses
