"""Experiment design -- a bounded, falsifiable plan to test a hypothesis.

Every :class:`ExperimentDesign` is bounded (max steps / duration), declares
what would count as the expected result, what would falsify or weaken the
hypothesis, and what would count as inconclusive. Real-world action scope is
prohibited; the scope is one of latent replay, nursery simulation, GridWorld
simulation, read-only stream observation, sidecar observation, or internal
trace analysis.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .hypotheses import Hypothesis, HypothesisScope, HypothesisType
from .interventions import Intervention, InterventionPlan, InterventionType


class ExperimentScope:
    LATENT_REPLAY = "latent_replay"
    NURSERY_SIMULATION = "nursery_simulation"
    GRIDWORLD_SIMULATION = "gridworld_simulation"
    READ_ONLY_STREAM_OBSERVATION = "read_only_stream_observation"
    SIDECAR_OBSERVATION = "sidecar_observation"
    INTERNAL_TRACE_ANALYSIS = "internal_trace_analysis"

    ALL = (LATENT_REPLAY, NURSERY_SIMULATION, GRIDWORLD_SIMULATION,
           READ_ONLY_STREAM_OBSERVATION, SIDECAR_OBSERVATION,
           INTERNAL_TRACE_ANALYSIS)


# Hypothesis required_scope -> experiment scope.
_SCOPE_MAP = {
    HypothesisScope.INTERNAL_ONLY: ExperimentScope.INTERNAL_TRACE_ANALYSIS,
    HypothesisScope.SIMULATION_ONLY: ExperimentScope.GRIDWORLD_SIMULATION,
    HypothesisScope.NURSERY_ONLY: ExperimentScope.NURSERY_SIMULATION,
    HypothesisScope.LATENT_REPLAY_ONLY: ExperimentScope.LATENT_REPLAY,
    HypothesisScope.READ_ONLY_STREAM:
        ExperimentScope.READ_ONLY_STREAM_OBSERVATION,
    HypothesisScope.SIDECAR_OBSERVE_ONLY: ExperimentScope.SIDECAR_OBSERVATION,
}


@dataclass
class ExperimentVariable:
    """One independent or observed variable, named and grounded."""

    name: str
    description: str = ""
    kind: str = "observed"  # independent | observed | control

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ExperimentControl:
    """An optional control condition for the experiment."""

    description: str
    holds_constant: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ExperimentOutcome:
    """What was expected, what would falsify, and what is inconclusive."""

    expected_result: str
    falsifying_result: str
    inconclusive_result: str = "insufficient evidence within the bound"

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ExperimentDesign:
    """A bounded, falsifiable test plan for one hypothesis."""

    hypothesis_id: str
    scope: str
    independent_variable: str
    observed_variable: str
    expected_result: str
    falsifying_result: str
    inconclusive_result: str = "insufficient evidence within the bound"
    control_condition: Optional[str] = None
    max_steps: int = 60
    max_duration_s: float = 30.0
    required_safety: List[str] = field(default_factory=list)
    required_governance: List[str] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    artifact_paths: List[str] = field(default_factory=list)
    intervention_plan: Optional[InterventionPlan] = None
    design_id: str = field(
        default_factory=lambda: f"EXP_{uuid.uuid4().hex[:8]}")
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.scope not in ExperimentScope.ALL:
            raise ValueError(f"unknown experiment scope {self.scope!r}")
        # The value is kept as declared so the safety validator can refuse an
        # unbounded design; the runner additionally caps live interaction.
        self.max_steps = int(self.max_steps)

    def to_dict(self) -> Dict[str, Any]:
        data = dict(self.__dict__)
        data["intervention_plan"] = (self.intervention_plan.to_dict()
                                     if self.intervention_plan else None)
        return data


# Hypothesis type -> (independent var, observed var, metric, intervention).
_DESIGN_HINTS = {
    HypothesisType.PREDICTION: (
        "stimulus pattern", "reaction valence / prediction hit",
        "prediction_accuracy", InterventionType.REPEAT_PATTERN),
    HypothesisType.CAUSAL_CANDIDATE: (
        "presence of the cause", "presence of the effect",
        "edge_weight", InterventionType.RUN_COUNTERFACTUAL_REPLAY),
    HypothesisType.DELAYED_CONSEQUENCE: (
        "the earlier signal", "the later consequence",
        "delay_steps", InterventionType.TRIGGER_DELAYED_CONSEQUENCE),
    HypothesisType.PROTO_SYMBOL_GROUNDING: (
        "grounding context", "symbol ambiguity score",
        "ambiguity_score", InterventionType.INSPECT_PROTO_SYMBOL),
    HypothesisType.PROTO_SYNTAX: (
        "held-out sequences", "rule validation outcome",
        "rule_validated", InterventionType.RUN_LATENT_REPLAY),
    HypothesisType.HABIT_CONTEXT: (
        "context", "habit value", "habit_value",
        InterventionType.INSPECT_WORLD_MODEL_NODE),
    HypothesisType.BOUNDARY: (
        "boundary event", "executive inhibition",
        "inhibition_rate", InterventionType.OBSERVE_ONLY),
    HypothesisType.MYSTERIUM_REDUCTION: (
        "targeted sampling", "unknown pressure",
        "mysterium_pressure", InterventionType.RUN_LATENT_REPLAY),
    HypothesisType.STAGNATION_RECOVERY: (
        "novelty sampling", "structural change score",
        "structural_change_score", InterventionType.INTRODUCE_NOVELTY),
    HypothesisType.HOMEOSTATIC_REGULATION: (
        "need conflict", "dominant drive stability",
        "conflict_count", InterventionType.OBSERVE_ONLY),
    HypothesisType.EXECUTIVE_ARBITRATION: (
        "context", "inhibition outcome", "inhibition_rate",
        InterventionType.OBSERVE_ONLY),
    HypothesisType.WORLD_MODEL_EDGE: (
        "more observation/replay", "edge weight/confidence",
        "edge_weight", InterventionType.INSPECT_WORLD_MODEL_NODE),
    HypothesisType.ANOMALY_PATTERN: (
        "anomaly occurrence", "anomaly recurrence regularity",
        "anomaly_rate", InterventionType.OBSERVE_ONLY),
}


# Experiment scope -> (executive label, candidate action_type, exec scope).
_CANDIDATE_MAP = {
    ExperimentScope.LATENT_REPLAY: ("run_replay", "latent_action",
                                    "internal_only"),
    ExperimentScope.INTERNAL_TRACE_ANALYSIS: (
        "look", "internal_maintenance_action", "internal_only"),
    ExperimentScope.NURSERY_SIMULATION: ("look", "simulated_embodied_action",
                                         "simulation_only"),
    ExperimentScope.GRIDWORLD_SIMULATION: (
        "look", "simulated_embodied_action", "simulation_only"),
    ExperimentScope.READ_ONLY_STREAM_OBSERVATION: (
        "remain_observe_only", "internal_maintenance_action",
        "internal_only"),
    ExperimentScope.SIDECAR_OBSERVATION: (
        "remain_observe_only", "internal_maintenance_action",
        "internal_only"),
}


def design_to_candidate(design: ExperimentDesign) -> Any:
    """One ExperimentDesign -> one executive ActionCandidate (a suggestion).

    A hypothesis test enters executive arbitration like any other
    suggestion: inhibition and prospection apply and no unsafe test can win.
    The candidate never commits and never reaches the real world.
    """
    from ..executive.action_candidates import ActionCandidate

    label, action_type, scope = _CANDIDATE_MAP.get(
        design.scope, ("look", "internal_maintenance_action",
                       "internal_only"))
    return ActionCandidate(
        action_type=action_type, label=label,
        expected_effect=f"test hypothesis {design.hypothesis_id} "
                        f"({design.scope})",
        expected_cost=0.05, expected_risk=0.05, confidence=0.5,
        executable_scope=scope,
        metadata={"design_id": design.design_id,
                  "hypothesis_id": design.hypothesis_id,
                  "experiment_scope": design.scope,
                  "source": "hypothesis_engine"})


def design_for(hypothesis: Hypothesis, max_steps: int = 60) -> ExperimentDesign:
    """Build a bounded, falsifiable design for one hypothesis."""
    scope = _SCOPE_MAP.get(hypothesis.required_scope,
                           ExperimentScope.INTERNAL_TRACE_ANALYSIS)
    independent, observed, metric, intervention_type = _DESIGN_HINTS.get(
        hypothesis.type,
        ("input", "output", "metric", InterventionType.OBSERVE_ONLY))
    plan = InterventionPlan(hypothesis_id=hypothesis.hypothesis_id)
    plan.add(Intervention(
        intervention_type=intervention_type,
        scope=hypothesis.required_scope, target_ref=hypothesis.target_ref))
    expected = (hypothesis.expected_observation
                or f"{observed} moves as expected")
    falsifying = (hypothesis.alternative_observation
                  or f"{observed} does not move as expected")
    design = ExperimentDesign(
        hypothesis_id=hypothesis.hypothesis_id, scope=scope,
        independent_variable=independent, observed_variable=observed,
        expected_result=expected, falsifying_result=falsifying,
        max_steps=max_steps, metrics=[metric],
        intervention_plan=plan,
        metadata={"hypothesis_type": hypothesis.type,
                  "required_scope": hypothesis.required_scope})
    return design
