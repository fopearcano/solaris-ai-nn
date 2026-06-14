"""ConsentBoundary: template generated; no implied consent; text isn't consent."""

from __future__ import annotations

from solaris_ai_nn.pilot4_planning import ConsentBoundary, ConsentRecordTemplate


def test_consent_template_generated():
    cb = ConsentBoundary()
    snap = cb.snapshot()
    assert snap["questions"]
    for q in ("who authorizes the actuator", "how consent is revoked",
              "how emergency stop works"):
        assert q in snap["questions"]


def test_no_implied_consent():
    t = ConsentRecordTemplate()
    assert t.implied_consent_allowed is False
    assert ConsentBoundary().snapshot()["implied_consent_allowed"] is False


def test_sensory_text_not_consent():
    cb = ConsentBoundary()
    assert cb.is_consent("sensory_text") is False
    assert cb.is_consent("operator_feedback") is False
    assert cb.is_consent("explicit_consent_record") is True


def test_completeness_tracks_answers():
    cb = ConsentBoundary()
    assert cb.complete is False
    for q in list(cb.snapshot()["questions"]):
        cb.answer(q, "answered")
    assert cb.complete is True
    assert cb.completeness == 1.0
