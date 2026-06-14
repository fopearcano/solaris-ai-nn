"""ResearchReproducibilityBuilder: package + checksum manifest + labels."""

from __future__ import annotations

import os

from solaris_ai_nn.research_lab import (
    ExperimentDesign,
    ResearchMetricsSuite,
    ResearchReproducibilityBuilder,
    ResearchResultStore,
)


def test_package_generated(tmp_path):
    design = ExperimentDesign(title="t", research_question="q",
                             base_dir=str(tmp_path))
    pkg = ResearchReproducibilityBuilder(base_dir=str(tmp_path)).build(
        design=design, result_store=ResearchResultStore(base_dir=str(tmp_path)),
        metrics=ResearchMetricsSuite())
    assert pkg.sections["experiment_design"]
    assert pkg.sections["module_availability"]
    assert pkg.sections["reproduction_instructions"]


def test_checksum_manifest_created(tmp_path):
    design = ExperimentDesign(title="t", research_question="q",
                             base_dir=str(tmp_path))
    builder = ResearchReproducibilityBuilder(base_dir=str(tmp_path))
    pkg = builder.build_and_write(
        design=design, result_store=ResearchResultStore(base_dir=str(tmp_path)),
        metrics=ResearchMetricsSuite())
    repro_dir = os.path.join(str(tmp_path), "reproducibility")
    assert os.path.exists(os.path.join(repro_dir, "checksum_manifest.json"))
    assert "paths" in pkg.sections


def test_data_labels_preserved(tmp_path):
    design = ExperimentDesign(title="t", research_question="q",
                             base_dir=str(tmp_path))
    pkg = ResearchReproducibilityBuilder(base_dir=str(tmp_path)).build(
        design=design, result_store=ResearchResultStore(base_dir=str(tmp_path)))
    assert set(pkg.sections["data_labels"]) == {
        "fixture", "simulated", "read_only", "sandbox_only"}
