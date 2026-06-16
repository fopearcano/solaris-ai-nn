"""Compiler: soak/replication evidence refs + follow-up in validation plan."""

from __future__ import annotations

from solaris_ai_nn.experiment_compiler import ExperimentCompilerRuntime
from solaris_ai_nn.experiment_compiler import (
    ArchitectureProposalReader,
    build_validation_plan,
    compile_spec,
)
from solaris_ai_nn.experiment_compiler.validation_plan import ValidationStageId


def test_source_evidence_refs_included():
    spec = compile_spec(ArchitectureProposalReader().read({
        "proposal_id": "p1", "target": "revise_metabolism_thresholds",
        "proposal": "raise threshold",
        "evidence_refs": ["soak:POST_RUN_AUTOPSY",
                          "replication:REPLICATION_MATRIX",
                          "falsification:FALSIFICATION_REPORT"]}))
    assert "soak:POST_RUN_AUTOPSY" in spec.evidence_refs
    assert "replication:REPLICATION_MATRIX" in spec.evidence_refs
    assert "falsification:FALSIFICATION_REPORT" in spec.evidence_refs


def test_validation_plan_includes_soak_replication_followup():
    plan = build_validation_plan({"spec_id": "exp_p1"})
    ids = {s.stage_id for s in plan.stages}
    assert ValidationStageId.MINI_SOAK in ids
    assert ValidationStageId.FALSIFICATION_REPLAY in ids
    assert ValidationStageId.REPLICATION_REGISTRATION in ids


def test_compiled_spec_follow_up_requires_replication(tmp_path):
    rt = ExperimentCompilerRuntime(state_dir=str(tmp_path))
    rt.load_manifest(proposals=[{
        "proposal_id": "p1", "target": "revise_semiogenesis_thresholds",
        "proposal": "lower threshold", "evidence_refs": ["replication:ok"]}])
    rt.compile()
    spec = rt.compiled[0].spec
    joined = " ".join(spec.follow_up_requirements).lower()
    assert "replication" in joined or "soak" in joined
