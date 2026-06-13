"""Tests for the LOGOS tension model."""

from __future__ import annotations

import pytest

from solaris_ai_nn.logos_complexity.tension import (
    LogosTension,
    TensionPolarity,
    TensionSeverity,
    TensionStatus,
    TensionType,
)


def test_eighteen_tension_types():
    assert len(TensionType.ALL) == 18


def test_twelve_statuses():
    assert len(TensionStatus.ALL) == 12


def test_tension_serializes():
    t = LogosTension(tension_type=TensionType.KNOWN_UNKNOWN,
                     polarity_a=TensionPolarity.KNOWN,
                     polarity_b=TensionPolarity.UNKNOWN)
    data = t.to_dict()
    assert data["tension_type"] == "known_unknown"
    assert data["evidence_ok"] is True  # watch needs no evidence
    assert data["tension_id"].startswith("TEN_")


def test_warning_requires_evidence():
    t = LogosTension(tension_type=TensionType.WORLD_MODEL_CONTRADICTION,
                     polarity_a=TensionPolarity.SUPPORT,
                     polarity_b=TensionPolarity.CONTRADICTION,
                     severity=TensionSeverity.WARNING)
    assert t.evidence_ok is False
    t2 = LogosTension(tension_type=TensionType.WORLD_MODEL_CONTRADICTION,
                      polarity_a=TensionPolarity.SUPPORT,
                      polarity_b=TensionPolarity.CONTRADICTION,
                      severity=TensionSeverity.HIGH,
                      evidence_refs=["e"])
    assert t2.evidence_ok is True


def test_safety_dominant_flag():
    t = LogosTension(tension_type=TensionType.NEED_SAFETY,
                     polarity_a=TensionPolarity.NEED,
                     polarity_b=TensionPolarity.SAFETY)
    assert t.is_safety_dominant is True
    t2 = LogosTension(tension_type=TensionType.KNOWN_UNKNOWN,
                      polarity_a=TensionPolarity.KNOWN,
                      polarity_b=TensionPolarity.UNKNOWN)
    assert t2.is_safety_dominant is False


def test_unknown_type_rejected():
    with pytest.raises(ValueError):
        LogosTension(tension_type="cosmic_dread", polarity_a="a",
                     polarity_b="b")


def test_set_status():
    t = LogosTension(tension_type=TensionType.SYMBOL_AMBIGUITY,
                     polarity_a=TensionPolarity.STABLE,
                     polarity_b=TensionPolarity.AMBIGUOUS)
    t.set_status(TensionStatus.PRESERVED)
    assert t.status == "preserved"
    with pytest.raises(ValueError):
        t.set_status("transcended")
