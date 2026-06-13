"""Milestones -- the firsts that mark transformation, kept as fossils.

Sixteen milestone types (first 24h survival, first stable habit, first
Mysterium spike, first consolidation, first restart recovery...). Each
fires once, must reference evidence, and becomes a fossil-memory
candidate. "First language-like structure" means internal
symbolic/explanatory structure -- never human-level language.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class MilestoneType:
    FIRST_24H_SURVIVAL = "first_24h_survival"
    FIRST_WEEK_SURVIVAL = "first_week_survival"
    FIRST_MONTH_SURVIVAL = "first_month_survival"
    FIRST_STABLE_HABIT = "first_stable_habit"
    FIRST_HABIT_COLLAPSE = "first_habit_collapse"
    FIRST_MAJOR_PREDICTION_FAILURE = "first_major_prediction_failure"
    FIRST_MYSTERIUM_SPIKE = "first_mysterium_spike"
    FIRST_SUCCESSFUL_CONSOLIDATION = "first_successful_consolidation"
    FIRST_MAJOR_PRUNING = "first_major_pruning"
    FIRST_WORLD_MODEL_SCHEMA = "first_world_model_schema"
    FIRST_IDENTITY_RESTART_RECOVERY = "first_identity_restart_recovery"
    FIRST_BOUNDARY_VIOLATION = "first_boundary_violation"
    FIRST_SAFE_SHUTDOWN = "first_safe_shutdown"
    FIRST_LANGUAGE_LIKE_STRUCTURE = "first_language_like_structure"
    FIRST_LONG_STAGNATION = "first_long_stagnation"
    FIRST_PHASE_TRANSITION = "first_phase_transition"
    # Proto-language (Prompt 22).
    FIRST_PROTO_SYMBOL = "first_proto_symbol"
    FIRST_STABLE_SYMBOL = "first_stable_symbol"
    FIRST_SYMBOL_SEQUENCE = "first_symbol_sequence"
    FIRST_PROTO_SYNTAX_RULE = "first_proto_syntax_rule"
    FIRST_SYMBOL_PREDICTION_IMPROVEMENT = (
        "first_symbol_prediction_improvement")
    FIRST_SYMBOL_EXTINCTION = "first_symbol_extinction"
    FIRST_PROTO_UTTERANCE = "first_proto_utterance"
    # Developmental nursery / stimulus ecology (Prompt 23).
    FIRST_ABSENCE_SYMBOL_FROM_NURSERY = (
        "first_absence_symbol_from_nursery")
    FIRST_ADAPTATION_TO_SEASONAL_SHIFT = (
        "first_adaptation_to_seasonal_shift")
    FIRST_DELAYED_CONSEQUENCE_ASSOCIATION = (
        "first_delayed_consequence_association")
    FIRST_BOUNDARY_PATTERN_LEARNED = "first_boundary_pattern_learned"
    FIRST_DEPRIVATION_RECOVERY = "first_deprivation_recovery"
    FIRST_ANOMALY_SCHEMA = "first_anomaly_schema"
    FIRST_ECOLOGY_PROTO_UTTERANCE = "first_ecology_proto_utterance"

    ALL = (FIRST_24H_SURVIVAL, FIRST_WEEK_SURVIVAL,
           FIRST_MONTH_SURVIVAL, FIRST_STABLE_HABIT,
           FIRST_HABIT_COLLAPSE, FIRST_MAJOR_PREDICTION_FAILURE,
           FIRST_MYSTERIUM_SPIKE, FIRST_SUCCESSFUL_CONSOLIDATION,
           FIRST_MAJOR_PRUNING, FIRST_WORLD_MODEL_SCHEMA,
           FIRST_IDENTITY_RESTART_RECOVERY, FIRST_BOUNDARY_VIOLATION,
           FIRST_SAFE_SHUTDOWN, FIRST_LANGUAGE_LIKE_STRUCTURE,
           FIRST_LONG_STAGNATION, FIRST_PHASE_TRANSITION,
           FIRST_PROTO_SYMBOL, FIRST_STABLE_SYMBOL,
           FIRST_SYMBOL_SEQUENCE, FIRST_PROTO_SYNTAX_RULE,
           FIRST_SYMBOL_PREDICTION_IMPROVEMENT,
           FIRST_SYMBOL_EXTINCTION, FIRST_PROTO_UTTERANCE,
           FIRST_ABSENCE_SYMBOL_FROM_NURSERY,
           FIRST_ADAPTATION_TO_SEASONAL_SHIFT,
           FIRST_DELAYED_CONSEQUENCE_ASSOCIATION,
           FIRST_BOUNDARY_PATTERN_LEARNED, FIRST_DEPRIVATION_RECOVERY,
           FIRST_ANOMALY_SCHEMA, FIRST_ECOLOGY_PROTO_UTTERANCE)


@dataclass
class Milestone:
    """One first, with mandatory evidence."""

    type: str
    description: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    lifetime_s: float = 0.0
    simulated: bool = True
    fossil_candidate: bool = True
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if not self.evidence_refs:
            raise ValueError("a milestone must reference evidence")
        if self.type not in MilestoneType.ALL:
            raise ValueError(f"unknown milestone type {self.type!r}")

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


# (milestone type, description template, predicate over context).
_RULES = (
    (MilestoneType.FIRST_24H_SURVIVAL,
     "Runtime survived 24h equivalent.",
     lambda c: c.get("runtime_hours", 0.0) >= 24.0),
    (MilestoneType.FIRST_WEEK_SURVIVAL,
     "Runtime survived one week equivalent.",
     lambda c: c.get("runtime_hours", 0.0) >= 24.0 * 7),
    (MilestoneType.FIRST_MONTH_SURVIVAL,
     "Runtime survived one month equivalent.",
     lambda c: c.get("runtime_hours", 0.0) >= 24.0 * 30),
    (MilestoneType.FIRST_STABLE_HABIT,
     "First stable habit formed.",
     lambda c: c.get("stable_habit_count", 0) >= 1),
    (MilestoneType.FIRST_HABIT_COLLAPSE,
     "A previously stable habit collapsed.",
     lambda c: c.get("habit_collapse_count", 0) >= 1),
    (MilestoneType.FIRST_MAJOR_PREDICTION_FAILURE,
     "First major prediction failure recorded.",
     lambda c: c.get("major_prediction_failures", 0) >= 1),
    (MilestoneType.FIRST_MYSTERIUM_SPIKE,
     "Prediction failure raised Mysterium pressure sharply.",
     lambda c: c.get("mysterium_pressure", 0.0) >= 0.7),
    (MilestoneType.FIRST_SUCCESSFUL_CONSOLIDATION,
     "First memory consolidation completed.",
     lambda c: c.get("consolidation_count", 0) >= 1),
    (MilestoneType.FIRST_MAJOR_PRUNING,
     "First major pruning/synthesis pass recorded.",
     lambda c: c.get("pruning_count", 0) >= 1),
    (MilestoneType.FIRST_WORLD_MODEL_SCHEMA,
     "World model recorded its first stable schema.",
     lambda c: c.get("consolidated_schema_count", 0) >= 1
     or c.get("world_model_schema_count", 0) >= 1),
    (MilestoneType.FIRST_IDENTITY_RESTART_RECOVERY,
     "Restart gap detected and identity continuity restored.",
     lambda c: c.get("restart_recovery_count", 0) >= 1),
    (MilestoneType.FIRST_BOUNDARY_VIOLATION,
     "A boundary violation was recorded (and blocked).",
     lambda c: c.get("boundary_violation_count", 0) >= 1),
    (MilestoneType.FIRST_SAFE_SHUTDOWN,
     "First graceful safe shutdown completed.",
     lambda c: c.get("safe_shutdown_count", 0) >= 1),
    (MilestoneType.FIRST_LANGUAGE_LIKE_STRUCTURE,
     "First internal symbolic/explanatory structure recorded (not "
     "human-level language).",
     lambda c: c.get("meaning_atom_count", 0) >= 50
     or c.get("explanation_count", 0) >= 1),
    (MilestoneType.FIRST_LONG_STAGNATION,
     "First long stagnation window recorded.",
     lambda c: c.get("stagnation_windows", 0) >= 3),
    (MilestoneType.FIRST_PHASE_TRANSITION,
     "First phase-transition candidate recorded (a hypothesis, not "
     "proof of emergence).",
     lambda c: c.get("phase_transition_candidates", 0) >= 1),
    (MilestoneType.FIRST_PROTO_SYMBOL,
     "First internal proto-symbol generated from repeated experience "
     "(an operational sign, not human language).",
     lambda c: c.get("proto_symbol_count", 0) >= 1),
    (MilestoneType.FIRST_STABLE_SYMBOL,
     "First proto-symbol reached stability (repeated, consistently "
     "grounded observation).",
     lambda c: c.get("stable_symbol_count", 0) >= 1),
    (MilestoneType.FIRST_SYMBOL_SEQUENCE,
     "First repeated proto-symbol sequence recorded.",
     lambda c: c.get("symbol_sequence_count", 0) >= 1),
    (MilestoneType.FIRST_PROTO_SYNTAX_RULE,
     "First proto-syntactic regularity inferred (a tested statistical "
     "pattern, not human grammar).",
     lambda c: c.get("proto_syntax_rule_count", 0) >= 1),
    (MilestoneType.FIRST_SYMBOL_PREDICTION_IMPROVEMENT,
     "Proto-symbols first improved prediction over the baseline.",
     lambda c: (c.get("symbol_prediction_improvement") or 0) > 0),
    (MilestoneType.FIRST_SYMBOL_EXTINCTION,
     "First proto-symbol went extinct (named structure that stopped "
     "recurring).",
     lambda c: c.get("symbol_extinction_count", 0) >= 1),
    (MilestoneType.FIRST_PROTO_UTTERANCE,
     "First proto-utterance built (an internal symbolic sequence, not "
     "speech).",
     lambda c: c.get("proto_utterance_count", 0) >= 1),
    (MilestoneType.FIRST_ABSENCE_SYMBOL_FROM_NURSERY,
     "First absence symbol emerged from nursery silence windows.",
     lambda c: c.get("nursery_absence_windows", 0) >= 3
     and c.get("stable_symbol_count", 0) >= 1),
    (MilestoneType.FIRST_ADAPTATION_TO_SEASONAL_SHIFT,
     "First seasonal shift was followed by structural adaptation.",
     lambda c: c.get("nursery_seasonal_shifts", 0) >= 1
     and c.get("structural_change_score", 0.0) > 0.0),
    (MilestoneType.FIRST_DELAYED_CONSEQUENCE_ASSOCIATION,
     "First candidate association across a delayed-consequence group.",
     lambda c: c.get("nursery_delayed_groups", 0) >= 1
     and c.get("world_model_node_count", 0) >= 5),
    (MilestoneType.FIRST_BOUNDARY_PATTERN_LEARNED,
     "First recurring boundary pattern recorded from the ecology.",
     lambda c: c.get("nursery_boundary_events", 0) >= 3),
    (MilestoneType.FIRST_DEPRIVATION_RECOVERY,
     "First recovery after a bounded deprivation/silence window.",
     lambda c: c.get("nursery_deprivation_recoveries", 0) >= 1),
    (MilestoneType.FIRST_ANOMALY_SCHEMA,
     "First schema-like response to a repeated anomaly pattern.",
     lambda c: c.get("nursery_anomaly_events", 0) >= 2),
    (MilestoneType.FIRST_ECOLOGY_PROTO_UTTERANCE,
     "First proto-utterance grounded in an ecology event sequence.",
     lambda c: c.get("nursery_ecology_utterances", 0) >= 1),
)


@dataclass
class MilestoneRegistry:
    """Every milestone exactly once, with its evidence."""

    milestones: List[Milestone] = field(default_factory=list)

    def has(self, milestone_type: str) -> bool:
        return any(m.type == milestone_type for m in self.milestones)

    def record(self, milestone: Milestone) -> Optional[Milestone]:
        if self.has(milestone.type):
            return None  # each first fires once
        self.milestones.append(milestone)
        return milestone

    def fossil_candidates(self) -> List[Milestone]:
        return [m for m in self.milestones if m.fossil_candidate]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "count": len(self.milestones),
            "types_recorded": [m.type for m in self.milestones],
            "latest": (self.milestones[-1].to_dict()
                       if self.milestones else None),
        }


@dataclass
class MilestoneDetector:
    """Fires each milestone once when its context predicate holds."""

    registry: MilestoneRegistry = field(default_factory=MilestoneRegistry)

    def detect(self, context: Dict[str, Any], lifetime_s: float = 0.0,
               simulated: bool = True) -> List[Milestone]:
        new: List[Milestone] = []
        for milestone_type, description, predicate in _RULES:
            if self.registry.has(milestone_type):
                continue
            if predicate(context):
                evidence = [f"{key}={context[key]}" for key in context
                            if isinstance(context[key], (int, float))
                            and context[key]][:4] or ["context"]
                milestone = Milestone(
                    type=milestone_type, description=description,
                    evidence_refs=evidence, lifetime_s=lifetime_s,
                    simulated=simulated)
                if self.registry.record(milestone):
                    new.append(milestone)
        return new

    def snapshot(self) -> Dict[str, Any]:
        return self.registry.snapshot()
