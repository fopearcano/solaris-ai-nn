"""Architecture <-> Safety invariants: safety-first roadmap; safety pruning blocked."""

from __future__ import annotations

from solaris_ai_nn.architecture_evolution import (
    PruningProposalBuilder,
    RoadmapCompiler,
    RoadmapHorizon,
    RoadmapItemType,
)


def test_critical_safety_failure_prioritizes_safety_roadmap(tmp_path):
    rc = RoadmapCompiler(base_dir=str(tmp_path))
    items = rc.compile(safety_critical_failing=True, lifecycle_assessments={
        "latent": {"lifecycle_class": "candidate_for_pruning",
                   "evidence_refs": ["r"]}})
    # Safety repair is first and immediate.
    assert items[0].item_type == RoadmapItemType.IMPROVE_SAFETY_INVARIANT
    assert items[0].horizon == RoadmapHorizon.IMMEDIATE


def test_safety_critical_pruning_blocked():
    p = PruningProposalBuilder().build("safety_invariants", safety_critical=True,
                                       evidence_refs=["r"])
    assert p.blocked is True


def test_safety_module_not_pruned_even_with_negative_evidence():
    from solaris_ai_nn.architecture_evolution import ModuleLifecycleClassifier

    a = ModuleLifecycleClassifier().classify(
        "governance", safety_critical=True, effect_value="harmful",
        evidence_refs=["r"])
    assert a.lifecycle_class == "safety_critical_do_not_prune"
