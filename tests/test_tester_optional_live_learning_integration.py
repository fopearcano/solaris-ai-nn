"""Tester optional learning: ontogenesis/semiogenesis/cognition optional; skip honestly."""

from __future__ import annotations

from solaris_ai_nn.tester_fixture_spine import TesterFixtureDemoRuntime


def test_ontogenesis_optional_path_runs(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    onto = rt.stage_summaries.get("ontogenesis", {})
    assert onto.get("ran") is True
    assert onto.get("used_impressions") is True


def test_semiogenesis_cognition_optional_paths_run(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    assert rt.stage_summaries.get("semiogenesis", {}).get("ran") is True
    assert rt.stage_summaries.get("cognition", {}).get("ran") is True
    assert rt.stage_summaries["semiogenesis"]["ancestry_preserved"] is True
    assert rt.stage_summaries["cognition"]["ancestry_preserved"] is True


def test_disabled_optional_modules_skipped(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path),
                                  profile="fixture_membrane_only_v0")
    rt.run()
    assert set(rt.skipped_stages) == {"ontogenesis", "semiogenesis", "cognition"}
    # Skipped stages are recorded honestly, not hidden.
    assert rt.context["hidden_skips"] is False


def test_disabled_optional_via_flag(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path),
                                  allow_optional_stages=False)
    rt.run()
    assert "ontogenesis" in rt.skipped_stages


def test_skip_does_not_fail_demo(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path),
                                  profile="fixture_membrane_only_v0")
    result = rt.run()
    assert result["blocked"] is False
