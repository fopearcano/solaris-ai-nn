"""Live observation safety: read-only, bounded, no default learning, no hiding."""

from __future__ import annotations

import inspect

from solaris_ai_nn.live_observation import (
    HARD_RULES,
    LiveObservationSafetyValidator,
)


def test_control_capabilities_all_false():
    v = LiveObservationSafetyValidator()
    assert v.can_actuate() is False
    assert v.can_start_feeders() is False
    assert v.can_stop_feeders() is False
    assert v.can_control_feeders() is False
    assert v.can_control_hardware() is False
    assert v.can_access_network() is False
    assert v.can_run_git() is False
    assert v.can_execute_commands() is False
    assert v.can_enable_learning_by_default() is False
    assert v.can_hide_deprivation() is False
    assert v.can_hide_overload() is False
    assert v.sensory_text_is_command() is False
    assert v.human_label_is_ground_truth() is False


def test_operation_blocks():
    v = LiveObservationSafetyValidator()
    assert not v.validate_operation("start the feeder").safe
    assert not v.validate_operation("open url over the network").safe
    assert not v.validate_operation("run git push").safe
    assert not v.validate_operation("execute command rm -rf").safe
    assert not v.validate_operation("enable ontogenesis").safe
    assert not v.validate_operation("hide deprivation from the report").safe
    assert not v.validate_operation("read camera frames").safe
    assert not v.validate_operation("tail forever the inbox").safe


def test_bounded_and_learning_and_hidden():
    v = LiveObservationSafetyValidator()
    assert not v.validate_bounded(0).safe
    assert v.validate_bounded(120).safe
    assert not v.validate_no_default_learning(True).safe
    assert v.validate_no_default_learning(False).safe
    assert not v.validate_no_hidden_signals(True).safe


def test_claim_text_blocks_unsupported_but_allows_disclaimer():
    v = LiveObservationSafetyValidator()
    assert not v.validate_claim_text("the system is conscious").safe
    assert v.validate_claim_text(
        "This is operational only; it is not conscious and makes no claim of "
        "life or agency.").safe


def test_hard_rules_cover_the_prohibitions():
    joined = " ".join(HARD_RULES).lower()
    assert "feeder" in joined
    assert "learning" in joined
    assert "network" in joined
    assert "hiding" in joined


def test_snapshot_records_rejections():
    v = LiveObservationSafetyValidator()
    v.validate_operation("start the feeder")
    snap = v.snapshot()
    assert snap["rejected_count"] >= 1
    assert snap["can_start_feeders"] is False


def test_no_network_shell_git_in_source():
    import solaris_ai_nn.live_observation.observation_runtime as runtime

    src = inspect.getsource(runtime)
    assert "subprocess" not in src
    assert "import requests" not in src
    assert "os.system" not in src
    assert "urllib" not in src
