"""Embodied absence experiment -- a body in a low-stimulus region.

A sparse GridWorld (almost no objects) puts the body through long silence
windows: the AbsenceSensor emits absence Stimuli, the substrate keeps updating,
and the body fills the silence with whatever it suggests (rest, look, ping,
move). Feedback records whether those absence-driven actions turn out useful
(needed rest, novel discoveries) or useless (repetition penalties).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..embodiment.grid_world import GridWorld
from ..embodiment.simulation_runner import SensorimotorSimulationRunner

SPARSE_COUNTS = {"signal_source": 0, "obstacle": 1, "reward_marker": 0,
                 "danger_marker": 0, "unknown_marker": 1}


@dataclass
class EmbodiedAbsenceResult:
    steps: int
    absence_stimuli: int
    absence_ratio: float
    substrate_updates: int
    substrate_drift_during_run: float
    useful_actions: int
    useless_actions: int
    went_inert: bool
    report: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if k != "report"}


def run_embodied_absence(
    steps: int = 300,
    state_dir: Optional[str] = None,
    seed: int = 7,
    substrate: str = "esn",
    width: int = 11,
    height: int = 9,
    verbose: bool = False,
) -> EmbodiedAbsenceResult:
    """Run the sparse-world session and measure absence-driven behaviour."""
    world = GridWorld(width=width, height=height, seed=seed,
                      object_counts=dict(SPARSE_COUNTS), sense_range=2)
    runner = SensorimotorSimulationRunner(
        max_steps=steps, seed=seed, state_dir=state_dir, substrate=substrate,
        world=world,
    )
    report = runner.run()

    absence = sum(1 for r in runner.sensor_history if r.is_absence)
    total_readings = max(1, len(runner.sensor_history))
    # Useful vs useless absence-driven feedback (from recorded valences):
    useful = sum(1 for v in runner.reaction_valences if v > 0)
    useless = runner.feedback.useless_repeats
    metrics = runner.bridge.substrate.metrics()
    went_inert = metrics.state_norm == 0.0 and metrics.drift == 0.0

    result = EmbodiedAbsenceResult(
        steps=report["steps"],
        absence_stimuli=absence,
        absence_ratio=absence / total_readings,
        substrate_updates=report["telemetry"]["reservoir_updates"],
        substrate_drift_during_run=metrics.drift,
        useful_actions=useful,
        useless_actions=useless,
        went_inert=went_inert,
        report=report,
    )

    if verbose:
        print("=" * 70)
        print(f"Solaris-AI-NN -- embodied absence ({steps} steps, sparse world)")
        print("=" * 70)
        print(report["world_ascii"])
        print(f"absence stimuli:           {result.absence_stimuli} "
              f"({result.absence_ratio:.0%} of sensor readings)")
        print(f"substrate updates:         {result.substrate_updates} "
              f"(drift now: {result.substrate_drift_during_run:.4f})")
        print(f"useful / useless feedback: {result.useful_actions} / "
              f"{result.useless_actions} useless repetitions")
        print(f"went inert?                {result.went_inert}")
        counts = sorted(report["action_counts"].items(), key=lambda kv: -kv[1])
        print("absence-window actions:    ",
              ", ".join(f"{a}={n}" for a, n in counts[:5]) or "(none)")
        print("-" * 70)
        print("Absence stimuli kept the substrate moving through the empty world;")
        print("the numbers above say whether the silence-filling actions paid off.")
    return result


def main() -> None:
    run_embodied_absence(verbose=True)


if __name__ == "__main__":
    main()
