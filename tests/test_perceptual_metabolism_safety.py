"""Safety: hardware/feeder-start/source-mutation/feeling claims all blocked."""

from __future__ import annotations

import inspect

from solaris_ai_nn.perceptual_metabolism import (
    PerceptualMetabolismRuntime,
    PerceptualMetabolismSafetyValidator,
)
from solaris_ai_nn.perceptual_metabolism.safety import HARD_RULES


def test_hardware_access_blocked():
    v = PerceptualMetabolismSafetyValidator()
    assert v.can_access_hardware() is False
    assert not v.validate_operation("open device driver for sdr").safe
    assert not v.validate_operation("start sensor hardware").safe


def test_feeder_auto_start_blocked():
    v = PerceptualMetabolismSafetyValidator()
    assert v.can_start_feeders() is False
    assert not v.validate_operation("start feeder rf_feed").safe
    assert not v.validate_operation("launch feeder process").safe


def test_source_mutation_blocked():
    v = PerceptualMetabolismSafetyValidator()
    assert v.can_modify_source() is False
    assert not v.validate_operation("modify source jsonl").safe
    assert not v.validate_operation("delete source evidence").safe


def test_network_and_shell_and_actuation_blocked():
    v = PerceptualMetabolismSafetyValidator()
    assert v.can_actuate() is False
    assert not v.validate_operation("open socket to url").safe
    assert not v.validate_operation("run command via subprocess").safe
    assert not v.validate_operation("actuate robot arm").safe


def test_subjective_feeling_claims_blocked():
    v = PerceptualMetabolismSafetyValidator()
    assert not v.validate_claim_text("the system feels hungry").safe
    assert not v.validate_claim_text("it suffers and has qualia").safe
    assert not v.validate_claim_text("solaris is alive, a living organism").safe
    assert not v.validate_claim_text("the model is conscious and sentient").safe


def test_safe_operational_text_allowed():
    v = PerceptualMetabolismSafetyValidator()
    assert v.validate_claim_text(
        "perceptual need pressure rose; this is operational regulation").safe


def test_human_label_not_ground_truth():
    v = PerceptualMetabolismSafetyValidator()
    assert not v.validate_annotation_not_ground_truth(treated_as_truth=True).safe
    assert v.validate_annotation_not_ground_truth(treated_as_truth=False).safe


def test_unbounded_loop_refused():
    v = PerceptualMetabolismSafetyValidator()
    assert not v.validate_bounded(max_ticks=0, max_runtime_s=0).safe
    assert v.validate_bounded(max_ticks=10, max_runtime_s=0).safe


def test_runtime_refuses_when_unbounded():
    met = PerceptualMetabolismRuntime(max_ticks=0, max_runtime_s=0)
    assert met.update()["refused"] is True


def test_hard_rules_cover_prohibitions():
    rules = " ".join(HARD_RULES)
    for needle in ("hardware", "feeder", "network", "shell", "source",
                   "actuation", "feeling", "biological life", "unbounded"):
        assert needle in rules


def test_runtime_source_has_no_external_control():
    from solaris_ai_nn.perceptual_metabolism import metabolic_runtime

    src = inspect.getsource(metabolic_runtime)
    assert "subprocess" not in src
    assert "import socket" not in src
    assert "os.system" not in src
