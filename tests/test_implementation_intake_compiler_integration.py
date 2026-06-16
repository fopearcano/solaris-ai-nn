"""Intake consumes experiment-compiler artifacts (prompt/branch/tests/gates)."""

from __future__ import annotations

from solaris_ai_nn.experiment_compiler import (
    ArchitectureProposalReader,
    BranchSpecBuilder,
    PromptPackBuilder,
    SafetyGateEvaluator,
    build_test_matrix,
    compile_spec,
)
from solaris_ai_nn.implementation_intake import ImplementationIntakeRuntime


def _compiler_artifacts():
    spec = compile_spec(ArchitectureProposalReader().read({
        "proposal_id": "p1", "target": "revise_metabolism_thresholds",
        "proposal": "raise overload threshold",
        "evidence_refs": ["replication:ok"]}))
    spec_d = spec.to_dict()
    gates = SafetyGateEvaluator()
    return {
        "implementation_prompt": PromptPackBuilder().build(spec_d).to_dict(),
        "branch_spec": BranchSpecBuilder().build(spec_d).to_dict(),
        "test_matrix": build_test_matrix(spec_d).to_dict(),
        "safety_gates": gates.summary(gates.evaluate(spec_d)),
    }


def _runtime(tmp_path):
    artifacts = _compiler_artifacts()
    bundle = dict(artifacts)
    bundle.update({
        "implementation_summary": "implemented; does not prove life",
        "changed_file_list": ["src/solaris_ai_nn/perceptual_metabolism/x.py"],
        "patch_file": "+++ b/src/x.py\n+def f():\n+    return 1\n",
        "test_results": {"passed": 3, "failed": 0,
                         "by_category": {"safety": {"passed": True},
                                         "claim_guard": {"passed": True}}},
        "claimguard_results": {"safe": True},
        "safety_invariant_results": {"passed": True}})
    rt = ImplementationIntakeRuntime(state_dir=str(tmp_path))
    rt.load_manifest(bundle)
    rt.run()
    return rt


def test_consumes_prompt_pack_and_branch_spec(tmp_path):
    rt = _runtime(tmp_path)
    assert rt.manifest.get("implementation_prompt") is not None
    assert rt.manifest.get("branch_spec") is not None
    # The reference spec is derived from the compiler artifacts.
    ref = rt._reference_spec()
    assert ref["proposed_changes"] or ref["tests_required"]


def test_consumes_test_matrix_and_safety_gates(tmp_path):
    rt = _runtime(tmp_path)
    assert rt.manifest.get("test_matrix") is not None
    gate_ids = rt._safety_gate_ids()
    assert gate_ids  # extracted from the compiler's safety-gate summary


def test_audit_runs_against_compiler_reference(tmp_path):
    rt = _runtime(tmp_path)
    assert rt.spec_compliance["item_count"] >= 1
    assert "status" in rt.merge
