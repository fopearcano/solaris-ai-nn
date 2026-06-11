"""Tests for ego attribution of LLM output."""

from __future__ import annotations

from solaris_ai_nn.ego.self_model import SelfModel
from solaris_ai_nn.ego.self_report import SelfReportBuilder


def test_llm_output_attributed_as_paraphrase(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1"})
    result = model.attributor.attribute_event(
        {"source": "llm_adapter", "kind": "paraphrase",
         "payload": "In plain terms: steps=5."})
    assert result.category == "generated_by_llm_adapter"
    assert any("not primary evidence" in r for r in result.reasons)
    assert any("not system authority" in r for r in result.reasons)


def test_llm_not_primary_evidence(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1"})
    classification = model.classify_event(
        {"source": "llm_adapter", "kind": "paraphrase"})
    assert classification.attribution == "generated_by_llm_adapter"
    # Neither observed external evidence nor an authorized action.
    assert classification.evidence_status != "observed"
    assert not classification.authorized_action


def test_self_report_includes_llm_authority_false(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1"})
    model.llm_status = {"enabled": True, "adapter": "mock",
                        "last_paraphrased": True,
                        "grounding_status": "ok",
                        "fallback_count": 0, "authority": False}
    report = SelfReportBuilder(model).to_dict()
    section = report["sections"]["llm_adapter_status"]
    assert section["enabled"] is True
    assert section["adapter"] == "mock"
    assert section["authority"] is False
    assert "never primary evidence" in section["note"]
    # The summary carries it too, with authority pinned False.
    assert model.summary()["llm_status"]["authority"] is False


def test_default_llm_status_disabled(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    assert model.llm_status == {"enabled": False, "adapter": None,
                                "authority": False}
    report = SelfReportBuilder(model).to_dict()
    assert report["sections"]["llm_adapter_status"]["enabled"] is False
