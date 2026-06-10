"""Tests for the pilot manifest and safety contract."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.pilot.pilot_manifest import (
    PilotManifest,
    PilotSafetyContract,
)


def test_manifest_serializes(tmp_path):
    manifest = PilotManifest(
        profile="read_only_stream", operator="alice",
        state_dir=str(tmp_path / "state"),
        artifact_dir=str(tmp_path / "pilots"),
        input_sources=["a.jsonl"], max_steps=100, notes="test")
    data = manifest.to_dict()
    json.dumps(data)  # JSON-safe
    for key in ("pilot_id", "profile", "created_at", "run_id", "session_id",
                "operator", "state_dir", "artifact_dir", "input_sources",
                "output_policy", "max_steps", "max_duration_s", "substrate",
                "enabled_features", "governance_approval_ids",
                "emergency_stop_path", "expected_artifacts", "notes",
                "safety_contract", "environment"):
        assert key in data, key
    clone = PilotManifest.from_dict(data)
    assert clone.pilot_id == manifest.pilot_id
    assert clone.contract.is_intact()


def test_safety_contract_includes_forbidden_actions():
    contract = PilotSafetyContract()
    assert contract.is_intact()
    statements = " ".join(contract.statements()).lower()
    for phrase in ("read-only", "network", "os commands", "browser",
                   "physical actuation", "solaris_ai actions",
                   "source-code", "unbounded"):
        assert phrase in statements, phrase
    fields = contract.to_dict()
    for key in ("no_network_calls", "no_os_commands",
                "no_browser_automation", "no_physical_actuation",
                "no_committed_solaris_actions", "no_source_code_rewriting",
                "no_unbounded_run_without_approval"):
        assert fields[key] is True, key


def test_unbounded_pilot_rejected_without_approval():
    with pytest.raises(ValueError):
        PilotManifest(profile="simulated", max_steps=None,
                      max_duration_s=None)
    # With explicit governance approval ids it is constructible.
    manifest = PilotManifest(profile="simulated", max_steps=None,
                             max_duration_s=None,
                             governance_approval_ids=["appr-123"])
    assert not manifest.is_bounded()


def test_weakened_contract_rejected():
    with pytest.raises(ValueError):
        PilotManifest(profile="simulated", max_steps=10,
                      contract=PilotSafetyContract(no_network_calls=False))


def test_emergency_stop_path_defaults_to_sentinel(tmp_path):
    manifest = PilotManifest(profile="simulated", max_steps=10,
                             state_dir=str(tmp_path / "state"))
    assert manifest.emergency_stop_path.endswith("EMERGENCY_STOP")
    assert str(tmp_path / "state") in manifest.emergency_stop_path


def test_unknown_profile_rejected():
    with pytest.raises(ValueError):
        PilotManifest(profile="full_autonomy", max_steps=10)
