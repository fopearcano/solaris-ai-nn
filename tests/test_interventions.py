"""Tests for interventions."""

from __future__ import annotations

import pytest

from solaris_ai_nn.hypothesis.interventions import (
    Intervention,
    InterventionPlan,
    InterventionType,
)


def test_twelve_intervention_types():
    assert len(InterventionType.ALL) == 12


def test_no_os_or_network_intervention_exists():
    text = " ".join(InterventionType.ALL).lower()
    for forbidden in ("network", "os_", "browser", "shell", "http",
                      "real_world"):
        assert forbidden not in text


def test_nursery_intervention_serializes():
    interv = Intervention(
        intervention_type=InterventionType.INTRODUCE_NOVELTY,
        scope="nursery_only", target_ref="novel_region")
    data = interv.to_dict()
    assert data["intervention_type"] == "introduce_novelty"
    # Nursery interventions require ecology safety.
    assert interv.requires_ecology_safety is True


def test_unknown_intervention_rejected():
    with pytest.raises(ValueError):
        Intervention(intervention_type="launch_missile")


def test_plan_is_bounded():
    plan = InterventionPlan(hypothesis_id="h", max_interventions=2)
    assert plan.add(Intervention(
        intervention_type=InterventionType.OBSERVE_ONLY))
    assert plan.add(Intervention(
        intervention_type=InterventionType.RUN_LATENT_REPLAY))
    # Third exceeds the cap.
    assert not plan.add(Intervention(
        intervention_type=InterventionType.SAMPLE_PATTERN))
    assert plan.bounded
    assert len(plan.interventions) == 2


def test_internal_interventions_classified():
    assert InterventionType.RUN_LATENT_REPLAY in InterventionType.INTERNAL
    assert InterventionType.INTRODUCE_ANOMALY in InterventionType.NURSERY
