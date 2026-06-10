"""Reward/danger adaptation experiment.

A GridWorld rich in reward and danger markers (rewards replenish when consumed,
so the learning signal persists). Approaching/consuming rewards earns positive
valence; approaching/standing on danger earns negative valence. The experiment
splits the run into early and late halves and reports whether action tendencies
measurably shifted toward reward and away from danger -- or clearly states that
no change was detected. Both are valid findings.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..embodiment.grid_world import REWARD, GridWorld
from ..embodiment.simulation_runner import SensorimotorSimulationRunner

RICH_COUNTS = {"signal_source": 1, "obstacle": 1, "reward_marker": 3,
               "danger_marker": 3, "unknown_marker": 0}


@dataclass
class RewardDangerResult:
    steps: int
    reactions_recorded: int
    early_mean_valence: float
    late_mean_valence: float
    early_reward_events: int
    late_reward_events: int
    early_danger_events: int
    late_danger_events: int
    tendencies_changed: bool
    verdict: str
    report: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if k != "report"}


class _ReplenishingRunner(SensorimotorSimulationRunner):
    """Runner that re-places consumed rewards so the gradient never vanishes."""

    def __post_init__(self) -> None:
        super().__post_init__()
        self._replenish_rng = random.Random(self.seed + 999)
        self.reward_events_log: List[Dict[str, Any]] = []
        self.danger_events_log: List[Dict[str, Any]] = []
        self._step_no = 0

    def _do_step(self, step: int) -> None:
        self._step_no = step
        before_reactions = len(self.reaction_valences)
        super()._do_step(step)
        if len(self.reaction_valences) > before_reactions:
            reasons = getattr(self.feedback, "last_reasons", [])
            if any(r in ("closer_to_reward", "consumed_reward",
                         "standing_on_reward") for r in reasons):
                self.reward_events_log.append({"step": step})
            if any(r in ("closer_to_danger", "touched_danger",
                         "standing_on_danger") for r in reasons):
                self.danger_events_log.append({"step": step})
        # Replenish: keep the configured number of rewards on the board.
        want = RICH_COUNTS["reward_marker"]
        have = sum(1 for k in self.world.objects.values() if k == REWARD)
        while have < want:
            free = [(x, y) for x in range(self.world.width)
                    for y in range(self.world.height)
                    if (x, y) not in self.world.objects
                    and (x, y) != self.world.agent_pos]
            if not free:
                break
            self.world.objects[self._replenish_rng.choice(free)] = REWARD
            have += 1


def run_reward_danger_adaptation(
    steps: int = 300,
    state_dir: Optional[str] = None,
    seed: int = 7,
    substrate: str = "esn",
    verbose: bool = False,
) -> RewardDangerResult:
    """Run the bounded adaptation session and grade early-vs-late tendencies."""
    world = GridWorld(width=9, height=9, seed=seed,
                      object_counts=dict(RICH_COUNTS))
    runner = _ReplenishingRunner(
        max_steps=steps, seed=seed, state_dir=state_dir, substrate=substrate,
        world=world,
    )
    report = runner.run()
    half = steps // 2

    valences = runner.reaction_valences
    # Reactions are not step-indexed; approximate halves by order.
    mid = len(valences) // 2
    early_v = valences[:mid] or [0.0]
    late_v = valences[mid:] or [0.0]
    early_mean = sum(early_v) / len(early_v)
    late_mean = sum(late_v) / len(late_v)

    early_reward = sum(1 for e in runner.reward_events_log if e["step"] <= half)
    late_reward = sum(1 for e in runner.reward_events_log if e["step"] > half)
    early_danger = sum(1 for e in runner.danger_events_log if e["step"] <= half)
    late_danger = sum(1 for e in runner.danger_events_log if e["step"] > half)

    improved_valence = late_mean > early_mean + 0.02
    improved_ratio = (late_reward - late_danger) > (early_reward - early_danger)
    changed = improved_valence or improved_ratio
    if changed:
        verdict = ("action tendencies shifted toward reward / away from danger "
                   f"(mean valence {early_mean:.3f} -> {late_mean:.3f}; "
                   f"reward-danger balance {early_reward - early_danger} -> "
                   f"{late_reward - late_danger})")
    else:
        verdict = ("no clear tendency change detected in this run "
                   f"(mean valence {early_mean:.3f} -> {late_mean:.3f}) -- "
                   "reported honestly rather than claimed")

    result = RewardDangerResult(
        steps=report["steps"], reactions_recorded=len(valences),
        early_mean_valence=early_mean, late_mean_valence=late_mean,
        early_reward_events=early_reward, late_reward_events=late_reward,
        early_danger_events=early_danger, late_danger_events=late_danger,
        tendencies_changed=changed, verdict=verdict, report=report,
    )

    if verbose:
        print("=" * 70)
        print(f"Solaris-AI-NN -- reward/danger adaptation ({steps} steps)")
        print("=" * 70)
        print(report["world_ascii"])
        print(f"reactions recorded:   {result.reactions_recorded}")
        print(f"mean valence:         early {early_mean:.3f} -> late {late_mean:.3f}")
        print(f"reward events:        early {early_reward} -> late {late_reward}")
        print(f"danger events:        early {early_danger} -> late {late_danger}")
        print(f"rewards consumed:     {report['rewards_consumed']}")
        print(f"tendencies changed:   {result.tendencies_changed}")
        print(f"verdict:              {result.verdict}")
        print("-" * 70)
        print("Feedback shaped tendencies through online learning + habit only;")
        print("all of it inside the simulation. No consciousness is claimed.")
    return result


def main() -> None:
    run_reward_danger_adaptation(verbose=True)


if __name__ == "__main__":
    main()
