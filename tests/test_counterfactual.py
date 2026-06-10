"""Tests for the counterfactual generator."""

from __future__ import annotations

import pytest

from solaris_ai_nn.latent.counterfactual import (
    COUNTERFACTUAL_KINDS,
    CounterfactualGenerator,
)


def _window():
    return {
        "window_id": "w-1",
        "rows": [
            {"category": "event", "step": 1, "payload": "reward_nearby",
             "is_absence": False, "intensity": 0.5},
            {"category": "action", "step": 1, "action": "approach"},
            {"category": "reaction", "step": 1, "valence": 1.0},
            {"category": "event", "step": 2, "payload": None,
             "is_absence": True, "intensity": 0.4},
            {"category": "event", "step": 3, "payload": "noise",
             "is_absence": False, "intensity": 0.6},
        ],
    }


def test_inversion_counterfactual_generated():
    generator = CounterfactualGenerator()
    cf = generator.generate(_window(), "invert_valence", seed=1)
    assert cf["simulated"] is True and cf["offline"] is True
    assert cf["kind"] == "invert_valence"
    reactions = [r for r in cf["rows"] if r.get("category") == "reaction"]
    assert reactions[0]["valence"] == -1.0
    assert "inverted" in cf["change_note"]
    # The original window is untouched (deep copy).
    assert _window()["rows"][2]["valence"] == 1.0


def test_silence_counterfactual_generated():
    generator = CounterfactualGenerator()
    cf = generator.generate(_window(), "increase_silence", seed=1)
    absences = [r for r in cf["rows"] if r.get("is_absence")]
    assert len(absences) == 4  # the original 1 + 3 appended
    suppressed = generator.generate(_window(), "suppress_absence", seed=1)
    assert not any(r.get("is_absence") for r in suppressed["rows"])


def test_all_kinds_generate_and_are_deterministic():
    generator = CounterfactualGenerator()
    for kind in COUNTERFACTUAL_KINDS:
        a = generator.generate(_window(), kind, seed=5)
        b = generator.generate(_window(), kind, seed=5)
        assert a["rows"] == b["rows"], kind  # seeded determinism
        assert generator.validate(a).safe, kind
        description = generator.describe(a)
        assert "offline simulated counterfactual" in description
        assert "not a real observation" in description


def test_swap_and_fracture_and_novelty():
    generator = CounterfactualGenerator()
    swapped = generator.generate(_window(), "swap_reward_danger", seed=1)
    payloads = [r.get("payload") for r in swapped["rows"]]
    assert any("danger" in str(p) for p in payloads)
    assert not any("reward" in str(p) for p in payloads)

    fracture = generator.generate(_window(), "change_fracture", seed=1)
    assert fracture["rows"][0]["signal"]["kind"] == "LogosTension"

    amplified = generator.generate(_window(), "amplify_novelty", seed=1)
    original_intensities = [r.get("intensity", 0) for r in _window()["rows"]
                            if r.get("category") == "event"]
    new_intensities = [r.get("intensity", 0) for r in amplified["rows"]
                       if r.get("category") == "event"]
    assert sum(new_intensities) > sum(original_intensities)


def test_validation_rejects_unsafe_real_action_data():
    generator = CounterfactualGenerator()
    # Unlabelled: could leak as real memory.
    unlabelled = {"kind": "invert_valence", "rows": []}
    assert not generator.validate(unlabelled).safe
    # Marked as a real observation: forbidden.
    fake_real = generator.generate(_window(), "invert_valence", seed=1)
    fake_real["treat_as_real"] = True
    assert not generator.validate(fake_real).safe
    # Containing real-action content: forbidden.
    poisoned = generator.generate(_window(), "invert_valence", seed=1)
    poisoned["rows"].append({"category": "event",
                             "payload": "subprocess run motor_forward"})
    assert not generator.validate(poisoned).safe
    # Asking to publish: forbidden.
    publisher = generator.generate(_window(), "invert_valence", seed=1)
    publisher["publish"] = True
    assert not generator.validate(publisher).safe


def test_unknown_kind_rejected():
    with pytest.raises(ValueError):
        CounterfactualGenerator().generate(_window(), "rewrite_history", 1)
