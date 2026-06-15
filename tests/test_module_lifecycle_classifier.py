"""ModuleLifecycleClassifier: promote/insufficient/prune; safety protected."""

from __future__ import annotations

from solaris_ai_nn.architecture_evolution import (
    ModuleLifecycleClass,
    ModuleLifecycleClassifier,
)


def test_positive_evidence_promotes():
    a = ModuleLifecycleClassifier().classify(
        "world_model", effect_value="strong_positive", integration_count=4,
        evidence_refs=["r"])
    assert a.lifecycle_class == ModuleLifecycleClass.PROMOTE_TO_CORE


def test_weak_evidence_or_missing_insufficient():
    a = ModuleLifecycleClassifier().classify("x", effect_value=None)
    assert a.lifecycle_class == ModuleLifecycleClass.INSUFFICIENT_EVIDENCE
    b = ModuleLifecycleClassifier().classify("y", effect_value="weak_positive",
                                             evidence_refs=[])
    assert b.lifecycle_class == ModuleLifecycleClass.INSUFFICIENT_EVIDENCE


def test_harmful_evidence_pruning_candidate():
    a = ModuleLifecycleClassifier().classify("latent", effect_value="harmful",
                                             evidence_refs=["r"])
    assert a.lifecycle_class in (
        ModuleLifecycleClass.CANDIDATE_FOR_PRUNING,
        ModuleLifecycleClass.CANDIDATE_FOR_QUARANTINE)


def test_safety_critical_module_not_pruned():
    a = ModuleLifecycleClassifier().classify(
        "ego", safety_critical=True, effect_value="harmful",
        evidence_refs=["r"])
    assert a.lifecycle_class == ModuleLifecycleClass.SAFETY_CRITICAL_DO_NOT_PRUNE
    assert a.lifecycle_class not in ModuleLifecycleClass.REMOVAL_LEANING


def test_recommendation_only_with_limitations():
    a = ModuleLifecycleClassifier().classify("x", effect_value="neutral",
                                             evidence_refs=["r"])
    assert a.recommendation_only is True
    assert a.limitations
