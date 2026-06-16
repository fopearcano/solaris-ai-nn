"""Experiment test matrix: generated, safety blocking, missing blocks ready."""

from __future__ import annotations

from solaris_ai_nn.experiment_compiler import (
    ExperimentTestMatrix,
    TestCategory,
    TestMatrixRow,
    build_test_matrix,
)


def _matrix():
    return build_test_matrix({"spec_id": "exp_p1",
                              "target_modules": ["sensorium_lab"],
                              "spec_type": "sensorium_variant",
                              "evidence_refs": ["replication:ok"]})


def test_matrix_generated():
    matrix = _matrix()
    d = matrix.to_dict()
    assert d["row_count"] >= 5
    assert TestCategory.UNIT in d["categories_present"]
    assert TestCategory.INTEGRATION in d["categories_present"]


def test_safety_tests_blocking():
    matrix = _matrix()
    safety_rows = [r for r in matrix.rows if r.category == TestCategory.SAFETY]
    assert safety_rows
    assert all(r.blocking for r in safety_rows)
    claim_rows = [r for r in matrix.rows
                  if r.category == TestCategory.CLAIM_GUARD]
    assert claim_rows and all(r.blocking for r in claim_rows)


def test_missing_tests_block_readiness():
    # A matrix lacking a blocking category blocks ready status.
    matrix = ExperimentTestMatrix(spec_id="x")
    matrix.add(TestMatrixRow("tests/test_x.py", TestCategory.UNIT))
    assert matrix.blocks_ready is True
    assert TestCategory.SAFETY in matrix.missing_blocking_categories()


def test_full_matrix_does_not_block():
    matrix = _matrix()
    assert matrix.blocks_ready is False
