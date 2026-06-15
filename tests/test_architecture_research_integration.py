"""Architecture <-> Research: research feeds lifecycle; negatives preserved."""

from __future__ import annotations

from solaris_ai_nn.architecture_evolution import (
    ModuleInventory,
    ModuleLifecycleClass,
    ModuleLifecycleClassifier,
)
from solaris_ai_nn.research_lab import EffectAnalyzer


def test_research_report_feeds_lifecycle_classifier():
    # The research lab's module-effect output drives lifecycle classification.
    ea = EffectAnalyzer()
    full = {"g": {"prediction_accuracy": 0.6}}
    ablation = {"g": {"prediction_accuracy": 0.2}}
    effect = ea.analyze_module("protolanguage", full, ablation)
    a = ModuleLifecycleClassifier().classify(
        "protolanguage", effect_value=effect.value, integration_count=3,
        evidence_refs=effect.evidence_refs)
    assert a.lifecycle_class in (ModuleLifecycleClass.CORE_KEEP,
                                 ModuleLifecycleClass.PROMOTE_TO_CORE,
                                 ModuleLifecycleClass.EXPERIMENTAL_KEEP)


def test_negative_evidence_preserved():
    # A harmful research effect becomes a pruning/quarantine candidate, not
    # silently dropped.
    ea = EffectAnalyzer()
    full = {"g": {"prediction_accuracy": 0.2}}
    ablation = {"g": {"prediction_accuracy": 0.6}}
    effect = ea.analyze_module("latent", full, ablation)
    a = ModuleLifecycleClassifier().classify(
        "latent", effect_value=effect.value, evidence_refs=effect.evidence_refs)
    assert a.lifecycle_class in ModuleLifecycleClass.REMOVAL_LEANING
    assert a.evidence_refs  # the (negative) evidence is retained


def test_classify_inventory_from_research_effects():
    inv = ModuleInventory()
    effects = {"protolanguage": "strong_positive", "latent": "harmful"}
    ev = {"protolanguage": ["r1"], "latent": ["r2"]}
    out = ModuleLifecycleClassifier().classify_inventory(inv, effects, ev)
    assert out["protolanguage"].lifecycle_class == \
        ModuleLifecycleClass.PROMOTE_TO_CORE or \
        out["protolanguage"].lifecycle_class == ModuleLifecycleClass.CORE_KEEP
    # Safety-critical ego is never a pruning candidate even with no effect.
    assert out["ego"].lifecycle_class == \
        ModuleLifecycleClass.SAFETY_CRITICAL_DO_NOT_PRUNE
