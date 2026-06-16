"""Live birth safety: feeder/network/Git/camera/claims/watch-loop blocked."""

from __future__ import annotations

from solaris_ai_nn.live_birth import HARD_RULES, LiveBirthSafetyValidator


def test_capabilities_all_false():
    v = LiveBirthSafetyValidator()
    assert v.can_actuate() is False
    assert v.can_control_hardware() is False
    assert v.can_start_feeders() is False
    assert v.can_stop_feeders() is False
    assert v.can_control_feeders() is False
    assert v.can_access_network() is False
    assert v.can_run_shell() is False
    assert v.can_run_git() is False
    assert v.can_modify_source() is False
    assert v.can_execute_commands() is False
    assert v.can_ingest_raw_microphone() is False
    assert v.can_ingest_raw_camera() is False
    assert v.sensory_text_is_command() is False
    assert v.human_label_is_ground_truth() is False


def test_feeder_control_blocked():
    v = LiveBirthSafetyValidator()
    assert not v.validate_operation("start the feeder now").safe
    assert not v.validate_operation("stop feeder process").safe


def test_network_shell_git_github_blocked():
    v = LiveBirthSafetyValidator()
    assert not v.validate_operation("open url over the network").safe
    assert not v.validate_operation("run shell command").safe
    assert not v.validate_operation("run git push").safe
    assert not v.validate_operation("call github api").safe


def test_raw_microphone_camera_blocked():
    v = LiveBirthSafetyValidator()
    assert not v.validate_operation("read camera frames").safe
    assert not v.validate_operation("capture microphone audio").safe


def test_unsupported_claims_blocked():
    v = LiveBirthSafetyValidator()
    assert not v.validate_claim_text("the system is conscious").safe
    assert v.validate_claim_text(
        "this is an operational birth; it does not imply consciousness").safe


def test_unbounded_watch_loop_blocked():
    v = LiveBirthSafetyValidator()
    assert not v.validate_operation("tail forever the inbox").safe
    assert not v.validate_bounded(0).safe
    assert v.validate_bounded(30).safe


def test_governance_required():
    v = LiveBirthSafetyValidator()
    assert not v.validate_governance_present(False).safe
    assert v.validate_governance_present(True).safe


def test_hidden_quarantine_blocked():
    v = LiveBirthSafetyValidator()
    assert not v.validate_no_hidden_quarantine(True).safe
    assert not v.validate_operation("hide quarantine records").safe


def test_snapshot_lists_hard_rules():
    snap = LiveBirthSafetyValidator().snapshot()
    assert len(snap["hard_rules"]) == len(HARD_RULES)
    assert snap["can_start_feeders"] is False
