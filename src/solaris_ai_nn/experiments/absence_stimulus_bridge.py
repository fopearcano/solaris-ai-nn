"""Absence-stimulus bridge experiment.

This experiment exercises the :class:`SolarisNeuralBridge` against the behaviour
of Solaris_Ai's AION/Impulse core (``core/aion_impulse.py``): the system must
never go inert. It runs in two phases:

1. **Presence.** External stimuli arrive for a while; the bridge processes them
   and learns weakly from `+1/-1` reactions.
2. **Silence.** No external input arrives. Mimicking AION's Subtraction
   Principle, we synthesise escalating *absence* stimuli ("I exist!") and feed
   them through the bridge. The reservoir state keeps evolving through silence --
   the substrate stays alive without external drive.

The result quantifies that the reservoir does **not** freeze during silence
(non-zero, changing state energy; non-zero state drift across the silent phase).
No claim of consciousness -- only that an event-driven substrate keeps moving.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from ..bridges.neural_bridge import SolarisNeuralBridge
from ..signals import canonical as C
from ..signals.encoding import EventEncoder
from ..utils.math import norm

# Reuse the tiny world from the minimal experiment for the presence phase.
WORLD: Dict[str, str] = {"light": "approach", "noise": "withdraw", "food": "consume"}
ACTIONS: List[str] = ["approach", "withdraw", "consume"]


@dataclass
class AbsenceResult:
    """Outcome of the absence-stimulus bridge experiment."""

    presence_events: int
    silence_events: int
    energy_presence_mean: float
    energy_silence_mean: float
    silence_state_drift: float
    went_inert: bool
    energies_silence: List[float] = field(default_factory=list)
    telemetry_report: Dict[str, object] = field(default_factory=dict)


def run_absence_stimulus_bridge(
    presence_steps: int = 45,
    silence_steps: int = 45,
    seed: int = 7,
    verbose: bool = False,
) -> AbsenceResult:
    """Run the presence -> silence experiment through the neural bridge.

    Args:
        presence_steps: External stimuli to present in phase 1.
        silence_steps: Absence stimuli to synthesise in phase 2.
        seed: Determinism seed.
        verbose: Print a human-readable summary.
    """
    encoder = EventEncoder(vocabulary=list(WORLD.keys()) + ["I exist!"])
    bridge = SolarisNeuralBridge(action_labels=ACTIONS, encoder=encoder, seed=seed)

    payloads = list(WORLD.keys())
    energies_presence: List[float] = []
    energies_silence: List[float] = []

    # --- Phase 1: presence (external stimuli + reaction feedback) ---
    for i in range(presence_steps):
        payload = payloads[i % len(payloads)]
        stimulus = C.Stimulus(
            origin="world", modality="sensor", payload=payload, intensity=0.6
        )
        result = bridge.process(stimulus)
        energies_presence.append(result["reservoir_energy"])
        valence = 1.0 if result["suggested_action"] == WORLD[payload] else -1.0
        bridge.react(C.Reaction(valence=valence))

    # --- Phase 2: silence (synthesised absence stimuli, no external reaction) ---
    state_before = bridge.esn.state
    absence_intensity = 0.0
    for _ in range(silence_steps):
        # Intensity escalates as silence persists, then would reset on input --
        # exactly AION's "I exist!" absence escalation.
        absence_intensity = min(1.0, absence_intensity + 0.1)
        absence = C.Stimulus(
            origin="aion",
            modality="internal",
            payload="I exist!",
            intensity=absence_intensity,
            is_absence=True,
        )
        result = bridge.process(absence)
        energies_silence.append(result["reservoir_energy"])
    state_after = bridge.esn.state

    bridge.telemetry.finish()

    silence_drift = norm([a - b for a, b in zip(state_after, state_before)])
    energy_silence_mean = sum(energies_silence) / len(energies_silence) if energies_silence else 0.0
    energy_presence_mean = (
        sum(energies_presence) / len(energies_presence) if energies_presence else 0.0
    )
    # "Inert" = the substrate stopped moving during silence (no energy, no drift).
    went_inert = energy_silence_mean < 1e-9 and silence_drift < 1e-9

    result = AbsenceResult(
        presence_events=presence_steps,
        silence_events=silence_steps,
        energy_presence_mean=energy_presence_mean,
        energy_silence_mean=energy_silence_mean,
        silence_state_drift=silence_drift,
        went_inert=went_inert,
        energies_silence=energies_silence,
        telemetry_report=bridge.telemetry.report(),
    )

    if verbose:
        print("=" * 60)
        print("Solaris-AI-NN -- absence-stimulus bridge experiment")
        print("=" * 60)
        print(bridge.telemetry)
        print("-" * 60)
        print(f"presence events: {result.presence_events} "
              f"(mean reservoir energy {result.energy_presence_mean:.4f})")
        print(f"silence  events: {result.silence_events} "
              f"(mean reservoir energy {result.energy_silence_mean:.4f})")
        print(f"reservoir state drift across silence: {result.silence_state_drift:.4f}")
        print(f"went inert during silence? {result.went_inert}")
        print("-" * 60)
        print("The reservoir keeps evolving during silence via synthesised")
        print("absence stimuli -- the substrate does not go inert. This mirrors")
        print("AION/Impulse, with no claim that the system is conscious.")

    return result


def main() -> None:
    """Console / example entry point."""
    run_absence_stimulus_bridge(verbose=True)


if __name__ == "__main__":
    main()
