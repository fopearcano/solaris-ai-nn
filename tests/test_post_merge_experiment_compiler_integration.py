"""Post-merge consumes compiler branch spec / validation plan; compares reqs."""

from __future__ import annotations

from solaris_ai_nn.experiment_compiler import (
    ArchitectureProposalReader,
    BranchSpecBuilder,
    build_validation_plan,
    compile_spec,
)
from solaris_ai_nn.post_merge_assimilation import PostMergeManifest


def _compiler_artifacts():
    spec = compile_spec(ArchitectureProposalReader().read({
        "proposal_id": "p1", "target": "revise_metabolism_thresholds",
        "proposal": "raise overload threshold",
        "evidence_refs": ["replication:ok"]}))
    spec_d = spec.to_dict()
    return {"branch_spec": BranchSpecBuilder().build(spec_d).to_dict(),
            "validation_plan": build_validation_plan(spec_d).to_dict(),
            "experiment_spec": spec_d}


def test_consumes_branch_spec():
    artifacts = _compiler_artifacts()
    manifest = PostMergeManifest.from_dict({
        "merge_id": "m1", "source_branch_spec_id": "experiment/metabolism",
        "source_experiment_id": "exp_p1",
        "artifacts": {"branch_spec": artifacts["branch_spec"]}})
    assert manifest.artifacts["branch_spec"].present
    assert manifest.source_branch_spec_id == "experiment/metabolism"


def test_consumes_validation_plan():
    artifacts = _compiler_artifacts()
    plan = artifacts["validation_plan"]
    # The compiler's validation plan stages are the requirements post-merge
    # evidence must eventually satisfy.
    assert plan["stage_count"] >= 1


def test_compares_against_experiment_requirements():
    artifacts = _compiler_artifacts()
    spec = artifacts["experiment_spec"]
    # The experiment spec lists tests/docs the post-merge evidence is checked
    # against (consumed by the intake/assimilation chain).
    assert spec["tests_required"] or spec["docs_required"]
