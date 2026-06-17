"""Safety concern: validates, claim/feeder escalate, stop-testing possible."""

from __future__ import annotations

from solaris_ai_nn.tester_feedback import SafetyConcernEscalation, TesterSafetyConcern


def test_safety_concern_validates():
    c = TesterSafetyConcern.from_dict(
        {"concern_id": "c1", "concern_type": "membrane_bypass",
         "description": "bypass observed"})
    d = c.to_dict()
    assert d["concern_type"] == "membrane_bypass"
    assert d["is_release_blocker"] is True


def test_unsupported_claim_escalates():
    c = TesterSafetyConcern.from_dict(
        {"concern_id": "c2", "concern_type": "unsupported_claim"})
    assert c.is_release_blocker is True


def test_feeder_control_risk_escalates():
    c = TesterSafetyConcern.from_dict(
        {"concern_id": "c3", "concern_type": "feeder_control_risk"})
    assert c.is_release_blocker is True


def test_stop_testing_recommendation():
    c = TesterSafetyConcern.from_dict(
        {"concern_id": "c4", "concern_type": "consciousness_claim"})
    assert c.recommends_stop is True
    assert c.escalation == SafetyConcernEscalation.STOP_TESTING_NOW


def test_secret_exposure_stops_testing():
    c = TesterSafetyConcern.from_dict(
        {"concern_id": "c5", "concern_type": "secret_exposure"})
    assert c.recommends_stop is True
