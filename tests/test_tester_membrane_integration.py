"""Tester membrane integration: uses membrane, missing blocks strict, audit runs."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.tester_fixture_spine import TesterFixtureDemoRuntime


def test_tester_demo_uses_membrane(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    assert rt.context["membrane_present"] is True
    impressions = os.path.join(rt.run_dir, "membrane", "impressions",
                               "SENSORY_IMPRESSIONS.jsonl")
    assert os.path.isfile(impressions)


def test_sensory_impressions_produced(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    assert rt.membrane_status["membrane_impression_count"] >= 1
    assert rt.context["all_impressions_have_receptor"] is True
    assert rt.context["all_impressions_have_source_ref"] is True


def test_membrane_integration_audit_runs(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    assert rt.integration_status.get("membrane_integration_enabled") is True
    assert "pipeline_status" in rt.integration_status
    # No raw event bypass on a clean fixture run.
    assert rt.context["raw_bypass_detected"] is False


def test_missing_membrane_blocks_strict(tmp_path):
    # All events quarantined -> no impressions -> strict + require-membrane block.
    fixture = tmp_path / "only_unsafe.jsonl"
    fixture.write_text(json.dumps({
        "event_id": "fx_unsafe_command", "source_id": "operator_pulse",
        "modality": "pulse", "channel": "operator/pulse", "read_only": True,
        "is_command": True, "payload": {"pulse": 1},
        "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": False,
                    "is_noisy": False},
        "safety": {"private_data": False, "contains_instruction": True,
                   "contains_secret": False, "allow_learning": False},
        "fixture_kind": "unsafe_command"}) + "\n")
    rt = TesterFixtureDemoRuntime(
        state_dir=str(tmp_path), fixture_pack_path=str(fixture), strict=True)
    result = rt.run()
    assert result["blocked"] is True
