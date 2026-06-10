"""Simple baselines -- the bar Solaris-AI-NN mechanisms must beat.

Each baseline runs the standard tiny world (`light->approach`, etc.) for a
bounded number of steps and reports late-window accuracy plus context, so
experiments can ask "did the mechanism actually help?" against random/fixed/
ablated behaviour.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from ..bridges.neural_bridge import SolarisNeuralBridge
from ..signals import canonical as C
from ..signals.encoding import EventEncoder

WORLD = {"light": "approach", "noise": "withdraw", "food": "consume"}
ACTIONS = ["approach", "withdraw", "consume"]


def _world_loop(steps: int, choose, learn=None, seed: int = 7) -> Dict[str, Any]:
    payloads = list(WORLD.keys())
    hits: List[int] = []
    for i in range(steps):
        payload = payloads[i % len(payloads)]
        action = choose(i, payload)
        hit = 1 if action == WORLD[payload] else 0
        hits.append(hit)
        if learn is not None:
            learn(payload, action, 1.0 if hit else -1.0)
    late = hits[-max(1, len(hits) // 5):]
    return {
        "steps": steps,
        "seed": seed,
        "accuracy": sum(hits) / len(hits) if hits else 0.0,
        "late_accuracy": sum(late) / len(late),
        "bounded": True,
    }


def random_action_baseline(steps: int = 150, seed: int = 7) -> Dict[str, Any]:
    """Uniformly random actions (the floor: ~1/3 on this world)."""
    rng = random.Random(seed)
    out = _world_loop(steps, lambda i, p: rng.choice(ACTIONS), seed=seed)
    return {"baseline": "random_action", **out}


def fixed_action_baseline(steps: int = 150, seed: int = 7,
                          action: str = "approach") -> Dict[str, Any]:
    """Always the same action (~1/3 on this world)."""
    out = _world_loop(steps, lambda i, p: action, seed=seed)
    return {"baseline": "fixed_action", "action": action, **out}


def _bridge(seed: int, **kw: Any) -> SolarisNeuralBridge:
    return SolarisNeuralBridge(
        action_labels=list(ACTIONS),
        encoder=EventEncoder(vocabulary=list(WORLD.keys())),
        seed=seed, **kw)


def _bridge_loop(steps: int, seed: int, bridge: SolarisNeuralBridge,
                 react: bool = True, prune_every: int = 0) -> Dict[str, Any]:
    from ..plasticity.synthesis_pruning import SynthesisPruner

    pruner = SynthesisPruner()

    def choose(i: int, payload: str) -> str:
        result = bridge.process(C.Stimulus(payload=payload, intensity=0.6,
                                           origin="world"))
        if prune_every and (i + 1) % prune_every == 0:
            pruner.prune(bridge.readout, bridge.habit)
        return result["suggested_action"]

    def learn(payload: str, action: str, valence: float) -> None:
        if react:
            bridge.react(C.Reaction(valence=valence))

    return _world_loop(steps, choose, learn, seed=seed)


def no_plasticity_baseline(steps: int = 150, seed: int = 7) -> Dict[str, Any]:
    """Full learning loop, plasticity engine never constructed."""
    out = _bridge_loop(steps, seed, _bridge(seed))
    return {"baseline": "no_plasticity", "plasticity_enabled": False, **out}


def no_habit_baseline(steps: int = 150, seed: int = 7) -> Dict[str, Any]:
    """Habit bias zeroed: the readout learns alone."""
    bridge = _bridge(seed)
    bridge.habit.bias_scale = 0.0
    bridge.habit.lr = 0.0
    out = _bridge_loop(steps, seed, bridge)
    return {"baseline": "no_habit", "habit_disabled": True, **out}


def no_synthesis_baseline(steps: int = 150, seed: int = 7) -> Dict[str, Any]:
    """No pruning ever runs (vs a pruned twin for ablation studies)."""
    out = _bridge_loop(steps, seed, _bridge(seed), prune_every=0)
    return {"baseline": "no_synthesis", "synthesis_disabled": True, **out}


def observe_only_baseline(steps: int = 150, seed: int = 7) -> Dict[str, Any]:
    """Suggestions produced but never any feedback: no learning signal."""
    out = _bridge_loop(steps, seed, _bridge(seed), react=False)
    return {"baseline": "observe_only", "feedback_disabled": True, **out}


ALL_BASELINES = {
    "random_action": random_action_baseline,
    "fixed_action": fixed_action_baseline,
    "no_plasticity": no_plasticity_baseline,
    "no_habit": no_habit_baseline,
    "no_synthesis": no_synthesis_baseline,
    "observe_only": observe_only_baseline,
}


def run_all_baselines(steps: int = 150, seed: int = 7) -> Dict[str, Dict[str, Any]]:
    return {name: fn(steps=steps, seed=seed) for name, fn in ALL_BASELINES.items()}
