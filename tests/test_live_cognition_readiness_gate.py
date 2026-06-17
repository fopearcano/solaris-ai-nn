"""Live cognition readiness gate: ready / blocked by uncertainty/label/contradiction."""

from __future__ import annotations

from solaris_ai_nn.live_cognition import LiveCognitionReadinessGate

_OK = dict(governance_passed=True, birth_certificate_present=True,
           observation_stability_blocked=False, concept_memory_present=True,
           sign_memory_present=True, eligible_sign_count=3,
           promoted_trace_count=2, prediction_contradicted=False,
           contamination_summary={"contaminated_trace_count": 0,
                                  "contamination_types": {}},
           load={})


def _gate():
    return LiveCognitionReadinessGate(max_uncertainty=0.6,
                                      min_prediction_utility=0.5)


def test_trace_ready_case():
    opts = dict(_OK)
    r = _gate().evaluate(mean_uncertainty=0.3, prediction_utility=0.7,
                         allow_anticipation=False,
                         allow_internal_simulation=False, **opts).to_dict()
    assert r["cognition_readiness_status"] == "trace_ready"
    assert r["enables_action"] is False


def test_anticipation_ready_case():
    r = _gate().evaluate(mean_uncertainty=0.3, prediction_utility=0.7,
                         allow_anticipation=True,
                         allow_internal_simulation=False, **_OK).to_dict()
    assert r["cognition_readiness_status"] == "anticipation_ready"


def test_high_uncertainty_block():
    r = _gate().evaluate(mean_uncertainty=0.9, prediction_utility=0.7,
                         allow_anticipation=True,
                         allow_internal_simulation=False, **_OK).to_dict()
    assert r["cognition_readiness_status"] == "blocked_by_high_uncertainty"


def test_label_dependence_block():
    opts = dict(_OK)
    opts["contamination_summary"] = {
        "contaminated_trace_count": 1,
        "contamination_types": {"human_label_dependency": 1}}
    r = _gate().evaluate(mean_uncertainty=0.3, prediction_utility=0.7,
                         allow_anticipation=True,
                         allow_internal_simulation=False, **opts).to_dict()
    assert r["cognition_readiness_status"] == "blocked_by_label_dependence"


def test_prediction_contradiction_block():
    opts = dict(_OK)
    opts["prediction_contradicted"] = True
    r = _gate().evaluate(mean_uncertainty=0.3, prediction_utility=0.2,
                         allow_anticipation=True,
                         allow_internal_simulation=False, **opts).to_dict()
    assert r["cognition_readiness_status"] == "blocked_by_low_prediction_utility"


def test_weak_signs_block():
    opts = dict(_OK)
    opts["eligible_sign_count"] = 1
    r = _gate().evaluate(mean_uncertainty=0.3, prediction_utility=0.7,
                         allow_anticipation=True,
                         allow_internal_simulation=False, **opts).to_dict()
    assert r["cognition_readiness_status"] == "blocked_by_weak_signs"
