"""Baseline agents -- simple, low-compute reference policies.

A :class:`BaselineAgent` runs a simple, bounded policy and produces a result in
the same metric format as a Solaris variant, so the full system can be compared
honestly against trivial references. Baselines are deterministic given a seed,
take no real-world action, and (in GridWorld) act simulation-only. There is no
LLM baseline and no external-API baseline.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class BaselineAgentType:
    RANDOM_ACTION = "random_action_baseline"
    FIXED_WAIT = "fixed_wait_baseline"
    FIXED_EXPLORE = "fixed_explore_baseline"
    REACTIVE_NO_MEMORY = "reactive_no_memory_baseline"
    MEMORY_ONLY = "memory_only_baseline"
    WORLD_MODEL_ONLY = "world_model_only_baseline"
    ACTIVE_PERCEPTION_ONLY = "active_perception_only_baseline"
    HYPOTHESIS_ONLY = "hypothesis_only_baseline"
    GRIDWORLD_RANDOM_WALK = "gridworld_random_walk_baseline"
    SENSORY_PASSIVE_OBSERVER = "sensory_passive_observer_baseline"

    ALL = (RANDOM_ACTION, FIXED_WAIT, FIXED_EXPLORE, REACTIVE_NO_MEMORY,
           MEMORY_ONLY, WORLD_MODEL_ONLY, ACTIVE_PERCEPTION_ONLY,
           HYPOTHESIS_ONLY, GRIDWORLD_RANDOM_WALK, SENSORY_PASSIVE_OBSERVER)
    # Baselines that (simulation-only) act in GridWorld.
    GRIDWORLD = frozenset({RANDOM_ACTION, FIXED_EXPLORE, GRIDWORLD_RANDOM_WALK})


# A small, fixed action vocabulary (all simulation-only / internal).
_SIM_ACTIONS = ("look", "wait", "rest", "move_north", "move_south",
                "move_east", "move_west")


@dataclass
class BaselineRunResult:
    """The result of one bounded baseline run (variant-compatible metrics)."""

    baseline_type: str
    steps: int
    actions_taken: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    real_world_action_count: int = 0
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class BaselineAgent:
    """A simple, bounded reference policy; no real-world action."""

    baseline_type: str
    seed: int = 7
    max_steps: int = 40

    def __post_init__(self) -> None:
        if self.baseline_type not in BaselineAgentType.ALL:
            raise ValueError(f"unknown baseline {self.baseline_type!r}")
        self._rng = random.Random(self.seed)

    def _choose(self, step: int) -> str:
        b = self.baseline_type
        T = BaselineAgentType
        if b in (T.FIXED_WAIT, T.SENSORY_PASSIVE_OBSERVER):
            return "wait"
        if b == T.FIXED_EXPLORE:
            return "move_east"
        if b in (T.RANDOM_ACTION, T.GRIDWORLD_RANDOM_WALK):
            return self._rng.choice(_SIM_ACTIONS)
        if b == T.MEMORY_ONLY:
            return "rest" if step % 3 else "look"
        if b == T.WORLD_MODEL_ONLY:
            return "look"
        if b == T.ACTIVE_PERCEPTION_ONLY:
            return self._rng.choice(("look", "wait"))
        if b == T.HYPOTHESIS_ONLY:
            return "look" if step % 2 else "wait"
        return "wait"  # reactive_no_memory default

    def run(self, max_steps: Optional[int] = None) -> BaselineRunResult:
        n = int(max_steps if max_steps is not None else self.max_steps)
        n = max(1, min(n, 5000))  # bounded by construction
        actions = [self._choose(i) for i in range(n)]
        # Simple, honest metrics: a baseline produces little structure.
        distinct = len(set(actions))
        metrics = {
            "structural_change_score": round(0.05 * distinct, 4),
            "prediction_accuracy": 0.0,
            "compression_ratio": 1.0,
            "proto_symbol_count": 0,
            "world_model_node_count": 0,
            "useful_sampling_ratio": (0.0 if self.baseline_type
                                      != BaselineAgentType.ACTIVE_PERCEPTION_ONLY
                                      else 0.1),
            "action_grounding_quality": "unsupported",
            "simulated_action_count": (n if self.baseline_type
                                       in BaselineAgentType.GRIDWORLD else 0),
            "non_actuation_proof_score": 1.0,
            "invariant_pass_rate": 1.0,
        }
        return BaselineRunResult(
            baseline_type=self.baseline_type, steps=n, actions_taken=actions,
            metrics=metrics, real_world_action_count=0,
            notes=["baseline is simulation/internal only; no real-world action",
                   "baselines are trivial references, not Solaris variants"])
