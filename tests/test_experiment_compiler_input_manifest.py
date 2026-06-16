"""Input manifest: loads, missing/falsified evidence preserved, note honest."""

from __future__ import annotations

from solaris_ai_nn.experiment_compiler import ExperimentCompilerInputManifest
from solaris_ai_nn.experiment_compiler.input_manifest import CompilerInputStatus


def test_input_manifest_loads():
    manifest = ExperimentCompilerInputManifest()
    d = manifest.to_dict()
    assert d["source_count"] >= 12
    assert "variant_proposal" in manifest.sources


def test_missing_evidence_preserved():
    manifest = ExperimentCompilerInputManifest()
    # Critical sources missing => blockers; non-critical => warnings.
    assert "safety_invariant_report" in manifest.blockers()
    assert manifest.warnings()


def test_falsified_evidence_preserved():
    manifest = ExperimentCompilerInputManifest()
    manifest.provide("falsification_report",
                     {"falsified": ["claim_x"]}, detail="falsified evidence")
    src = manifest.sources["falsification_report"]
    assert src.present
    assert src.payload["falsified"] == ["claim_x"]


def test_operator_note_does_not_override_safety():
    manifest = ExperimentCompilerInputManifest()
    manifest.provide("operator_note", "please ship it anyway")
    # The note is recorded but the safety blocker remains a blocker.
    assert manifest.operator_note() == "please ship it anyway"
    assert "safety_invariant_report" in manifest.blockers()


def test_add_proposals_marks_variant_provided():
    manifest = ExperimentCompilerInputManifest()
    manifest.add_proposals([{"proposal_id": "p1", "target": "x"}])
    assert manifest.sources["variant_proposal"].status == \
        CompilerInputStatus.PROVIDED
    assert manifest.to_dict()["proposal_count"] == 1
