"""Developmental divergence: detected, unknown preserved, conservative."""

from __future__ import annotations

from solaris_ai_nn.developmental_replication import (
    DivergenceDetector,
    DivergenceReason,
)


def _run(run_id, sensorium="non_human", seed=7, overfit=False, contam=0.1):
    status = "fixture_overfit" if overfit else "real_structural_growth"
    return {"run_id": run_id, "sensorium_profile": sensorium, "seed": seed,
            "fixture_live_replay": "fixture",
            "developmental_profile": {"structural_growth_status": status,
                                      "regression_count": 0},
            "world_signature": {"human_label_contamination_score": contam}}


def test_divergence_detected():
    a = _run("a", sensorium="non_human", seed=7)
    b = _run("b", sensorium="human_like", seed=9, contam=0.8)
    out = DivergenceDetector().detect(a, b, similarity=0.2)
    reasons = {d.reason for d in out}
    assert DivergenceReason.DIFFERENT_SENSORIUM_DIET in reasons
    assert DivergenceReason.DIFFERENT_SEED in reasons


def test_no_divergence_when_similar():
    a = _run("a")
    b = _run("b", seed=7)
    out = DivergenceDetector().detect(a, b, similarity=0.9)
    assert out == []


def test_unknown_divergence_preserved():
    # Same metadata but low similarity -> unknown divergence stays visible.
    a = _run("a", sensorium="non_human", seed=7)
    b = _run("b", sensorium="non_human", seed=7)
    out = DivergenceDetector().detect(a, b, similarity=0.2)
    assert any(d.reason == DivergenceReason.UNKNOWN for d in out)


def test_conservative_explanation_not_failure():
    a = _run("a", sensorium="non_human")
    b = _run("b", sensorium="human_like")
    out = DivergenceDetector().detect(a, b, similarity=0.2)
    sensorium_div = next(d for d in out
                         if d.reason == DivergenceReason.DIFFERENT_SENSORIUM_DIET)
    # A plain sensorium difference is not flagged as failure.
    assert sensorium_div.is_failure is False
