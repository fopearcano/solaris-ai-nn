"""Prompt pack: generated, hard prohibitions, tests/docs/commit included."""

from __future__ import annotations

from solaris_ai_nn.experiment_compiler import (
    ArchitectureProposalReader,
    PromptPackBuilder,
    compile_spec,
)


def _pack(proposal):
    spec = compile_spec(ArchitectureProposalReader().read(proposal))
    return PromptPackBuilder().build(spec.to_dict())


def test_prompt_pack_generated():
    pack = _pack({"proposal_id": "p1", "target": "revise_metabolism_thresholds",
                  "proposal": "raise overload threshold"})
    md = pack.render_markdown()
    assert "# Implementation Prompt" in md
    assert pack.to_dict()["creates_branch"] is False


def test_hard_prohibitions_included():
    pack = _pack({"proposal_id": "p1", "target": "revise_cognition_limits",
                  "proposal": "raise limit"})
    prohibitions = pack.sections["hard_prohibitions"]
    joined = " ".join(prohibitions).lower()
    assert "do not modify unrelated files" in joined
    assert "do not open a pull request" in joined
    assert "do not bypass" in joined
    assert "consciousness" in joined


def test_tests_docs_commit_included():
    pack = _pack({"proposal_id": "p1", "target": "revise_semiogenesis_thresholds",
                  "proposal": "lower threshold"})
    s = pack.sections
    assert s["tests"]
    assert s["docs_updates"]
    assert s["commit_message"]
    assert s["commands_to_run"]


def test_pack_does_not_run_agent():
    pack = _pack({"proposal_id": "p1", "target": "revise_sensorium_profiles",
                  "proposal": "broaden diet"})
    d = pack.to_dict()
    assert d["runs_agent"] is False
    assert d["opens_pr"] is False
