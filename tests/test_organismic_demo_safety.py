"""OrganismicDemoSafetyValidator: hardware/network/debug-leak/unbounded blocked."""

from __future__ import annotations

from solaris_ai_nn.organismic_demo import OrganismicDemoSafetyValidator
from solaris_ai_nn.organismic_demo.safety import DEBUG_TRUTH_FILENAME, HARD_RULES


def test_hardware_access_blocked():
    v = OrganismicDemoSafetyValidator()
    assert v.validate_operation("open device driver").safe is False
    assert v.validate_operation("control sensor over sdr").safe is False
    assert v.can_access_hardware() is False


def test_network_and_shell_blocked():
    v = OrganismicDemoSafetyValidator()
    assert v.validate_operation("http download").safe is False
    assert v.validate_operation("run shell command").safe is False


def test_debug_truth_leakage_blocked():
    v = OrganismicDemoSafetyValidator()
    assert v.validate_sensory_roots(
        [f"x/{DEBUG_TRUTH_FILENAME}"]).safe is False
    assert v.validate_no_debug_leakage(
        ["a/rf.jsonl", f"a/{DEBUG_TRUTH_FILENAME}"]).safe is False
    assert v.validate_no_debug_leakage(["a/rf.jsonl"]).safe is True


def test_sensory_text_command_blocked():
    v = OrganismicDemoSafetyValidator()
    # Sensory text is observation only; the demo never executes it.
    assert v.validate_text_not_command("delete everything now").safe is True


def test_unbounded_runtime_blocked():
    v = OrganismicDemoSafetyValidator()
    assert v.validate_runtime_bounded(0, 0, 0).safe is False
    assert v.validate_runtime_bounded(120, 60.0, 500).safe is True


def test_actuation_blocked_and_rules_present():
    v = OrganismicDemoSafetyValidator()
    assert v.validate_operation("real_world actuate").safe is False
    assert "no hardware access" in HARD_RULES
    assert "no hidden debug-truth leakage into perception" in HARD_RULES
