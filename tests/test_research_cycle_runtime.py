"""Research cycle runtime: bounded, validated/blocked cycles, status view."""

from __future__ import annotations

from solaris_ai_nn.research_cycle import ResearchCycleRuntime, ResearchCycleStage


def _validated():
    return {
        "cycle_manifest": {"cycle_id": "cycle_3", "parent_cycle_id": "cycle_2",
                           "baseline_id": "b2"},
        "research_baseline": {"baseline_status": "validated",
                              "safety_boundary_status": "pass",
                              "critical_limitation_count": 0},
        "roadmap": {"roadmap_item_count": 3},
        "architecture_evolution": {"proposal_count": 1},
        "experiment_compiler": {"ready_spec_count": 2,
                                "safety_gate_failure_count": 0},
        "implementation_intake": {"merge_recommendation_status": "recommend",
                                  "critical_safety_regression_count": 0},
        "post_merge": {"candidate_baseline_status": "validated",
                       "critical_regression_count": 0},
        "operator_decisions": [
            {"decision_type": "confirm_external_merge", "status": "approved"}],
    }


def _blocked():
    return {
        "cycle_manifest": {"cycle_id": "cycle_4"},
        "implementation_intake": {
            "merge_recommendation_status": "block_merge_due_to_safety",
            "critical_safety_regression_count": 1},
    }


def test_bounded_runs(tmp_path):
    rt = ResearchCycleRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_validated())
    assert rt.run()["refused"] is False


def test_unbounded_refused(tmp_path):
    rt = ResearchCycleRuntime(state_dir=str(tmp_path), max_runtime_s=0)
    rt.load_bundle(_validated())
    assert rt.run()["refused"] is True


def test_validated_cycle_status(tmp_path):
    rt = ResearchCycleRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_validated())
    rt.run()
    st = rt.research_cycle_status()
    assert st["current_cycle_stage"] == \
        ResearchCycleStage.RESEARCH_BASELINE_VALIDATED
    assert st["blocked_state_count"] == 0
    assert st["runs_git"] is False and st["calls_github"] is False
    assert st["approves_itself"] is False


def test_blocked_cycle_status(tmp_path):
    rt = ResearchCycleRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_blocked())
    res = rt.run()
    assert res["blocked"] is True
    st = rt.research_cycle_status()
    assert st["blocked_state_count"] >= 1
    assert st["next_action_count"] >= 1


def test_snapshot_alias(tmp_path):
    rt = ResearchCycleRuntime(state_dir=str(tmp_path))
    rt.load_bundle(_validated())
    rt.run()
    assert rt.snapshot() == rt.research_cycle_status()


def test_archive_only_on_operator_decision(tmp_path):
    bundle = _validated()
    bundle["operator_decisions"].append(
        {"decision_type": "archive_cycle", "status": "approved"})
    rt = ResearchCycleRuntime(state_dir=str(tmp_path), allow_archive=True)
    rt.load_bundle(bundle)
    rt.run()
    assert rt.research_cycle_status()["archived_cycle_count"] == 1
    # Without allow_archive, nothing is archived.
    rt2 = ResearchCycleRuntime(state_dir=str(tmp_path), allow_archive=False)
    rt2.load_bundle(bundle)
    rt2.run()
    assert rt2.research_cycle_status()["archived_cycle_count"] == 0
