"""Research experiment design -- bounded, evidence-scoped, never a real soak.

An :class:`ExperimentDesign` pins one research experiment: its question,
hypothesis, arms (variants and baselines), metrics, and bounds. Experiments are
always bounded (no month-long real runs); long runs are representable only as
plans or fixture analyses; and every conclusion drawn from a design is
evidence-scoped.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ExperimentCondition:
    MINIMAL_RUNTIME = "minimal_runtime"
    FULL_RUNTIME = "full_runtime"
    NURSERY_ONLY = "nursery_only"
    SENSORY_MEMBRANE = "sensory_membrane"
    GRIDWORLD_EMBODIMENT = "gridworld_embodiment"
    MIXED_SENSORY_GRIDWORLD = "mixed_sensory_gridworld"
    SAFETY_FAST_CHECK = "safety_fast_check"
    POST_PILOT_ANALYSIS = "post_pilot_analysis"
    ABLATION_RUN = "ablation_run"
    BASELINE_RUN = "baseline_run"

    ALL = (MINIMAL_RUNTIME, FULL_RUNTIME, NURSERY_ONLY, SENSORY_MEMBRANE,
           GRIDWORLD_EMBODIMENT, MIXED_SENSORY_GRIDWORLD, SAFETY_FAST_CHECK,
           POST_PILOT_ANALYSIS, ABLATION_RUN, BASELINE_RUN)


class ExperimentStatus:
    DESIGNED = "designed"
    RUNNING = "running"
    COMPLETED = "completed"
    UNSAFE = "unsafe"
    INCONCLUSIVE = "inconclusive"
    FAILED = "failed"

    ALL = (DESIGNED, RUNNING, COMPLETED, UNSAFE, INCONCLUSIVE, FAILED)


@dataclass
class ExperimentArm:
    """One arm of an experiment (a variant or a baseline)."""

    arm_id: str
    kind: str  # "variant" | "baseline" | "ablation"
    label: str
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ExperimentProtocol:
    """The bounded procedure an experiment follows."""

    steps: List[str] = field(default_factory=lambda: [
        "safety invariant pre-check",
        "instantiate arms",
        "run bounded scenario per arm",
        "collect metrics and artifacts",
        "safety invariant post-check",
        "compare arms (cautiously)",
        "store results (append-only)"])
    bounded: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"steps": list(self.steps), "bounded": self.bounded}


@dataclass
class ExperimentDesign:
    """One bounded, evidence-scoped research experiment design."""

    title: str
    research_question: str
    hypothesis: str = ""
    condition: str = ExperimentCondition.ABLATION_RUN
    arms: List[ExperimentArm] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    expected_artifacts: List[str] = field(default_factory=list)
    max_steps: int = 40
    max_duration_s: float = 120.0
    seed: int = 7
    base_dir: str = ".solaris_ai_nn_research"
    state_dir: Optional[str] = None
    artifact_dir: Optional[str] = None
    safety_profile: str = "safety_fast_check"
    governance_profile: str = "bounded"
    protocol: ExperimentProtocol = field(default_factory=ExperimentProtocol)
    limitations: List[str] = field(default_factory=list)
    status: str = ExperimentStatus.DESIGNED
    experiment_id: str = field(
        default_factory=lambda: f"EXP_{uuid.uuid4().hex[:10]}")
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.condition not in ExperimentCondition.ALL:
            raise ValueError(f"unknown experiment condition {self.condition!r}")
        # Experiments are bounded by construction.
        if not self.max_steps or self.max_steps <= 0:
            raise ValueError("experiments must be bounded (max_steps > 0)")
        if self.max_steps > 5000:
            raise ValueError("experiments must stay bounded; max_steps too "
                             "large (this is a lab, not a real soak)")
        # Every design carries explicit limitations (evidence-scoped).
        if not self.limitations:
            self.limitations = [
                "Bounded fixture/simulated experiment; not a real long run.",
                "Single-run differences are observed associations, not proven "
                "causes.",
                "Benchmark scores are operational proxies, not consciousness, "
                "sentience, life, personhood, or free will.",
            ]
        import os
        self.state_dir = self.state_dir or os.path.join(self.base_dir, "state")
        self.artifact_dir = self.artifact_dir or os.path.join(self.base_dir,
                                                              "artifacts")

    @property
    def is_real_long_run(self) -> bool:
        return False  # the lab never starts a real long run

    def add_arm(self, arm: ExperimentArm) -> None:
        self.arms.append(arm)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id, "title": self.title,
            "research_question": self.research_question,
            "hypothesis": self.hypothesis, "condition": self.condition,
            "arms": [a.to_dict() for a in self.arms], "metrics": self.metrics,
            "expected_artifacts": self.expected_artifacts,
            "max_steps": self.max_steps, "max_duration_s": self.max_duration_s,
            "seed": self.seed, "state_dir": self.state_dir,
            "artifact_dir": self.artifact_dir,
            "safety_profile": self.safety_profile,
            "governance_profile": self.governance_profile,
            "protocol": self.protocol.to_dict(), "limitations": self.limitations,
            "status": self.status, "is_real_long_run": False,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentDesign":
        arms = [ExperimentArm(**a) for a in data.get("arms", [])]
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items()
                  if k in valid and k not in ("arms", "protocol")}
        design = cls(**kwargs)
        design.arms = arms
        return design
