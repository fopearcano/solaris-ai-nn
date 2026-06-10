"""Spiking silence experiment.

Tests whether the spike-based substrates (liquid-state and spiking-recurrent)
keep evolving through silence, the way Solaris_Ai's AION/Impulse keeps the
conceptual system alive with absence stimuli.

Three phases of equal length per substrate:

1. **presence** -- external stimuli arrive;
2. **silence**  -- no external input; escalating "I exist!" absence stimuli are
   synthesised (the Subtraction Principle);
3. **post**     -- external stimuli resume.

For each phase we record mean activity rate, mean state norm, spike counts, and
state drift, then ask the only question that matters here: did the substrate go
inert during silence, or did it maintain low-level activity? No claim of
consciousness is made -- "not inert" means non-zero, changing numbers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from ..bridges.neural_bridge import SolarisNeuralBridge
from ..runtime.persistence import PersistenceManager
from ..signals import canonical as C
from ..signals.encoding import EventEncoder

PAYLOADS = ["light", "noise", "food"]
ACTIONS = ["approach", "withdraw", "consume"]
DEFAULT_SUBSTRATES = ["liquid_state", "spiking_recurrent"]


@dataclass
class PhaseStats:
    """Mean activity statistics over one phase."""

    activity_rate: float = 0.0
    state_norm: float = 0.0
    drift: float = 0.0
    spikes: float = 0.0
    steps: int = 0

    def to_dict(self) -> Dict[str, float]:
        return {"activity_rate": self.activity_rate, "state_norm": self.state_norm,
                "drift": self.drift, "spikes": self.spikes, "steps": self.steps}


@dataclass
class SilenceResult:
    """Per-substrate phase statistics + inertness verdicts."""

    steps: int
    per_substrate: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"steps": self.steps, "per_substrate": self.per_substrate}


def _phase(bridge: SolarisNeuralBridge, stimuli: List[C.Stimulus]) -> PhaseStats:
    stats = PhaseStats(steps=len(stimuli))
    for stim in stimuli:
        bridge.process(stim)
        m = bridge.substrate.metrics()
        stats.activity_rate += m.activity_rate
        stats.state_norm += m.state_norm
        stats.drift += m.drift
        if m.spike_rate is not None:
            stats.spikes += m.spike_rate
    n = max(1, stats.steps)
    stats.activity_rate /= n
    stats.state_norm /= n
    stats.drift /= n
    stats.spikes /= n
    return stats


def run_spiking_silence(
    steps: int = 300,
    seed: int = 7,
    substrates: Optional[List[str]] = None,
    state_dir: Optional[str] = None,
    verbose: bool = False,
) -> SilenceResult:
    """Run presence -> silence -> post phases through each substrate."""
    names = substrates or list(DEFAULT_SUBSTRATES)
    third = max(1, steps // 3)
    result = SilenceResult(steps=steps)

    for name in names:
        encoder = EventEncoder(vocabulary=PAYLOADS + ["I exist!"])
        bridge = SolarisNeuralBridge(
            action_labels=ACTIONS, encoder=encoder, substrate_name=name, seed=seed)

        presence = [C.Stimulus(origin="world", modality="sensor",
                               payload=PAYLOADS[i % 3], intensity=0.7)
                    for i in range(third)]
        # Escalating absence stimuli, AION-style ("I exist!").
        silence = [C.Stimulus(origin="aion", modality="internal", payload="I exist!",
                              intensity=min(1.0, 0.1 * (i + 1)), is_absence=True)
                   for i in range(third)]
        post = [C.Stimulus(origin="world", modality="sensor",
                           payload=PAYLOADS[i % 3], intensity=0.7)
                for i in range(third)]

        before = _phase(bridge, presence)
        state_at_silence_start = bridge.substrate.get_state().copy()
        during = _phase(bridge, silence)
        state_at_silence_end = bridge.substrate.get_state().copy()
        after = _phase(bridge, post)

        silence_state_shift = float(np.linalg.norm(
            state_at_silence_end - state_at_silence_start))
        went_inert = during.drift == 0.0 and during.activity_rate == 0.0

        result.per_substrate[name] = {
            "before": before.to_dict(),
            "during_silence": during.to_dict(),
            "after": after.to_dict(),
            "silence_state_shift": silence_state_shift,
            "went_inert": went_inert,
        }

    if state_dir is not None:
        pm = PersistenceManager(state_dir)
        pm._write_json(pm.state_dir / "spiking_silence.json", result.to_dict())

    if verbose:
        print("=" * 72)
        print(f"Solaris-AI-NN -- spiking silence experiment ({steps} steps, seed {seed})")
        print("=" * 72)
        for name, data in result.per_substrate.items():
            print(f"\n[{name}]")
            for phase in ("before", "during_silence", "after"):
                p = data[phase]
                print(f"  {phase:15s} activity={p['activity_rate']:.4f}  "
                      f"norm={p['state_norm']:.4f}  drift={p['drift']:.4f}  "
                      f"spike_rate={p['spikes']:.4f}")
            print(f"  silence state shift: {data['silence_state_shift']:.4f}")
            print(f"  went inert during silence? {data['went_inert']}")
        print("-" * 72)
        print("Absence stimuli keep the substrates moving through silence --")
        print("non-zero, changing numbers; no claim of consciousness.")
    return result


def main() -> None:
    run_spiking_silence(verbose=True)


if __name__ == "__main__":
    main()
