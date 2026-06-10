"""Substrate comparison experiment.

Runs the *same deterministic event trace* (stimuli, silences, reactions) through
each selected substrate -- ESN, liquid-state, spiking-recurrent -- via identical
bridges, and reports a side-by-side table of:

* activity rate / state drift (substrate dynamics),
* readout adaptation speed (early vs late accuracy) and prediction error,
* habit reinforcement and synthesis pruning counts,
* runtime duration, memory trace length,
* a crude energy proxy (updates/sec per average active unit -- NOT a power
  measurement).

The point is not to crown a winner; it is to make the substrates' different
temporal characters measurable under the same Solaris signal ecology.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..bridges.neural_bridge import SolarisNeuralBridge
from ..plasticity.synthesis_pruning import SynthesisPruner
from ..runtime.persistence import PersistenceManager
from ..signals import canonical as C
from ..signals.encoding import EventEncoder
from ..substrates.comparison import ComparisonReport, energy_proxy
from ..substrates.registry import SubstrateRegistry

WORLD: Dict[str, str] = {"light": "approach", "noise": "withdraw", "food": "consume"}
ACTIONS: List[str] = ["approach", "withdraw", "consume"]
DEFAULT_SUBSTRATES: List[str] = ["esn", "liquid_state", "spiking_recurrent"]


def _event_trace(steps: int) -> List[Optional[str]]:
    """The shared deterministic event schedule: payload or None (silence)."""
    payloads = list(WORLD.keys())
    trace: List[Optional[str]] = []
    for step in range(steps):
        if step % 9 < 2:  # a small silence window in every cycle of 9
            trace.append(None)
        else:
            trace.append(payloads[step % len(payloads)])
    return trace


@dataclass
class SubstrateComparisonResult:
    """Per-substrate metric rows plus the rendered table."""

    report: ComparisonReport
    steps: int
    seed: int
    rows: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def table(self) -> str:
        return self.report.table()

    def to_dict(self) -> Dict[str, Any]:
        return {"steps": self.steps, "seed": self.seed, "rows": self.rows}


def _run_one(name: str, trace: List[Optional[str]], seed: int) -> Dict[str, Any]:
    encoder = EventEncoder(vocabulary=list(WORLD.keys()) + ["I exist!"])
    bridge = SolarisNeuralBridge(
        action_labels=ACTIONS, encoder=encoder, substrate_name=name, seed=seed)
    pruner = SynthesisPruner()
    pruned = 0
    prune_passes = 0
    hits: List[int] = []
    drift_sum = 0.0
    activity_sum = 0.0
    silence = 0
    absence_intensity = 0.0

    start = time.perf_counter()
    for payload in trace:
        if payload is None:
            silence += 1
            absence_intensity = min(1.0, absence_intensity + 0.2)
            stim = C.Stimulus(origin="aion", modality="internal", payload="I exist!",
                              intensity=absence_intensity, is_absence=True)
        else:
            silence = 0
            absence_intensity = 0.0
            stim = C.Stimulus(origin="world", modality="sensor", payload=payload,
                              intensity=0.6)
        result = bridge.process(stim)
        m = bridge.substrate.metrics()
        drift_sum += m.drift
        activity_sum += m.activity_rate
        if payload is not None:
            hit = 1 if result["suggested_action"] == WORLD[payload] else 0
            hits.append(hit)
            bridge.react(C.Reaction(valence=1.0 if hit else -1.0))
        # Periodic synthesis pass, identical cadence for every substrate.
        if bridge.telemetry.steps % 100 == 0:
            report = pruner.prune(bridge.readout, bridge.habit)
            pruned += report.total_removed
            prune_passes += 1
    duration = time.perf_counter() - start

    n = len(trace)
    early = hits[: max(1, len(hits) // 5)]
    late = hits[-max(1, len(hits) // 5):]
    metrics = bridge.substrate.metrics()
    avg_activity = activity_sum / n if n else 0.0
    updates_per_sec = n / duration if duration > 0 else 0.0
    avg_active_units = avg_activity * bridge.substrate.state_size

    return {
        "state_size": bridge.substrate.state_size,
        "activity_rate": avg_activity,
        "state_drift_mean": drift_sum / n if n else 0.0,
        "early_accuracy": sum(early) / len(early),
        "late_accuracy": sum(late) / len(late),
        "adaptation_gain": (sum(late) / len(late)) - (sum(early) / len(early)),
        "recent_prediction_error": bridge.telemetry.recent_prediction_error,
        "habit_reinforcements": bridge.telemetry.readout_updates,
        "habit_pathways": len(bridge.habit.weights),
        "pruning_passes": prune_passes,
        "pruned_pathways": pruned,
        "spike_rate": metrics.spike_rate if metrics.spike_rate is not None else 0.0,
        "memory_trace_length": len(bridge.trace),
        "duration_seconds": duration,
        "updates_per_second": updates_per_sec,
        "energy_proxy": energy_proxy(updates_per_sec, avg_active_units),
    }


def run_substrate_comparison(
    steps: int = 300,
    seed: int = 7,
    substrates: Optional[List[str]] = None,
    state_dir: Optional[str] = None,
    verbose: bool = False,
) -> SubstrateComparisonResult:
    """Run the bounded comparison and return per-substrate metrics + table."""
    names = substrates or list(DEFAULT_SUBSTRATES)
    for name in names:
        if name not in SubstrateRegistry.list_substrates():
            raise ValueError(f"unknown substrate {name!r}; "
                             f"available: {SubstrateRegistry.list_substrates()}")
    trace = _event_trace(steps)
    report = ComparisonReport()
    rows: Dict[str, Dict[str, Any]] = {}
    for name in names:
        row = _run_one(name, trace, seed)
        rows[name] = row
        report.add(name, **row)

    result = SubstrateComparisonResult(report=report, steps=steps, seed=seed, rows=rows)

    if state_dir is not None:
        pm = PersistenceManager(state_dir)
        pm._write_json(pm.state_dir / "substrate_comparison.json", result.to_dict())

    if verbose:
        print("=" * 72)
        print("Solaris-AI-NN -- substrate comparison "
              f"({steps} steps, seed {seed}, same event trace)")
        print("=" * 72)
        print(result.table())
        print("-" * 72)
        print("All substrates consumed the identical Solaris signal trace; only the")
        print("nervous substrate differs. Energy proxy = updates/sec per average")
        print("active unit (a crude indicator, not a power measurement).")
        if state_dir is not None:
            print(f"report saved under: {state_dir}/substrate_comparison.json")
    return result


def main() -> None:
    run_substrate_comparison(verbose=True)


if __name__ == "__main__":
    main()
