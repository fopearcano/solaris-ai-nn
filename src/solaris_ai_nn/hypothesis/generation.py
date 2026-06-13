"""Hypothesis generation -- seeds become grounded, testable candidates.

The :class:`HypothesisGenerator` converts :class:`HypothesisSeed`s into
:class:`Hypothesis` objects: it writes a deterministic, non-anthropomorphic
statement, the expected and alternative observations, picks the bounded test
scope, assigns an initial (low) confidence and high uncertainty, rejects
untestable/unsafe candidates, and avoids duplicates. No LLM is involved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .hypotheses import (
    Hypothesis,
    HypothesisScope,
    HypothesisType,
)
from .safety import HypothesisSafetyValidator
from .sources import HypothesisSeed

# Per type: (scope, risk, statement template, expected, alternative).
_TEMPLATES = {
    HypothesisType.PREDICTION: (
        HypothesisScope.NURSERY_ONLY, "low",
        "prediction candidate: pattern {t} may predict its consequence",
        "the consequence follows the pattern above chance",
        "the consequence does not follow the pattern"),
    HypothesisType.CAUSAL_CANDIDATE: (
        HypothesisScope.INTERNAL_ONLY, "low",
        "association candidate: {t} may be a causal candidate, not just "
        "co-occurrence",
        "the relation persists under counterfactual replay",
        "the relation vanishes when the cause is withheld (offline)"),
    HypothesisType.DELAYED_CONSEQUENCE: (
        HypothesisScope.NURSERY_ONLY, "low",
        "delayed-consequence candidate: group {t} may belong to an earlier "
        "signal",
        "a consequence recurs a stable number of steps after the cause",
        "no stable delay is observed"),
    HypothesisType.PROTO_SYMBOL_GROUNDING: (
        HypothesisScope.LATENT_REPLAY_ONLY, "low",
        "grounding candidate: proto-symbol {t} may refer to two different "
        "patterns",
        "ambiguity falls when grounding contexts are separated",
        "ambiguity stays the same or rises"),
    HypothesisType.PROTO_SYNTAX: (
        HypothesisScope.INTERNAL_ONLY, "low",
        "proto-syntax candidate: regularity {t} may hold on held-out traces",
        "the regularity validates on held-out sequences",
        "the regularity fails to validate"),
    HypothesisType.HABIT_CONTEXT: (
        HypothesisScope.INTERNAL_ONLY, "low",
        "habit-context candidate: habit {t} may be useful only in one "
        "context",
        "the habit's value concentrates in one context",
        "the habit's value is context-independent"),
    HypothesisType.BOUNDARY: (
        HypothesisScope.INTERNAL_ONLY, "low",
        "boundary candidate: boundary events near {t} may predict executive "
        "inhibition",
        "inhibition follows boundary events above chance",
        "no association between boundary events and inhibition"),
    HypothesisType.MYSTERIUM_REDUCTION: (
        HypothesisScope.LATENT_REPLAY_ONLY, "low",
        "mysterium-reduction candidate: sampling {t} may reduce unknown "
        "pressure",
        "unknown pressure falls after the sampling",
        "unknown pressure does not fall"),
    HypothesisType.STAGNATION_RECOVERY: (
        HypothesisScope.NURSERY_ONLY, "medium",
        "stagnation-recovery candidate: novelty sampling may raise "
        "structural change",
        "structural change rises after novelty sampling",
        "structural change stays flat"),
    HypothesisType.HOMEOSTATIC_REGULATION: (
        HypothesisScope.INTERNAL_ONLY, "low",
        "homeostatic candidate: need conflict {t} may resolve toward one "
        "stable channel",
        "one drive channel stabilizes the conflict",
        "the conflict persists across updates"),
    HypothesisType.EXECUTIVE_ARBITRATION: (
        HypothesisScope.INTERNAL_ONLY, "low",
        "arbitration candidate: candidate {t} may be inhibited only in one "
        "context",
        "inhibition concentrates in one context",
        "inhibition is context-independent"),
    HypothesisType.WORLD_MODEL_EDGE: (
        HypothesisScope.INTERNAL_ONLY, "low",
        "edge candidate: world-model edge {t} may be weak or false",
        "the edge gains support under more observation/replay",
        "the edge stays weak or is contradicted"),
    HypothesisType.ANOMALY_PATTERN: (
        HypothesisScope.NURSERY_ONLY, "medium",
        "anomaly candidate: anomaly {t} may be recurring, not noise",
        "the anomaly recurs with a detectable regularity",
        "the anomaly does not recur"),
}


@dataclass
class HypothesisGenerator:
    """Converts seeds to hypotheses; deterministic, no LLM, dedup-aware."""

    safety: HypothesisSafetyValidator = field(
        default_factory=HypothesisSafetyValidator)
    generated_total: int = field(default=0, init=False)
    rejected_total: int = field(default=0, init=False)
    _seen_keys: set = field(default_factory=set, init=False)

    def generate(self, seeds: List[HypothesisSeed],
                 context: Optional[Dict[str, Any]] = None,
                 ) -> List[Hypothesis]:
        out: List[Hypothesis] = []
        for seed in seeds:
            hypothesis = self._from_seed(seed)
            if hypothesis is None:
                continue
            if hypothesis.dedup_key in self._seen_keys:
                continue
            report = self.safety.validate_hypothesis(hypothesis)
            if not report.safe:
                hypothesis.testable = False
                hypothesis.set_status("unsafe_to_test")
                hypothesis.metadata["unsafe_reasons"] = report.violations
                self.rejected_total += 1
            self._seen_keys.add(hypothesis.dedup_key)
            self.generated_total += 1
            out.append(hypothesis)
        return out

    def _from_seed(self, seed: HypothesisSeed) -> Optional[Hypothesis]:
        template = _TEMPLATES.get(seed.hypothesis_type)
        if template is None:
            return None
        scope, risk, statement_t, expected, alternative = template
        target = seed.target_ref or "target"
        statement = statement_t.format(t=target)
        # Counterfactual/offline seeds can only be tested offline.
        if seed.offline:
            scope = HypothesisScope.LATENT_REPLAY_ONLY
        confidence = round(min(0.45, 0.2 + 0.25 * seed.intensity), 4)
        hypothesis = Hypothesis(
            type=seed.hypothesis_type, statement=statement,
            expected_observation=expected,
            alternative_observation=alternative,
            source_refs=list(seed.evidence_refs),
            required_scope=scope, confidence=confidence,
            uncertainty=round(1.0 - confidence, 4), risk_level=risk,
            target_ref=seed.target_ref,
            metadata={"source": seed.source, "offline_seed": seed.offline,
                      "seed_observation": seed.observation})
        return hypothesis

    def snapshot(self) -> Dict[str, Any]:
        return {
            "generated_total": self.generated_total,
            "rejected_total": self.rejected_total,
            "distinct_keys": len(self._seen_keys),
        }
