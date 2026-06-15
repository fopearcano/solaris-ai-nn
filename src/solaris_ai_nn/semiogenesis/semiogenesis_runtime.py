"""Semiogenesis runtime -- birth internal signs from sensorium-native concepts.

:class:`SemiogenesisRuntime` reads the perceptual-ontogenesis proto-concepts (and
their families/relations, plus optional metabolism state), conservatively births
:class:`InternalSign`s, stabilizes/decays them by utility, clusters them into sign
families, derives a private syntax, composes internal utterances, evaluates
utility, detects drift and contamination, and summarizes. Every output is
*internal*: no LLM is used, no human language is the default, no hardware/feeder/
source/action is touched, and the loop is bounded against sign explosion.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .contamination import SignContaminationAnalyzer
from .drift import SignDriftDetector
from .private_syntax import SyntaxPatternBuilder
from .reports import SemiogenesisReportBuilder
from .safety import SemiogenesisSafetyValidator
from .sign_birth import SignBirthEngine
from .sign_family import SignFamilyBuilder
from .sign_memory import SignMemoryStore
from .sign_utility import SignUtilityEvaluator
from .signs import InternalSign, SignKind, SignStatus
from .translation_gloss import GlossBuilder
from .utterance import UtteranceBuilder


class SemiogenesisMilestone:
    FIRST_SIGN = "first_internal_sign"
    FIRST_STABLE_SIGN = "first_stable_sign"
    FIRST_SIGN_FAMILY = "first_sign_family"
    FIRST_SYNTAX_PATTERN = "first_private_syntax_pattern"
    FIRST_UTTERANCE = "first_internal_utterance"
    FIRST_DRIFT = "first_sign_drift"
    FIRST_CONTAMINATION = "first_sign_contamination"
    FIRST_CROSS_MODAL_SIGN = "first_cross_modal_sign"
    FIRST_ABSENCE_SIGN = "first_absence_sign"

    ALL = (FIRST_SIGN, FIRST_STABLE_SIGN, FIRST_SIGN_FAMILY,
           FIRST_SYNTAX_PATTERN, FIRST_UTTERANCE, FIRST_DRIFT,
           FIRST_CONTAMINATION, FIRST_CROSS_MODAL_SIGN, FIRST_ABSENCE_SIGN)


@dataclass
class SemiogenesisRuntime:
    """The bounded sign-formation loop (internal-only, no LLM, no actuation)."""

    state_dir: str = ".solaris_ai_nn_semiogenesis"
    ontogenesis: Any = None
    world_model: Any = None
    proto_language: Any = None
    metabolism: Any = None
    max_signs_per_tick: int = 50
    max_utterances_per_tick: int = 50
    max_signs_total: int = 2000
    max_runtime_s: float = 30.0
    max_ticks: int = 120
    fixture_mode: bool = True
    live_read_only_mode: bool = False
    dry_run: bool = False

    birth: SignBirthEngine = field(default=None, init=False)
    family_builder: SignFamilyBuilder = field(
        default_factory=SignFamilyBuilder)
    syntax_builder: SyntaxPatternBuilder = field(
        default_factory=SyntaxPatternBuilder)
    utterance_builder: UtteranceBuilder = field(
        default_factory=UtteranceBuilder)
    utility: SignUtilityEvaluator = field(default_factory=SignUtilityEvaluator)
    drift_detector: SignDriftDetector = field(
        default_factory=SignDriftDetector)
    contamination: SignContaminationAnalyzer = field(
        default_factory=SignContaminationAnalyzer)
    gloss_builder: GlossBuilder = field(default_factory=GlossBuilder)
    memory: SignMemoryStore = field(default=None, init=False)
    safety: SemiogenesisSafetyValidator = field(
        default_factory=SemiogenesisSafetyValidator)

    signs: Dict[str, InternalSign] = field(default_factory=dict, init=False)
    _sign_by_signature: Dict[str, str] = field(default_factory=dict, init=False)
    patterns: List[Any] = field(default_factory=list, init=False)
    utterances: List[Any] = field(default_factory=list, init=False)
    drift_results: List[Dict[str, Any]] = field(default_factory=list,
                                                init=False)
    milestones: List[str] = field(default_factory=list, init=False)
    explosion_warnings: int = field(default=0, init=False)
    ticks_run: int = field(default=0, init=False)
    _last: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.birth = SignBirthEngine(live_mode=not self.fixture_mode)
        self.memory = SignMemoryStore(state_dir=self.state_dir,
                                      persist=not self.dry_run)
        bounded = self.safety.validate_bounded(self.max_ticks,
                                               self.max_runtime_s)
        self._refused = not bounded.safe

    def _milestone(self, name: str) -> None:
        if name not in self.milestones:
            self.milestones.append(name)

    def _concepts(self) -> List[Any]:
        ont = self.ontogenesis
        if ont is None:
            return []
        if hasattr(ont, "concepts"):
            return list(ont.concepts.values())
        if isinstance(ont, (list, tuple)):
            return list(ont)
        return []

    def _concept_relations(self) -> List[Dict[str, Any]]:
        ont = self.ontogenesis
        if ont is not None and hasattr(ont, "world_model_edges"):
            return ont.world_model_edges()
        return []

    def _metabolism_status(self) -> Dict[str, Any]:
        m = self.metabolism
        if m is None:
            return {}
        if isinstance(m, dict):
            return m
        if hasattr(m, "metabolism_status"):
            return m.metabolism_status()
        if hasattr(m, "snapshot"):
            return m.snapshot()
        return {}

    def update(self, *, tick: int = 0) -> Dict[str, Any]:
        """Run one bounded semiogenesis tick over the current concepts."""
        if self._refused:
            return {"refused": True, "reason": "unbounded sign creation"}
        self.ticks_run += 1

        status = self._metabolism_status()
        overloaded = bool(status.get("overload_state"))
        priority_boost = float(status.get("novelty_appetite_pressure", 0.0)
                               or 0.0)

        # 1. Birth signs from concepts (conservative; metabolism modulates).
        concepts = self._concepts()
        candidates = self.birth.propose(concepts, priority_boost=priority_boost)
        born = 0
        for cand in candidates:
            if overloaded and born >= max(1, self.max_signs_per_tick // 4):
                break  # sign overload throttles birth (no deletion)
            if born >= self.max_signs_per_tick \
                    or len(self.signs) >= self.max_signs_total:
                self.explosion_warnings += 1
                break
            self._absorb(cand)
            born += 1

        sign_list = list(self.signs.values())

        # 2. Utility, contamination, drift, gloss per sign.
        for sign in sign_list:
            self.utility.evaluate(sign)
            crep = self.contamination.analyze(sign)
            if not crep.feature_grounded:
                self._milestone(SemiogenesisMilestone.FIRST_CONTAMINATION)
            drift = self.drift_detector.observe(sign)
            if drift.drifted:
                self._milestone(SemiogenesisMilestone.FIRST_DRIFT)
                self.drift_results.append(drift.to_dict())
            self.gloss_builder.build(sign)
            if sign.is_cross_modal:
                self._milestone(SemiogenesisMilestone.FIRST_CROSS_MODAL_SIGN)
            if sign.is_absence:
                self._milestone(SemiogenesisMilestone.FIRST_ABSENCE_SIGN)
            if sign.status == SignStatus.STABLE:
                self._milestone(SemiogenesisMilestone.FIRST_STABLE_SIGN)
            self.memory.record_sign(sign.to_dict())

        # 3. Families.
        families = self.family_builder.build(sign_list)
        if families:
            self._milestone(SemiogenesisMilestone.FIRST_SIGN_FAMILY)
        # 4. Private syntax.
        self.patterns = self.syntax_builder.build(
            sign_list, concept_relations=self._concept_relations())
        for pat in self.patterns:
            self.memory.record_relation(pat.to_dict())
        if self.patterns:
            self._milestone(SemiogenesisMilestone.FIRST_SYNTAX_PATTERN)
        # 5. Internal utterances.
        self.utterances = self.utterance_builder.build(
            self.patterns, max_utterances=self.max_utterances_per_tick)
        for utt in self.utterances:
            self.memory.record_utterance(utt.to_dict())
        if self.utterances:
            self._milestone(SemiogenesisMilestone.FIRST_UTTERANCE)
        for sign in sign_list:
            sign.relation_utility = min(1.0, 0.2 * sum(
                1 for p in self.patterns if sign.sign_id in p.signs))

        self.memory.write_index()
        self._last = {
            "tick": tick,
            "sign_count": len(self.signs),
            "born_this_tick": born,
            "family_count": len(families),
            "pattern_count": len(self.patterns),
            "utterance_count": len(self.utterances),
        }
        return self._last

    def _absorb(self, cand: Any) -> None:
        signature = cand.sign.metadata.get("concept_signature", "")
        existing_id = self._sign_by_signature.get(signature)
        if existing_id is not None and existing_id in self.signs:
            sign = self.signs[existing_id]
            sign.recurrence_count += 1
            sign.last_seen = cand.sign.last_seen
            sign.grounding_score = min(1.0, sign.grounding_score + 0.05)
            return
        self.signs[cand.sign.sign_id] = cand.sign
        if signature:
            self._sign_by_signature[signature] = cand.sign.sign_id
        self._milestone(SemiogenesisMilestone.FIRST_SIGN)

    def run_bounded(self, max_ticks: Optional[int] = None) -> Dict[str, Any]:
        if self._refused:
            return {"refused": True}
        started = time.time()
        n = min(self.max_ticks, max_ticks or self.max_ticks)
        for tick in range(n):
            if time.time() - started > self.max_runtime_s:
                break
            self.update(tick=tick)
        return {"refused": False, "ticks_run": self.ticks_run,
                "last": self._last}

    # -- views / integration --------------------------------------------------

    def stable_signs(self) -> List[InternalSign]:
        return [s for s in self.signs.values()
                if s.status == SignStatus.STABLE]

    def ambiguous_signs(self) -> List[InternalSign]:
        return [s for s in self.signs.values() if s.is_ambiguous]

    def decaying_signs(self) -> List[InternalSign]:
        return [s for s in self.signs.values()
                if s.status in (SignStatus.DECAYING, SignStatus.REJECTED)]

    def contaminated_signs(self) -> List[InternalSign]:
        return [s for s in self.signs.values() if s.is_contaminated]

    def latent_replay_recommendations(self) -> List[str]:
        """A bounded list of signs worth consolidating (recommendation only)."""
        recs: List[str] = []
        for s in self.signs.values():
            if s.status in (SignStatus.STABLE, SignStatus.AMBIGUOUS,
                            SignStatus.DECAYING):
                recs.append(f"consolidate:{s.sign_id}:{s.status}")
            if len(recs) >= 6:
                break
        return recs

    def metabolism_signals(self) -> Dict[str, Any]:
        """Sign-pressure signals the perceptual metabolism can track."""
        signs = list(self.signs.values())
        n = max(1, len(signs))
        weak = sum(1 for s in signs if s.status in (SignStatus.AMBIGUOUS,
                                                    SignStatus.EMERGING))
        return {
            "sign_overload": len(signs) >= self.max_signs_total
            or self.explosion_warnings > 0,
            "sign_starvation": len(signs) == 0,
            "sign_ambiguity_pressure": round(len(self.ambiguous_signs()) / n, 4),
            "utterance_explosion": len(self.utterances)
            >= self.max_utterances_per_tick,
            "consolidation_pressure_from_weak_signs": round(weak / n, 4),
        }

    def world_model_nodes(self) -> List[Dict[str, Any]]:
        """Signs as world-model reference nodes (distinct from concepts)."""
        from ..world_model.nodes import NodeType, node_id_for

        nodes: List[Dict[str, Any]] = []
        for s in self.signs.values():
            nodes.append({
                "node_id": node_id_for(NodeType.PROTO_SYMBOL, s.sign_code),
                "type": NodeType.PROTO_SYMBOL,
                "label": s.sign_code,
                "confidence": s.utility(),
                "attributes": {
                    "sign_id": s.sign_id, "sign_kind": s.kind,
                    "status": s.status,
                    "proto_concept_refs": list(s.proto_concept_refs),
                    "is_cross_modal": s.is_cross_modal,
                    "human_label_contaminated": s.is_contaminated,
                    "role": "sign",
                    "note": "internal sign reference node, not a human word or "
                            "object category"},
            })
        return nodes

    def hypothesis_seeds(self) -> List[Any]:
        """Seed hypotheses that use signs as compact references."""
        from ..hypothesis.sources import HypothesisSeed

        seeds: List[HypothesisSeed] = []
        for pat in self.patterns:
            if len(pat.signs) >= 2:
                seeds.append(HypothesisSeed(
                    source="semiogenesis", hypothesis_type="relation",
                    target_ref=pat.pattern_id,
                    observation=f"{pat.signs[0]} {pat.relation} {pat.signs[1]}",
                    intensity=pat.strength,
                    evidence_refs=list(pat.evidence_refs)))
        for s in self.contaminated_signs():
            seeds.append(HypothesisSeed(
                source="semiogenesis", hypothesis_type="anomaly",
                target_ref=s.sign_id,
                observation=f"{s.sign_code} is human-label contaminated; "
                            "evidence strength reduced",
                intensity=0.3))
        return seeds

    def logos_tensions(self) -> List[Any]:
        """Semiogenesis tensions expressed as LOGOS tensions (valid types only)."""
        from ..logos_complexity.tension import (
            LogosTension,
            TensionPolarity,
            TensionType,
        )

        tensions: List[LogosTension] = []
        if self.contaminated_signs():
            tensions.append(LogosTension(
                tension_type=TensionType.SYMBOL_AMBIGUITY,
                polarity_a="modality_native_sign", polarity_b="human_word",
                source_modules=["semiogenesis"],
                metadata={"semiogenesis_tension":
                          "modality_native_sign_vs_human_word"}))
        if self.ambiguous_signs():
            tensions.append(LogosTension(
                tension_type=TensionType.SYMBOL_AMBIGUITY,
                polarity_a=TensionPolarity.STABLE,
                polarity_b=TensionPolarity.AMBIGUOUS,
                source_modules=["semiogenesis"],
                metadata={"semiogenesis_tension": "stable_sign_vs_drift"}))
        if any(d.get("recommend_logos_tension") for d in self.drift_results):
            tensions.append(LogosTension(
                tension_type=TensionType.DRIFT_IDENTITY,
                polarity_a="stable_sign", polarity_b="drift",
                source_modules=["semiogenesis"],
                metadata={"semiogenesis_tension": "stable_sign_vs_drift"}))
        if self.signs:
            tensions.append(LogosTension(
                tension_type=TensionType.SYMBOL_AMBIGUITY,
                polarity_a="sign", polarity_b="gloss",
                source_modules=["semiogenesis"],
                metadata={"semiogenesis_tension": "sign_vs_gloss"}))
        return tensions

    def gloss_dependence_score(self) -> float:
        return self.gloss_builder.dependence_score(self.signs.values())

    def semiogenesis_status(self) -> Dict[str, Any]:
        signs = list(self.signs.values())
        n = max(1, len(signs))
        modality_native = sum(1 for s in signs
                              if s.kind == SignKind.MODALITY_NATIVE)
        cross_modal = sum(1 for s in signs if s.is_cross_modal)
        absence = sum(1 for s in signs if s.is_absence)
        contaminated = sum(1 for s in signs if s.is_contaminated)
        contamination = (sum(1.0 for s in signs if s.is_contaminated) / n)
        means = self.utility.means(signs)
        return {
            "semiogenesis_enabled": True,
            "internal_sign_count": len(signs),
            "stable_sign_count": len(self.stable_signs()),
            "ambiguous_sign_count": len(self.ambiguous_signs()),
            "decaying_sign_count": len(self.decaying_signs()),
            "rejected_sign_count": sum(
                1 for s in signs if s.status == SignStatus.REJECTED),
            "sign_family_count": len(self.family_builder.families),
            "dominant_sign_family": self.family_builder.dominant_family(),
            "private_syntax_pattern_count": len(self.patterns),
            "internal_utterance_count": len(self.utterances),
            "modality_native_sign_ratio": round(modality_native / n, 4),
            "cross_modal_sign_ratio": round(cross_modal / n, 4),
            "absence_sign_ratio": round(absence / n, 4),
            "contaminated_sign_count": contaminated,
            "contaminated_sign_ratio": round(contaminated / n, 4),
            "sign_compression_utility_mean": means["compression"],
            "sign_prediction_utility_mean": means["prediction"],
            "sign_attention_utility_mean": means["attention"],
            "sign_drift_count": len(self.drift_results),
            "gloss_dependence_score": self.gloss_dependence_score(),
            "sign_explosion_warning_count": self.explosion_warnings,
            "latest_semiogenesis_report_path": self._report_path(),
        }

    def _report_path(self) -> Optional[str]:
        import os

        path = os.path.join(self.state_dir, "SEMIOGENESIS_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.semiogenesis_status()

    def write_artifacts(self) -> Dict[str, Any]:
        return SemiogenesisReportBuilder(self).write()
