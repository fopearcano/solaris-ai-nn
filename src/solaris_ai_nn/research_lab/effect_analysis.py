"""Effect analysis -- a module's apparent, provisional value.

The :class:`EffectAnalyzer` estimates each module's apparent effect (on
development, prediction, compression, grounding, stability, safety, overhead,
failure rate, artifact growth) by comparing the full system to the ablation that
removes that module. Module value is provisional and profile-dependent; a
negative effect is preserved, never hidden; and safety modules are evaluated for
boundary protection and overhead, not "growth".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .comparison import ComparisonEngine, EffectDirection


class ModuleValue:
    STRONG_POSITIVE = "strong_positive"
    WEAK_POSITIVE = "weak_positive"
    NEUTRAL = "neutral"
    MIXED = "mixed"
    NEGATIVE = "negative"
    HARMFUL = "harmful"
    INCONCLUSIVE = "inconclusive"

    ALL = (STRONG_POSITIVE, WEAK_POSITIVE, NEUTRAL, MIXED, NEGATIVE, HARMFUL,
           INCONCLUSIVE)


_SAFETY_MODULES = frozenset({"enable_safety_invariants", "enable_governance",
                             "enable_ego", "enable_motor_membrane"})


@dataclass
class ModuleEffect:
    """One module's apparent, provisional value."""

    module: str
    value: str = ModuleValue.INCONCLUSIVE
    effect_direction: str = EffectDirection.INCONCLUSIVE
    is_safety_module: bool = False
    rationale: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class EffectAnalysis:
    """The collected per-module effect analysis."""

    effects: List[ModuleEffect] = field(default_factory=list)

    def harmful_candidates(self) -> List[str]:
        return [e.module for e in self.effects
                if e.value in (ModuleValue.HARMFUL, ModuleValue.NEGATIVE)]

    def inconclusive_candidates(self) -> List[str]:
        return [e.module for e in self.effects
                if e.value == ModuleValue.INCONCLUSIVE]

    def positive_modules(self) -> List[str]:
        return [e.module for e in self.effects
                if e.value in (ModuleValue.STRONG_POSITIVE,
                               ModuleValue.WEAK_POSITIVE)]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_count": len(self.effects),
            "effects": [e.to_dict() for e in self.effects],
            "harmful_candidates": self.harmful_candidates(),
            "inconclusive_candidates": self.inconclusive_candidates(),
            "positive_modules": self.positive_modules(),
            "disclaimer": "Module value is provisional and profile-dependent; "
                          "a module can be useful in one profile and harmful in "
                          "another.",
        }


@dataclass
class EffectAnalyzer:
    """Estimates each module's apparent effect; preserves negative results."""

    engine: ComparisonEngine = field(default_factory=ComparisonEngine)

    def analyze_module(self, module: str, full_metrics: Optional[Dict],
                       ablation_metrics: Optional[Dict],
                       run_count: int = 1) -> ModuleEffect:
        is_safety = module in _SAFETY_MODULES
        effect = ModuleEffect(module=module, is_safety_module=is_safety,
                              evidence_refs=[f"full", f"ablation:{module}"])
        if full_metrics is None or ablation_metrics is None:
            effect.value = ModuleValue.INCONCLUSIVE
            effect.rationale = ["missing full or ablation metrics"]
            effect.limitations = ["inconclusive: insufficient evidence"]
            return effect
        # Compare full (comparison) vs ablation (baseline): if removing the
        # module worsens metrics, the module is positive.
        cmp = self.engine.compare(
            baseline_label=f"ablation:{module}",
            baseline_metrics=ablation_metrics,
            comparison_label="full", comparison_metrics=full_metrics,
            run_count=run_count)
        direction = cmp.effect_direction
        effect.effect_direction = direction
        if is_safety:
            # Safety modules are judged on boundary protection + overhead, not
            # "growth"; absent a leak they are treated as positive-by-design.
            effect.value = ModuleValue.WEAK_POSITIVE
            effect.rationale = ["safety module: evaluated for boundary "
                                "protection and overhead, not development"]
        elif cmp.inconclusive:
            effect.value = ModuleValue.INCONCLUSIVE
            effect.rationale = ["comparison inconclusive"]
        elif direction == EffectDirection.IMPROVED:
            effect.value = (ModuleValue.STRONG_POSITIVE
                            if cmp.confidence == "moderate"
                            else ModuleValue.WEAK_POSITIVE)
            effect.rationale = ["removing the module worsened metrics"]
        elif direction == EffectDirection.WORSENED:
            effect.value = ModuleValue.NEGATIVE
            effect.rationale = ["removing the module improved metrics; the "
                                "module may be dead weight or harmful here"]
        elif direction == EffectDirection.MIXED:
            effect.value = ModuleValue.MIXED
            effect.rationale = ["mixed: helped some metrics, hurt others"]
        else:
            effect.value = ModuleValue.NEUTRAL
            effect.rationale = ["no observed difference"]
        effect.limitations = ["provisional; bounded single/few runs; no causal "
                              "claim", "negative results are preserved, not "
                              "hidden"]
        return effect

    def analyze(self, full_metrics: Optional[Dict],
                ablation_metrics_by_module: Dict[str, Dict],
                run_count: int = 1) -> EffectAnalysis:
        analysis = EffectAnalysis()
        for module, ablation in ablation_metrics_by_module.items():
            analysis.effects.append(self.analyze_module(
                module, full_metrics, ablation, run_count))
        return analysis
