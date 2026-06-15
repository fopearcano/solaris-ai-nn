"""ArchitectureReviewReportBuilder: JSON+MD; ClaimGuard; limitations."""

from __future__ import annotations

import os

from solaris_ai_nn.architecture_evolution import (
    ArchitectureReviewReportBuilder,
    ModuleInventory,
)


def _build(tmp_path):
    return ArchitectureReviewReportBuilder(
        base_dir=str(tmp_path)).build_and_write(
        inventory=ModuleInventory(),
        lifecycle_assessments={
            "ego": {"lifecycle_class": "safety_critical_do_not_prune"},
            "latent": {"lifecycle_class": "candidate_for_pruning"},
            "world_model": {"lifecycle_class": "core_keep"}})


def test_json_report_generated(tmp_path):
    _build(tmp_path)
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "ARCHITECTURE_REVIEW.json"))


def test_markdown_generated(tmp_path):
    _build(tmp_path)
    assert os.path.exists(os.path.join(str(tmp_path),
                                       "ARCHITECTURE_REVIEW.md"))


def test_claim_guard_scans_report(tmp_path):
    report = _build(tmp_path)
    assert report.claim_guard_safe is True


def test_limitations_included(tmp_path):
    report = _build(tmp_path)
    joined = " ".join(report.sections["limitations"]).lower()
    assert "recommendation-only" in joined
    assert "no code is modified" in joined
    assert "safety-critical modules cannot be pruned" in joined


def test_keep_and_prune_lists(tmp_path):
    report = _build(tmp_path)
    assert "world_model" in report.sections["modules_to_keep"]
    assert "latent" in report.sections["modules_candidate_for_pruning"]
    assert "ego" in report.sections["modules_blocked_from_pruning"]
