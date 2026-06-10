"""Sensorimotor GridWorld experiment -- the full embodied loop, bounded.

A simulated body in a grid world perceives (proximity/contact/boundary/energy/
absence/clock), the neural bridge suggests actions, safe actions execute in the
simulation, consequences come back as Reactions, and the substrate adapts
online. The report shows the final ASCII world, action/reaction/energy
summaries, strongest habits, substrate metrics, and the Inner MAP embodiment
view. Simulation-only; no real-world actuation; no consciousness claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..embodiment.simulation_runner import SensorimotorSimulationRunner


@dataclass
class SensorimotorResult:
    report: Dict[str, Any]
    persistence_paths: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"report": self.report, "persistence_paths": self.persistence_paths}


def run_sensorimotor_gridworld(
    steps: int = 300,
    state_dir: Optional[str] = None,
    seed: int = 7,
    substrate: str = "esn",
    observe_only: bool = False,
    enable_plasticity: bool = False,
    width: int = 9,
    height: int = 7,
    verbose: bool = False,
) -> SensorimotorResult:
    """Run the bounded sensorimotor session and return its report."""
    runner = SensorimotorSimulationRunner(
        max_steps=steps, seed=seed, state_dir=state_dir, substrate=substrate,
        execute_suggestions=not observe_only, enable_plasticity=enable_plasticity,
        width=width, height=height,
    )
    report = runner.run()
    paths = runner.persist() if state_dir is not None else {}
    result = SensorimotorResult(report=report, persistence_paths=paths)

    if verbose:
        _print_report(runner, report, paths)
    return result


def _print_report(runner, report: Dict[str, Any], paths: Dict[str, str]) -> None:
    print("=" * 70)
    print(f"Solaris-AI-NN -- sensorimotor GridWorld "
          f"({report['steps']} steps, substrate={report['substrate']}, "
          f"observe_only={report['observe_only']})")
    print("=" * 70)
    print("final world:")
    print(report["world_ascii"])
    print("-" * 70)
    counts = sorted(report["action_counts"].items(), key=lambda kv: -kv[1])
    print(f"actions executed/blocked: {report['actions_executed']} / "
          f"{report['actions_blocked']}  (collisions: {report['collisions']})")
    print("action counts:           ",
          ", ".join(f"{a}={n}" for a, n in counts[:6]) or "(none)")
    rx = report["reactions"]
    print(f"reactions:                {rx['count']} "
          f"(+{rx['positive']} / -{rx['negative']}, "
          f"mean valence {rx['mean_valence']:.3f})")
    en = report["energy"]
    print(f"energy:                   {en['energy']:.2f}/{en['max_energy']} "
          f"(exhaustion events: {en['exhaustion_events']}, "
          f"spent: {en['spent_total']:.1f})")
    print(f"rewards consumed:         {report['rewards_consumed']}")
    habits = sorted(runner.bridge.habit.weights.items(),
                    key=lambda kv: abs(kv[1]), reverse=True)[:4]
    print("strongest habits:")
    for (pattern, action), w in habits:
        print(f"    {pattern} -> {action}  (w={w:.3f})")
    m = report["substrate_metrics"]
    print(f"substrate metrics:        norm={m['state_norm']:.3f} "
          f"activity={m['activity_rate']:.3f} drift={m['drift']:.3f}")
    emb = report["embodiment"]
    print(f"Inner MAP embodiment:     position={emb['position']} "
          f"energy={emb['energy']:.2f} authority={emb['action_authority']}")
    if report["plasticity"]:
        print(f"plasticity:               applied={report['plasticity']['applied_count']} "
              f"rejected={report['plasticity']['rejected_count']}")
    if paths:
        print("persisted:")
        for key, path in paths.items():
            print(f"    {key}: {path}")
    print("-" * 70)
    print("All actions were simulated; action authority is simulation-only.")
    print("No real-world actuation occurred; no consciousness is claimed.")


def main() -> None:
    run_sensorimotor_gridworld(verbose=True)


if __name__ == "__main__":
    main()
