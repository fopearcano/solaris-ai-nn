"""Tester live-birth/observation: validation/quarantine path, observation diets."""

from __future__ import annotations

from solaris_ai_nn.tester_fixture_spine import TesterFixtureDemoRuntime


def test_fixture_validation_quarantine_path(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    assert rt.fixture_validation["valid"] is True
    # The unsafe command-like fixture event is quarantined, not learned.
    assert any(q.get("event_id") == "fx_unsafe_command"
               for q in rt.quarantine_records)


def test_unsafe_fixture_event_quarantined(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    assert rt.context["unsafe_quarantined"] is True
    assert len(rt.quarantine_records) >= 1


def test_observation_consumes_impressions(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    obs = rt.stage_summaries["observation"]
    assert obs["used_impressions"] is True
    assert obs["distinguishes_event_and_impression_diet"] is True
    assert obs["impression_diet"]


def test_observation_distinguishes_event_vs_impression_diet(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    obs = rt.stage_summaries["observation"]
    assert "impression_diet" in obs and "event_diet" in obs


def test_operator_pulse_attenuated(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    assert rt.context["operator_pulse_attenuated"] is True
