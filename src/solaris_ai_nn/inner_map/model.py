"""Inner MAP data model -- the structured self-model of the NN substrate.

This is the heart of Solaris-AI-NN's self-observation layer. It mirrors
Solaris_Ai's Inner MAP concept (``modules/inner_map.py``): a running, inspectable
model of *what the system currently is*. It makes **no** claim of consciousness;
every field is a concrete, measured property of the substrate, its memory, its
plasticity, its continuity, its boundaries, and its unknowns.

All types are plain dataclasses (stdlib only). The top-level
:class:`InnerMapModel` aggregates the section sub-models and round-trips to/from
JSON via ``to_dict`` / ``from_dict`` (see ``inner_map/serialization.py``).
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ModuleState:
    """A single observed module in the substrate (the 'what exists' answer)."""

    name: str
    role: str = ""
    status: str = "active"
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContinuityState:
    """Runtime continuity (section B): is it alive, and how has it persisted?"""

    alive: bool = True
    lifecycle_state: str = "unknown"
    lifetime_steps: int = 0
    session_steps: int = 0
    restart_count: int = 0
    last_heartbeat_ts: float = 0.0
    last_checkpoint_ts: float = 0.0
    brain_death_gap_seconds: float = 0.0
    graceful_previous_shutdown: bool = True


@dataclass
class NeuralSubstrateState:
    """Neural substrate metrics (section C).

    The "nervous layer" may be any registered substrate (ESN, liquid-state,
    spiking-recurrent); the ``reservoir_*`` names are kept for continuity and
    refer to the active substrate.
    """

    reservoir_size: int = 0
    reservoir_state_norm: float = 0.0
    reservoir_sparsity: float = 0.0
    input_vector_size: int = 0
    readout_output_size: int = 0
    readout_weight_norm: float = 0.0
    prediction_confidence: float = 0.0
    average_prediction_error: float = 0.0
    # Substrate-laboratory observations (Prompt 6).
    substrate_type: str = "esn"
    substrate_activity_rate: float = 0.0
    substrate_drift: float = 0.0
    spike_rate: Optional[float] = None
    silence_ratio: Optional[float] = None
    saturation_ratio: Optional[float] = None
    substrate_switch_history: List[Dict[str, Any]] = field(default_factory=list)
    substrate_comparison: Optional[Dict[str, Any]] = None


@dataclass
class MemoryState:
    """Memory observations (section D)."""

    trace_length: int = 0
    last_signal_types: List[str] = field(default_factory=list)
    dominant_recent_signal_type: Optional[str] = None
    recent_absence_count: int = 0
    recent_reaction_count: int = 0
    consolidated_summaries: List[str] = field(default_factory=list)


@dataclass
class PlasticityState:
    """Habit + synthesis observations (sections E and F) + controlled plasticity."""

    # Habit
    habit_pathways: int = 0
    strongest_habits: List[Dict[str, Any]] = field(default_factory=list)
    most_repeated_mappings: List[Dict[str, Any]] = field(default_factory=list)
    habit_reinforcement_count: int = 0
    # Synthesis
    pruning_count: int = 0
    last_pruning_report: Optional[Dict[str, Any]] = None
    removed_pathway_count: int = 0
    subtraction_ratio: float = 0.0
    # Controlled self-modification (Prompt 5)
    applied_plasticity_count: int = 0
    rejected_plasticity_count: int = 0
    rollback_count: int = 0
    last_applied_step: Optional[Dict[str, Any]] = None
    last_rejected_step: Optional[Dict[str, Any]] = None
    mutable_parameters: Dict[str, Any] = field(default_factory=dict)
    plasticity_safety_status: str = "disabled"
    plasticity_audit_path: Optional[str] = None


@dataclass
class BoundaryState:
    """Observed operational boundaries (section G)."""

    max_reservoir_size: int = 0
    max_trace_length: int = 0
    max_runtime_duration: Optional[float] = None
    max_steps: Optional[int] = None
    continuous_mode_allowed: bool = False
    cpu_only: bool = True
    no_heavy_ml_frameworks: bool = True
    action_authority_suggest_only: bool = True


@dataclass
class TendencyState:
    """Current behavioural tendencies (section H). Suggestions, not decisions."""

    suggested_desire: Optional[str] = None
    suggested_action: Optional[str] = None
    action_tendency_vector: Optional[List[float]] = None
    exploration_tendency: float = 0.0
    stabilization_tendency: float = 0.0
    logos_modulation_influence: Optional[Dict[str, Any]] = None


@dataclass
class UnknownState:
    """Unknown / drift estimates (section I).

    ``unknown_pressure`` is a Mysterium-compatible placeholder: a [0,1]-ish
    scalar standing in for Solaris_Ai's "unknown pressure" until a dedicated
    module exists.
    """

    state_drift_score: float = 0.0
    novelty_estimate: float = 0.0
    unexplained_error_estimate: float = 0.0
    unknown_pressure: float = 0.0


@dataclass
class InnerMapModel:
    """The complete self-model: identity (A) + all observed sections."""

    # A. Identity
    system_name: str = "solaris-ai-nn"
    version: str = "0.1.0"
    run_id: str = ""
    session_id: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # Sections B-I + module inventory.
    continuity: ContinuityState = field(default_factory=ContinuityState)
    neural: NeuralSubstrateState = field(default_factory=NeuralSubstrateState)
    memory: MemoryState = field(default_factory=MemoryState)
    plasticity: PlasticityState = field(default_factory=PlasticityState)
    boundaries: BoundaryState = field(default_factory=BoundaryState)
    tendencies: TendencyState = field(default_factory=TendencyState)
    unknown: UnknownState = field(default_factory=UnknownState)
    modules: List[ModuleState] = field(default_factory=list)
    # Solaris sidecar integration status (Prompt 7); None when no sidecar.
    # Keys: attached, observing, observe_only, compatibility_level,
    # mirrored_signals, suggestions_produced/published,
    # last_suggestion_confidence, action_authority (always False),
    # substrate_type, sidecar_health.
    integration: Optional[Dict[str, Any]] = None
    # Embodiment status (Prompt 8); None when no simulated body exists.
    # Keys: body, body_type, environment_type, position, energy, exhausted,
    # available/forbidden_actions, last_stimulus_types, last_action,
    # last_action_result, last_reaction_valence, environment_boundaries,
    # nearby_objects, action_authority ("simulation-only"), safety_status.
    embodiment: Optional[Dict[str, Any]] = None
    # Internal language layer status (Prompt 9); None when language is off.
    # Keys: enabled, meaning_atom_count, causal_trace_count,
    # last_explanation_summary, dominant_categories, unknown_statements,
    # queryable, last_session_report_path.
    language: Optional[Dict[str, Any]] = None
    # Evaluation/benchmark status (Prompt 10); None until a benchmark ran.
    # Keys: last_run_id, last_scores, last_failure_findings,
    # reproducibility_status, comparison_summary, artifact_paths.
    evaluation: Optional[Dict[str, Any]] = None

    def touch(self) -> None:
        """Mark the model as freshly updated."""
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Recursively serialise to a JSON-friendly dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InnerMapModel":
        """Rebuild a model (with nested sub-models) from a dict."""
        data = dict(data)
        nested = {
            "continuity": ContinuityState,
            "neural": NeuralSubstrateState,
            "memory": MemoryState,
            "plasticity": PlasticityState,
            "boundaries": BoundaryState,
            "tendencies": TendencyState,
            "unknown": UnknownState,
        }
        kwargs: Dict[str, Any] = {}
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        for key, value in data.items():
            if key not in valid:
                continue
            if key in nested and isinstance(value, dict):
                sub = nested[key]
                sub_valid = set(sub.__dataclass_fields__)  # type: ignore[attr-defined]
                kwargs[key] = sub(**{k: v for k, v in value.items() if k in sub_valid})
            elif key == "modules" and isinstance(value, list):
                kwargs[key] = [
                    ModuleState(**{k: v for k, v in m.items()
                                   if k in ModuleState.__dataclass_fields__})  # type: ignore[attr-defined]
                    for m in value
                ]
            else:
                kwargs[key] = value
        return cls(**kwargs)
