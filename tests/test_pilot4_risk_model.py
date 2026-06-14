"""RiskModel: dimensions exist; high-risk prohibited; never enables actuation."""

from __future__ import annotations

from solaris_ai_nn.pilot4_planning import (
    ActuationRisk,
    RiskLikelihood,
    RiskModel,
    RiskRecommendation,
    RiskSeverity,
)


def test_risk_dimensions_exist():
    dims = RiskModel.dimensions()
    for d in ("physical_harm", "data_loss", "privacy_exposure",
              "financial_harm", "irreversible_action", "runaway_loop",
              "hallucinated_authority", "emergency_stop_failure",
              "audit_failure", "consent_failure"):
        assert d in dims


def test_high_risk_actuator_prohibited():
    rm = RiskModel()
    assert rm.default_assessment("network_action").recommendation == \
        RiskRecommendation.PROHIBITED
    assert rm.default_assessment("robotic_action").recommendation == \
        RiskRecommendation.PROHIBITED


def test_recommendation_never_enables_actuation():
    # No recommendation value is an "enable real actuation" option.
    assert all("enable" not in r for r in RiskRecommendation.ALL)
    rm = RiskModel()
    for cat in ("network_action", "device_action", "physical_world_action",
                "financial_action"):
        rec = rm.default_assessment(cat).recommendation
        assert rec in RiskRecommendation.ALL
        assert rec != "enable_real_actuation"


def test_severe_internal_dimension_forces_prohibited():
    rm = RiskModel()
    risks = [ActuationRisk(dimension="physical_harm",
                           severity=RiskSeverity.SEVERE,
                           likelihood=RiskLikelihood.POSSIBLE)]
    a = rm.assess("internal_state_action", risks, external=False)
    assert a.recommendation == RiskRecommendation.PROHIBITED


def test_assessment_is_planning_scoped():
    rm = RiskModel()
    d = rm.default_assessment("network_action").to_dict()
    assert d["real_world_actuation_enabled"] is False
    assert "cannot recommend enabling real actuation" in d["disclaimer"]
