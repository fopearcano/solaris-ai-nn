"""Live observation assessments: overload/deprivation, metabolism, stability gate."""

from __future__ import annotations

from solaris_ai_nn.live_observation import (
    LiveOverloadDeprivationAssessor,
    LiveStabilityGate,
    PerceptualMetabolismCalibrator,
)


def _window(accepted, peak=0.0, overload_markers=None):
    return {"summary": {"accepted_event_count": accepted,
                        "peak_event_rate_per_min": peak},
            "overload_markers": overload_markers or []}


def _health(count=3, healthy=3, silent=0, forbidden=0, noisy=0):
    return {"live_source_count": count, "live_healthy_source_count": healthy,
            "live_silent_source_count": silent,
            "live_forbidden_source_count": forbidden,
            "live_noisy_source_count": noisy}


def test_severe_overload_blocks_ontogenesis():
    a = LiveOverloadDeprivationAssessor().assess(
        windows=[_window(50, peak=600.0,
                         overload_markers=["peak_event_rate_too_high"])],
        source_health_summary=_health(),
        source_diet={"total_events": 50, "balance": "balanced"},
        absence={"deprivation_window_count": 0}).to_dict()
    assert a["load_status"] == "severe_overload"
    assert a["blocks_ontogenesis_recommendation"] is True


def test_severe_deprivation_blocks_ontogenesis():
    a = LiveOverloadDeprivationAssessor().assess(
        windows=[_window(0)],
        source_health_summary=_health(count=3, healthy=0, silent=3),
        source_diet={"total_events": 0, "balance": "empty"},
        absence={"deprivation_window_count": 3}).to_dict()
    assert a["load_status"] == "severe_deprivation"
    assert a["blocks_ontogenesis_recommendation"] is True


def test_mixed_requires_operator_review():
    a = LiveOverloadDeprivationAssessor().assess(
        windows=[_window(30, peak=200.0,
                         overload_markers=["peak_event_rate_too_high"])],
        source_health_summary=_health(count=3, healthy=1, silent=2),
        source_diet={"total_events": 30, "balance": "single_source"},
        absence={"deprivation_window_count": 1}).to_dict()
    assert a["load_status"] == "mixed"
    assert a["requires_operator_review"] is True


def test_no_feeder_change_flag():
    a = LiveOverloadDeprivationAssessor().assess(
        windows=[_window(50, peak=600.0,
                         overload_markers=["peak_event_rate_too_high"])],
        source_health_summary=_health(),
        source_diet={"total_events": 50, "balance": "balanced"},
        absence={"deprivation_window_count": 0}).to_dict()
    for m in a["overload_markers"]:
        assert m["triggers_feeder_change"] is False


def test_metabolism_calibration_is_report_only():
    cal = PerceptualMetabolismCalibrator().calibrate(
        source_health_summary=_health(),
        source_diet={"live_source_diet_dominance_score": 0.3,
                     "live_operator_pulse_dominance_score": 0.1,
                     "human_text_proportion": 0.2},
        rhythm={"rhythm_pattern_count": 2},
        absence={"deprivation_window_count": 0},
        load={"load_status": "stable",
              "blocks_ontogenesis_recommendation": False}).to_dict()
    assert cal["applied"] is False
    assert cal["recommendation_count"] >= 5
    for rec in cal["recommendations"]:
        assert rec["applied"] is False
    assert cal["source_weights"]["debug_gloss"] == 0.0


def test_stability_gate_ready_when_stable():
    g = LiveStabilityGate().evaluate(
        governance_passed=True, birth_certificate_present=True, safety_ok=True,
        source_health_summary=_health(count=4, healthy=4),
        source_diet={"balance": "balanced"},
        load={"load_status": "stable",
              "blocks_ontogenesis_recommendation": False},
        quarantine_rate=0.0).to_dict()
    assert g["live_stability_status"] == "ready_for_metabolism_calibration"
    assert g["starts_any_phase"] is False
    assert g["enables_learning"] is False


def test_stability_gate_blocks_on_governance():
    g = LiveStabilityGate().evaluate(
        governance_passed=False, birth_certificate_present=True, safety_ok=True,
        source_health_summary=_health(), source_diet={"balance": "balanced"},
        load={"load_status": "stable"}, quarantine_rate=0.0).to_dict()
    assert g["live_stability_status"] == "blocked_by_governance"
    assert g["blocked"] is True
    assert g["corrections"]


def test_stability_gate_blocks_on_overload():
    g = LiveStabilityGate().evaluate(
        governance_passed=True, birth_certificate_present=True, safety_ok=True,
        source_health_summary=_health(),
        source_diet={"balance": "balanced"},
        load={"load_status": "severe_overload", "severe_overload": True},
        quarantine_rate=0.0).to_dict()
    assert g["live_stability_status"] == "blocked_by_overload"


def test_stability_gate_blocks_on_quarantine_rate():
    g = LiveStabilityGate().evaluate(
        governance_passed=True, birth_certificate_present=True, safety_ok=True,
        source_health_summary=_health(),
        source_diet={"balance": "balanced"},
        load={"load_status": "stable"}, quarantine_rate=0.9).to_dict()
    assert g["live_stability_status"] == "blocked_by_quarantine_rate"
