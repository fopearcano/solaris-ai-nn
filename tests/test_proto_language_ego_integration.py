"""Tests for ego classification of proto-symbols."""

from __future__ import annotations

from solaris_ai_nn.ego.self_model import SelfModel
from solaris_ai_nn.ego.self_report import SelfReportBuilder


def test_symbol_classified_as_internal_generated(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1"})
    result = model.attributor.attribute_event(
        {"source": "protolanguage", "kind": "proto_symbol",
         "payload": "ABS_0001"})
    assert result.category == "generated_by_solaris_ai_nn"
    assert result.is_internal
    assert any("not human speech" in r for r in result.reasons)
    assert any("not an operator command" in r for r in result.reasons)


def test_not_treated_as_speech_or_command(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1"})
    result = model.attributor.attribute_event(
        {"source": "protolanguage", "kind": "proto_symbol",
         "payload": "EXEC_INHIB_0001"})
    assert not result.is_executable_instruction
    assert not result.is_committed_action
    classification = model.classify_event(
        {"source": "protolanguage", "kind": "proto_symbol"})
    assert classification.origin == "internal"
    assert not classification.authorized_action


def test_offline_born_symbol_classified_offline(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1"})
    classification = model.classify_event(
        {"source": "protolanguage", "kind": "replay_symbol"},
        context={"offline_replay": True})
    assert classification.offline
    assert classification.evidence_status in ("simulated",
                                              "counterfactual")


def test_self_report_includes_proto_language_authority_false(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1"})
    model.proto_language_status = {
        "enabled": True, "symbol_count": 7,
        "stable_symbol_count": 2, "ambiguous_symbol_count": 1,
        "authority": False}
    report = SelfReportBuilder(model).to_dict()
    section = report["sections"]["proto_language_status"]
    assert section["enabled"] is True
    assert section["symbol_count"] == 7
    assert section["authority"] is False
    assert "not human speech" in section["note"]
    # Default: disabled, authority pinned False.
    fresh = SelfModel(state_dir=tmp_path / "f")
    assert fresh.proto_language_status["enabled"] is False
    assert fresh.summary()["proto_language_status"]["authority"] \
        is False
