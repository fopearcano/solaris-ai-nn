"""Synthesis -- bounded, proposed resolutions of a tension (never assumed).

A :class:`SynthesisCandidate` proposes one way to resolve (or preserve) a
tension: merge/split a symbol, mark a world edge ambiguous, weaken/strengthen
an edge, create a hypothesis, request active sampling / latent replay /
consolidation / auto-regeneration, stabilize executive policy, preserve the
tension, prune a low-value relation, or do nothing. Synthesis is *proposed*,
not automatically true; some tensions must stay unresolved; and safety,
governance, and the executive remain authoritative. No source-code mutation.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .safety import LogosComplexitySafetyValidator
from .tension import LogosTension, TensionStatus, TensionType


class SynthesisType:
    MERGE_SYMBOLS = "merge_symbols"
    SPLIT_SYMBOL = "split_symbol"
    MARK_AMBIGUOUS = "mark_ambiguous"
    CREATE_HYPOTHESIS = "create_hypothesis"
    WEAKEN_WORLD_EDGE = "weaken_world_edge"
    STRENGTHEN_WORLD_EDGE = "strengthen_world_edge"
    CREATE_WORLD_MODEL_RELATION = "create_world_model_relation"
    REQUEST_ACTIVE_SAMPLING = "request_active_sampling"
    REQUEST_LATENT_REPLAY = "request_latent_replay"
    REQUEST_MEMORY_CONSOLIDATION = "request_memory_consolidation"
    REQUEST_AUTO_REGENERATION = "request_auto_regeneration"
    STABILIZE_EXECUTIVE_POLICY = "stabilize_executive_policy"
    PRESERVE_TENSION = "preserve_tension"
    PRUNE_LOW_VALUE_RELATION = "prune_low_value_relation"
    CREATE_PROTO_UTTERANCE = "create_proto_utterance"
    NO_SYNTHESIS = "no_synthesis"

    ALL = (MERGE_SYMBOLS, SPLIT_SYMBOL, MARK_AMBIGUOUS, CREATE_HYPOTHESIS,
           WEAKEN_WORLD_EDGE, STRENGTHEN_WORLD_EDGE,
           CREATE_WORLD_MODEL_RELATION, REQUEST_ACTIVE_SAMPLING,
           REQUEST_LATENT_REPLAY, REQUEST_MEMORY_CONSOLIDATION,
           REQUEST_AUTO_REGENERATION, STABILIZE_EXECUTIVE_POLICY,
           PRESERVE_TENSION, PRUNE_LOW_VALUE_RELATION, CREATE_PROTO_UTTERANCE,
           NO_SYNTHESIS)
    # Synthesis types that only emit a request to a safe subsystem.
    REQUEST_ONLY = frozenset({REQUEST_ACTIVE_SAMPLING, REQUEST_LATENT_REPLAY,
                              REQUEST_MEMORY_CONSOLIDATION,
                              REQUEST_AUTO_REGENERATION,
                              STABILIZE_EXECUTIVE_POLICY, PRESERVE_TENSION,
                              CREATE_HYPOTHESIS, NO_SYNTHESIS})


# Resulting tension status for each synthesis type when applied.
_STATUS_FOR = {
    SynthesisType.MERGE_SYMBOLS: TensionStatus.MERGED,
    SynthesisType.SPLIT_SYMBOL: TensionStatus.SPLIT,
    SynthesisType.MARK_AMBIGUOUS: TensionStatus.PRESERVED,
    SynthesisType.CREATE_HYPOTHESIS: TensionStatus.HYPOTHESIS_CREATED,
    SynthesisType.WEAKEN_WORLD_EDGE: TensionStatus.SYNTHESIZED,
    SynthesisType.STRENGTHEN_WORLD_EDGE: TensionStatus.SYNTHESIZED,
    SynthesisType.CREATE_WORLD_MODEL_RELATION: TensionStatus.SYNTHESIZED,
    SynthesisType.REQUEST_ACTIVE_SAMPLING: TensionStatus.SENT_TO_SAMPLING,
    SynthesisType.REQUEST_LATENT_REPLAY: TensionStatus.SENT_TO_REPLAY,
    SynthesisType.REQUEST_MEMORY_CONSOLIDATION: TensionStatus.SENT_TO_REPAIR,
    SynthesisType.REQUEST_AUTO_REGENERATION: TensionStatus.SENT_TO_REPAIR,
    SynthesisType.STABILIZE_EXECUTIVE_POLICY: TensionStatus.STABILIZED,
    SynthesisType.PRESERVE_TENSION: TensionStatus.PRESERVED,
    SynthesisType.PRUNE_LOW_VALUE_RELATION: TensionStatus.PRUNED,
    SynthesisType.CREATE_PROTO_UTTERANCE: TensionStatus.SYNTHESIZED,
    SynthesisType.NO_SYNTHESIS: TensionStatus.UNRESOLVED,
}

# Tension type -> ordered list of candidate synthesis types to propose.
_PROPOSALS = {
    TensionType.WORLD_MODEL_CONTRADICTION: [
        SynthesisType.MARK_AMBIGUOUS, SynthesisType.CREATE_HYPOTHESIS,
        SynthesisType.PRESERVE_TENSION],
    TensionType.SYMBOL_AMBIGUITY: [
        SynthesisType.REQUEST_ACTIVE_SAMPLING, SynthesisType.SPLIT_SYMBOL,
        SynthesisType.MARK_AMBIGUOUS],
    TensionType.PREDICTION_FAILURE: [
        SynthesisType.CREATE_HYPOTHESIS, SynthesisType.REQUEST_LATENT_REPLAY],
    TensionType.MYSTERIUM_SYNTHESIS: [
        SynthesisType.REQUEST_LATENT_REPLAY, SynthesisType.PRESERVE_TENSION],
    TensionType.MEMORY_COMPRESSION: [
        SynthesisType.REQUEST_MEMORY_CONSOLIDATION,
        SynthesisType.REQUEST_AUTO_REGENERATION],
    TensionType.GROWTH_STAGNATION: [
        SynthesisType.REQUEST_ACTIVE_SAMPLING, SynthesisType.PRESERVE_TENSION],
    TensionType.DRIFT_IDENTITY: [
        SynthesisType.REQUEST_AUTO_REGENERATION,
        SynthesisType.STABILIZE_EXECUTIVE_POLICY],
    TensionType.REGULARITY_ANOMALY: [SynthesisType.CREATE_HYPOTHESIS],
    TensionType.HYPOTHESIS_CONFLICT: [
        SynthesisType.CREATE_HYPOTHESIS, SynthesisType.PRESERVE_TENSION],
    TensionType.COMPLEXITY_OVERLOAD: [
        SynthesisType.REQUEST_AUTO_REGENERATION,
        SynthesisType.STABILIZE_EXECUTIVE_POLICY,
        SynthesisType.PRUNE_LOW_VALUE_RELATION],
    TensionType.INERT_SIMPLICITY: [SynthesisType.REQUEST_ACTIVE_SAMPLING],
    TensionType.EXPLORE_STABILIZE: [SynthesisType.PRESERVE_TENSION],
    TensionType.ACTION_INHIBITION: [
        SynthesisType.STABILIZE_EXECUTIVE_POLICY],
    TensionType.NEED_SAFETY: [SynthesisType.PRESERVE_TENSION],
    TensionType.SELF_OTHER_BOUNDARY: [SynthesisType.PRESERVE_TENSION],
    TensionType.OFFLINE_REAL_BOUNDARY: [SynthesisType.PRESERVE_TENSION],
    TensionType.KNOWN_UNKNOWN: [SynthesisType.PRESERVE_TENSION],
    TensionType.HABIT_NOVELTY: [SynthesisType.PRESERVE_TENSION],
}


@dataclass
class SynthesisCandidate:
    """One proposed (or preserving) resolution of a tension."""

    tension_id: str
    synthesis_type: str
    proposed_action: str = ""
    expected_benefit: str = ""
    expected_risk: float = 0.05
    reversible: bool = True
    requires_governance: bool = False
    evidence_refs: List[str] = field(default_factory=list)
    confidence: float = 0.5
    candidate_id: str = field(default_factory=lambda: f"SYN_{uuid.uuid4().hex[:8]}")
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.synthesis_type not in SynthesisType.ALL:
            raise ValueError(f"unknown synthesis type {self.synthesis_type!r}")
        self.expected_risk = max(0.0, min(1.0, float(self.expected_risk)))

    @property
    def is_request_only(self) -> bool:
        return self.synthesis_type in SynthesisType.REQUEST_ONLY

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


class SynthesisResultClass:
    APPLIED = "applied"
    PRESERVED = "preserved"
    REFUSED = "refused"
    INCONCLUSIVE = "inconclusive"

    ALL = (APPLIED, PRESERVED, REFUSED, INCONCLUSIVE)


@dataclass
class SynthesisResult:
    """The outcome of (attempting) a synthesis candidate."""

    candidate_id: str
    tension_id: str
    synthesis_type: str
    applied: bool = False
    refused: bool = False
    refused_reason: str = ""
    result_class: str = SynthesisResultClass.INCONCLUSIVE
    new_tension_status: str = TensionStatus.UNRESOLVED
    detail: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


# Synthesis type -> (executive label, candidate type, executable scope).
_CANDIDATE_MAP = {
    SynthesisType.REQUEST_LATENT_REPLAY: (
        "run_replay", "latent_action", "internal_only"),
    SynthesisType.REQUEST_MEMORY_CONSOLIDATION: (
        "consolidate_memory", "latent_action", "internal_only"),
    SynthesisType.REQUEST_ACTIVE_SAMPLING: (
        "explore_safely", "simulated_embodied_action", "simulation_only"),
    SynthesisType.STABILIZE_EXECUTIVE_POLICY: (
        "stabilize", "internal_maintenance_action", "internal_only"),
    SynthesisType.REQUEST_AUTO_REGENERATION: (
        "stabilize", "internal_maintenance_action", "internal_only"),
    SynthesisType.PRESERVE_TENSION: (
        "no_action", "no_action", "none"),
    SynthesisType.NO_SYNTHESIS: ("no_action", "no_action", "none"),
}


def synthesis_to_candidate(candidate: "SynthesisCandidate") -> Any:
    """One SynthesisCandidate -> one executive ActionCandidate (a suggestion).

    Synthesis enters executive arbitration like any other suggestion:
    inhibition applies and no unsafe synthesis can win. Nothing commits, and
    no synthesis reaches the real world or modifies source code.
    """
    from ..executive.action_candidates import ActionCandidate

    label, ctype, scope = _CANDIDATE_MAP.get(
        candidate.synthesis_type,
        ("look", "internal_maintenance_action", "internal_only"))
    return ActionCandidate(
        action_type=ctype, label=label,
        expected_effect=f"synthesis: {candidate.synthesis_type}",
        expected_cost=0.05, expected_risk=float(candidate.expected_risk),
        confidence=float(candidate.confidence), executable_scope=scope,
        metadata={"candidate_id": candidate.candidate_id,
                  "synthesis_type": candidate.synthesis_type,
                  "tension_id": candidate.tension_id,
                  "source": "logos_complexity"})


@dataclass
class SynthesisEngine:
    """Proposes and (when allowed) applies bounded synthesis."""

    safety: LogosComplexitySafetyValidator = field(
        default_factory=LogosComplexitySafetyValidator)
    # Optional safe subsystems (all duck-typed; any may be None).
    hypothesis_engine: Any = None
    active_perception: Any = None
    latent: Any = None
    autoregeneration: Any = None
    world_model: Any = None
    symbol_registry: Any = None
    proposed_total: int = field(default=0, init=False)
    applied_total: int = field(default=0, init=False)
    refused_total: int = field(default=0, init=False)

    # -- proposal -----------------------------------------------------------------

    def propose(self, tension: LogosTension,
                context: Optional[Dict[str, Any]] = None,
                ) -> List[SynthesisCandidate]:
        types = _PROPOSALS.get(tension.tension_type,
                               [SynthesisType.PRESERVE_TENSION])
        candidates: List[SynthesisCandidate] = []
        for stype in types:
            candidate = SynthesisCandidate(
                tension_id=tension.tension_id, synthesis_type=stype,
                proposed_action=self._describe(stype, tension),
                expected_benefit=f"resolve/relieve {tension.tension_type}",
                expected_risk=(0.05 if stype in SynthesisType.REQUEST_ONLY
                               else round(0.1 + 0.2 * (
                                   1.0 - tension.confidence), 4)),
                reversible=stype not in (
                    SynthesisType.PRUNE_LOW_VALUE_RELATION,),
                requires_governance=(tension.risk_level == "high"),
                evidence_refs=list(tension.evidence_refs),
                confidence=tension.confidence,
                metadata={"tension_type": tension.tension_type})
            candidates.append(candidate)
        self.proposed_total += len(candidates)
        return candidates

    @staticmethod
    def _describe(stype: str, tension: LogosTension) -> str:
        return (f"{stype} for {tension.tension_type} "
                f"({tension.polarity_a} vs {tension.polarity_b})")

    def select_candidate(self, candidates: List[SynthesisCandidate],
                        context: Optional[Dict[str, Any]] = None,
                        ) -> Optional[SynthesisCandidate]:
        """Prefer the lowest-risk reversible candidate."""
        if not candidates:
            return None
        runnable = [c for c in candidates
                    if self.safety.validate_synthesis_candidate(
                        c, context).safe]
        pool = runnable or candidates
        return sorted(pool, key=lambda c: (c.expected_risk,
                                           0 if c.reversible else 1))[0]

    # -- application --------------------------------------------------------------

    def apply_if_allowed(self, candidate: SynthesisCandidate,
                        context: Optional[Dict[str, Any]] = None,
                        ) -> SynthesisResult:
        ctx = dict(context or {})
        result = SynthesisResult(
            candidate_id=candidate.candidate_id,
            tension_id=candidate.tension_id,
            synthesis_type=candidate.synthesis_type,
            new_tension_status=_STATUS_FOR.get(candidate.synthesis_type,
                                              TensionStatus.UNRESOLVED))
        report = self.safety.validate_synthesis_candidate(candidate, ctx)
        if not report.safe:
            return self._refuse(result, "; ".join(report.violations))
        if candidate.requires_governance and not ctx.get(
                "governance_approved"):
            return self._refuse(result, "synthesis requires governance "
                                        "approval")
        applied, detail = self._apply(candidate, ctx)
        result.applied = applied
        result.detail = detail
        result.result_class = (
            SynthesisResultClass.PRESERVED
            if candidate.synthesis_type == SynthesisType.PRESERVE_TENSION
            else SynthesisResultClass.APPLIED if applied
            else SynthesisResultClass.INCONCLUSIVE)
        if applied:
            self.applied_total += 1
        return result

    def _apply(self, candidate: SynthesisCandidate,
               ctx: Dict[str, Any]) -> "tuple[bool, str]":
        stype = candidate.synthesis_type
        if stype == SynthesisType.PRESERVE_TENSION:
            return (True, "tension preserved as productive/unresolved")
        if stype == SynthesisType.CREATE_HYPOTHESIS:
            return (True, "hypothesis seed requested from tension")
        if stype == SynthesisType.REQUEST_ACTIVE_SAMPLING:
            return (self.active_perception is not None,
                    "active sampling requested")
        if stype == SynthesisType.REQUEST_LATENT_REPLAY:
            return (True, "latent replay requested (offline)")
        if stype in (SynthesisType.REQUEST_MEMORY_CONSOLIDATION,
                     SynthesisType.REQUEST_AUTO_REGENERATION):
            return (True, f"{stype} requested")
        if stype == SynthesisType.STABILIZE_EXECUTIVE_POLICY:
            return (True, "executive stabilization requested")
        if stype in (SynthesisType.MARK_AMBIGUOUS,
                     SynthesisType.WEAKEN_WORLD_EDGE):
            graph = getattr(self.world_model, "graph", None)
            edge_id = candidate.metadata.get("edge_id")
            if graph is not None and edge_id and edge_id in getattr(
                    graph, "edges", {}):
                edge = graph.edges[edge_id]
                edge.metadata["ambiguous"] = True
                if stype == SynthesisType.WEAKEN_WORLD_EDGE:
                    edge.decay(0.5)
                return (True, f"world edge {edge_id} marked/weakened "
                              "(evidence preserved)")
            return (False, "no world-model edge to mark/weaken")
        if stype in (SynthesisType.MARK_AMBIGUOUS, SynthesisType.SPLIT_SYMBOL,
                     SynthesisType.MERGE_SYMBOLS):
            return (self.symbol_registry is not None,
                    f"{stype} on symbol registry")
        # Other types (create relation / prune / proto-utterance) are
        # request-style markers recorded for the developmental layer.
        return (True, f"{stype} recorded as a proposal")

    def _refuse(self, result: SynthesisResult,
                reason: str) -> SynthesisResult:
        result.refused = True
        result.applied = False
        result.refused_reason = reason
        result.result_class = SynthesisResultClass.REFUSED
        result.new_tension_status = TensionStatus.UNRESOLVED
        self.refused_total += 1
        return result

    def snapshot(self) -> Dict[str, Any]:
        return {
            "proposed_total": self.proposed_total,
            "applied_total": self.applied_total,
            "refused_total": self.refused_total,
        }
