"""Golden run: steps generated, bounded, optional skip honestly, strict raw fail."""

from __future__ import annotations

from solaris_ai_nn.tester_fixture_spine import (
    GoldenRunBuilder,
    GoldenRunStatus,
    TesterFixtureDemoRuntime,
)


def test_golden_run_steps_generated(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    g = rt.golden_run.to_dict()
    names = {s["name"] for s in g["steps"]}
    assert "run_environmental_membrane" in names
    assert "run_membrane_integration_audit" in names
    assert "run_reproducibility_check" in names
    assert g["step_count"] == 17


def test_steps_are_bounded_and_ordered(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    indices = [s["index"] for s in rt.golden_run.to_dict()["steps"]]
    assert indices == sorted(indices)


def test_optional_stages_skip_honestly(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path),
                                  profile="fixture_membrane_only_v0")
    rt.run()
    g = rt.golden_run.to_dict()
    skipped = set(g["skipped_optional_steps"])
    assert "run_limited_ontogenesis" in skipped
    assert "run_limited_semiogenesis" in skipped
    assert "run_limited_cognition" in skipped
    # Skipped steps are explicitly marked, not hidden.
    onto = next(s for s in g["steps"] if s["name"] == "run_limited_ontogenesis")
    assert onto["status"] == GoldenRunStatus.SKIPPED_OPTIONAL


def test_clean_run_passes(tmp_path):
    rt = TesterFixtureDemoRuntime(state_dir=str(tmp_path))
    rt.run()
    assert rt.golden_run.overall_status in (
        GoldenRunStatus.PASS, GoldenRunStatus.PASS_WITH_WARNINGS)


def test_no_impression_strict_mode_blocks(tmp_path):
    # A fixture of only an unsafe command event -> all quarantined -> 0
    # impressions -> strict + require-membrane blocks (never a raw downstream
    # bypass).
    import json
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
    rt.run()
    gen = next(s for s in rt.golden_run.to_dict()["steps"]
               if s["name"] == "generate_sensory_impressions")
    assert gen["status"] == GoldenRunStatus.BLOCKED
    assert rt.blocked is True
