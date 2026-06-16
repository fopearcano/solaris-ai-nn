"""Environmental dependency -- what does the development depend on?

:class:`EnvironmentalDependencyAnalyzer` estimates how strongly a run's
developmental structure depends on its environment (fixture patterns, live
rhythms, human text labels, feature-only modalities, source-diet balance, source
silence, noisy sources, operator annotations, feeder schema, random seed,
checkpoint history). Strong dependency is not automatically bad, but fixture and
human-label dependencies are flagged; live dependency must be evidence-backed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class DependencyStrength:
    NONE = "none"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    INCONCLUSIVE = "inconclusive"

    ALL = (NONE, WEAK, MODERATE, STRONG, INCONCLUSIVE)

    @staticmethod
    def from_score(score: float, *, measurable: bool = True) -> str:
        if not measurable:
            return DependencyStrength.INCONCLUSIVE
        if score >= 0.66:
            return DependencyStrength.STRONG
        if score >= 0.33:
            return DependencyStrength.MODERATE
        if score > 0.0:
            return DependencyStrength.WEAK
        return DependencyStrength.NONE


class DependencyFactor:
    FIXTURE_PATTERNS = "fixture_patterns"
    LIVE_SOURCE_RHYTHMS = "live_source_rhythms"
    HUMAN_TEXT_LABELS = "human_text_labels"
    FEATURE_ONLY_MODALITIES = "feature_only_modalities"
    SOURCE_DIET_BALANCE = "source_diet_balance"
    SOURCE_SILENCE = "source_silence"
    NOISY_SOURCES = "noisy_sources"
    OPERATOR_ANNOTATIONS = "operator_annotations"
    FEEDER_SCHEMA = "feeder_schema"
    RANDOM_SEED = "random_seed"
    CHECKPOINT_HISTORY = "checkpoint_history"

    ALL = (FIXTURE_PATTERNS, LIVE_SOURCE_RHYTHMS, HUMAN_TEXT_LABELS,
           FEATURE_ONLY_MODALITIES, SOURCE_DIET_BALANCE, SOURCE_SILENCE,
           NOISY_SOURCES, OPERATOR_ANNOTATIONS, FEEDER_SCHEMA, RANDOM_SEED,
           CHECKPOINT_HISTORY)


@dataclass
class EnvironmentalDependency:
    """A single factor's dependency strength + evidence + flag."""

    factor: str
    strength: str
    score: float = 0.0
    evidence: str = ""
    flagged: bool = False
    evidence_backed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"factor": self.factor, "strength": self.strength,
                "score": round(self.score, 4), "evidence": self.evidence,
                "flagged": self.flagged, "evidence_backed": self.evidence_backed}


@dataclass
class EnvironmentalDependencyAnalyzer:
    """Estimates environmental dependency conservatively, with flags."""

    def analyze(self, run: Dict[str, Any]) -> List[EnvironmentalDependency]:
        sig = run.get("world_signature", {})
        dev = run.get("developmental_profile", {})
        deps: List[EnvironmentalDependency] = []
        fixture = run.get("fixture_live_replay") == "fixture"
        overfit = dev.get("structural_growth_status") == "fixture_overfit"

        # Fixture dependency (flagged when present).
        fx_score = 0.8 if overfit else (0.5 if fixture else 0.1)
        deps.append(EnvironmentalDependency(
            DependencyFactor.FIXTURE_PATTERNS,
            DependencyStrength.from_score(fx_score), fx_score,
            "fixture overfit verdict" if overfit else
            "run is fixture-based" if fixture else "non-fixture run",
            flagged=fixture or overfit))

        # Human-label dependency (flagged when present).
        hl = _f(sig.get("human_label_contamination_score"),
                run.get("human_label_exposure"))
        deps.append(EnvironmentalDependency(
            DependencyFactor.HUMAN_TEXT_LABELS,
            DependencyStrength.from_score(hl, measurable=hl is not None),
            hl or 0.0, f"contamination/exposure {hl}",
            flagged=(hl or 0.0) >= 0.3))

        # Live dependency (must be evidence-backed; inconclusive otherwise).
        live = run.get("fixture_live_replay") == "live"
        live_evidenced = bool(sig.get("modality_native_grounding_score"))
        deps.append(EnvironmentalDependency(
            DependencyFactor.LIVE_SOURCE_RHYTHMS,
            DependencyStrength.from_score(0.5 if live else 0.0,
                                          measurable=live_evidenced or not live),
            0.5 if live else 0.0,
            "live grounding evidence present" if live and live_evidenced else
            "live run without grounding evidence (inconclusive)" if live else
            "not a live run",
            evidence_backed=(not live) or live_evidenced))

        # Source-diet balance + random seed (informational).
        diet = run.get("source_diet", {})
        diet_score = _balance(diet)
        deps.append(EnvironmentalDependency(
            DependencyFactor.SOURCE_DIET_BALANCE,
            DependencyStrength.from_score(diet_score,
                                          measurable=bool(diet)),
            diet_score, f"{len(diet)} source(s) in diet"))
        seeded = run.get("seed") is not None
        deps.append(EnvironmentalDependency(
            DependencyFactor.RANDOM_SEED,
            DependencyStrength.WEAK if seeded else DependencyStrength.INCONCLUSIVE,
            0.2 if seeded else 0.0,
            f"seed={run.get('seed')}" if seeded else "seed unknown",
            evidence_backed=seeded))
        return deps

    def overall_scores(self, deps: List[EnvironmentalDependency],
                       ) -> Dict[str, float]:
        by = {d.factor: d.score for d in deps}
        return {
            "environmental_dependency_score": round(
                sum(d.score for d in deps) / len(deps), 4) if deps else 0.0,
            "fixture_overfit_score": round(
                by.get(DependencyFactor.FIXTURE_PATTERNS, 0.0), 4),
            "human_label_dependency_score": round(
                by.get(DependencyFactor.HUMAN_TEXT_LABELS, 0.0), 4),
        }


def _f(*vals):
    for v in vals:
        if isinstance(v, (int, float)):
            return float(v)
    return None


def _balance(diet: Dict[str, Any]) -> float:
    if not diet:
        return 0.0
    # A more concentrated diet (one source dominating) is a stronger dependency.
    vals = [float(v) for v in diet.values() if isinstance(v, (int, float))]
    if not vals or sum(vals) == 0:
        return 0.5
    return round(max(vals) / sum(vals), 4)
