"""Interventions -- bounded requests to safe subsystems, never raw execution.

An :class:`Intervention` is a *request* to a safe subsystem (the nursery, the
latent replay engine, the world model, the proto-language layer) to do
something inside simulation / internal replay / read-only observation. There
is no real-world, OS, browser, or network intervention here; ecology safety
and governance validate every request before anything runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class InterventionType:
    SAMPLE_PATTERN = "sample_pattern"
    REPEAT_PATTERN = "repeat_pattern"
    WITHHOLD_SIGNAL = "withhold_signal"
    INTRODUCE_NOVELTY = "introduce_novelty"
    INTRODUCE_ANOMALY = "introduce_anomaly"
    TRIGGER_DELAYED_CONSEQUENCE = "trigger_delayed_consequence"
    RUN_LATENT_REPLAY = "run_latent_replay"
    RUN_COUNTERFACTUAL_REPLAY = "run_counterfactual_replay"
    INSPECT_WORLD_MODEL_NODE = "inspect_world_model_node"
    INSPECT_PROTO_SYMBOL = "inspect_proto_symbol"
    SHIFT_NURSERY_REGIME = "shift_nursery_regime"
    OBSERVE_ONLY = "observe_only"

    ALL = (SAMPLE_PATTERN, REPEAT_PATTERN, WITHHOLD_SIGNAL,
           INTRODUCE_NOVELTY, INTRODUCE_ANOMALY,
           TRIGGER_DELAYED_CONSEQUENCE, RUN_LATENT_REPLAY,
           RUN_COUNTERFACTUAL_REPLAY, INSPECT_WORLD_MODEL_NODE,
           INSPECT_PROTO_SYMBOL, SHIFT_NURSERY_REGIME, OBSERVE_ONLY)

    # Interventions that touch only internal/offline state.
    INTERNAL = frozenset({RUN_LATENT_REPLAY, RUN_COUNTERFACTUAL_REPLAY,
                          INSPECT_WORLD_MODEL_NODE, INSPECT_PROTO_SYMBOL,
                          OBSERVE_ONLY})
    # Interventions that request a bounded nursery/ecology change.
    NURSERY = frozenset({SAMPLE_PATTERN, REPEAT_PATTERN, WITHHOLD_SIGNAL,
                         INTRODUCE_NOVELTY, INTRODUCE_ANOMALY,
                         TRIGGER_DELAYED_CONSEQUENCE, SHIFT_NURSERY_REGIME})


@dataclass
class Intervention:
    """One bounded request to a safe subsystem (never raw execution)."""

    intervention_type: str
    scope: str = "internal_only"
    target_ref: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    requires_ecology_safety: bool = False
    requires_governance: bool = False

    def __post_init__(self) -> None:
        if self.intervention_type not in InterventionType.ALL:
            raise ValueError(f"unknown intervention type "
                             f"{self.intervention_type!r}")
        if self.intervention_type in InterventionType.NURSERY:
            self.requires_ecology_safety = True

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class InterventionPlan:
    """An ordered, bounded set of interventions for one experiment."""

    hypothesis_id: str
    interventions: List[Intervention] = field(default_factory=list)
    max_interventions: int = 4

    def add(self, intervention: Intervention) -> bool:
        if len(self.interventions) >= self.max_interventions:
            return False
        self.interventions.append(intervention)
        return True

    @property
    def bounded(self) -> bool:
        return 0 <= len(self.interventions) <= self.max_interventions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "interventions": [i.to_dict() for i in self.interventions],
            "max_interventions": self.max_interventions,
            "bounded": self.bounded,
        }
