"""Branch spec: generated, suggested name only, no Git operation performed."""

from __future__ import annotations

from solaris_ai_nn.experiment_compiler import (
    ArchitectureProposalReader,
    BranchSpecBuilder,
    compile_spec,
)


def _branch(proposal):
    spec = compile_spec(ArchitectureProposalReader().read(proposal))
    return BranchSpecBuilder().build(spec.to_dict())


def test_branch_spec_generated():
    branch = _branch({"proposal_id": "p1", "target": "revise_metabolism",
                      "proposal": "raise threshold"})
    md = branch.render_markdown()
    assert "# Branch Spec" in md
    assert branch.pr_title_suggestion
    assert branch.pr_body_draft
    assert branch.review_checklist
    assert branch.merge_blockers


def test_suggested_branch_name_only():
    branch = _branch({"proposal_id": "p1", "target": "revise_cognition_limits",
                      "proposal": "raise limit"})
    assert branch.suggested_branch_name.startswith("experiment/")
    d = branch.to_dict()
    assert d["branch_created"] is False
    assert d["pr_opened"] is False


def test_no_git_operation_in_source():
    import inspect

    from solaris_ai_nn.experiment_compiler import branch_spec

    src = inspect.getsource(branch_spec)
    assert "subprocess" not in src
    assert "git checkout" not in src
    assert "gh pr" not in src


def test_merge_blockers_include_safety_and_falsification():
    branch = _branch({"proposal_id": "p1", "target": "revise_sensorium",
                      "proposal": "broaden diet"})
    joined = " ".join(branch.merge_blockers).lower()
    assert "safety gate" in joined
    assert "falsified" in joined
