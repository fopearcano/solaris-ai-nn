"""Developmental soak plan: stages exist, constraints serialize, bounded."""

from __future__ import annotations

from solaris_ai_nn.developmental_soak import (
    DevelopmentalSoakPlan,
    SoakPlanStageId,
)


def test_all_stages_exist():
    plan = DevelopmentalSoakPlan.default()
    assert plan.ordered_ids() == list(SoakPlanStageId.ORDER)
    for sid in SoakPlanStageId.ORDER:
        assert plan.stage(sid).purpose


def test_constraints_serialize():
    plan = DevelopmentalSoakPlan.default()
    d = plan.to_dict()
    assert d["constraints"]
    for c in d["constraints"]:
        assert "name" in c and "value" in c and "rationale" in c


def test_no_unbounded_stage():
    plan = DevelopmentalSoakPlan.default()
    assert plan.all_bounded()
    for stage in plan.stages.values():
        assert stage.bounded
        assert stage.max_ticks or stage.hard_runtime_cap_s


def test_live_stage_requires_governance():
    plan = DevelopmentalSoakPlan.default()
    for sid in plan.live_stages():
        assert plan.stage(sid).requires_governance


def test_no_stage_starts_feeders():
    plan = DevelopmentalSoakPlan.default()
    for stage in plan.stages.values():
        assert "no feeder" in stage.feeder_policy.lower()


def test_to_dict_disclaims_life():
    note = DevelopmentalSoakPlan.default().to_dict()["note"]
    assert "does not prove life" in note
    assert "consciousness" in note
