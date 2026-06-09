"""SolarisNeuralBridge -- the compatibility layer to Solaris_Ai's signal ecology.

The bridge is the integration point between Solaris_Ai-style signals and the
low-compute neural substrate. Per signal it:

1. **adapts** a raw Solaris-like signal (dataclass / dict / object) into a
   canonical NN signal (:class:`SolarisSignalAdapter`);
2. **encodes** it into a numeric vector (:class:`EventEncoder`);
3. **modulates** that vector by the current :class:`LogosTension`
   (:class:`LogosModulator`);
4. **updates** the continuous reservoir state (:class:`ESN`);
5. **produces** an Action/Desire *tendency* from the linear readout (lightly
   biased by Habit, with epsilon-greedy exploration);
6. on :class:`Reaction` feedback, **learns** online (NLMS) and reinforces Habit;
7. **records** telemetry and a memory trace, and **exposes** its state.

Crucially, the bridge does **not** decide for Solaris_Ai. It emits *suggestions /
tendencies*; a Solaris_Ai I/O module or future integration layer decides whether
to commit them. This keeps the NN layer a substrate *beside/underneath* the
signal ecology, never a replacement for it.

It does not import ``solaris-ai`` -- all coupling is via duck-typed adaptation.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..memory.trace_memory import TraceMemory
from ..plasticity.habit_reinforcement import HabitReinforcement
from ..reservoir.esn import ESN
from ..reservoir.modulation import LogosModulator
from ..reservoir.online_learning import DeltaRuleLearner
from ..reservoir.readout import LinearReadout
from ..runtime.telemetry import Telemetry
from ..signals import canonical as C
from ..signals.adapters import SolarisSignalAdapter
from ..signals.encoding import EventEncoder
from ..utils.logging import get_logger
from ..utils.math import clamp, norm

logger = get_logger(__name__)


@dataclass
class SolarisNeuralBridge:
    """Adaptive neural substrate that consumes Solaris-style signals.

    Args:
        action_labels: The discrete action tendencies the bridge can suggest.
        encoder / esn / readout / learner / habit / modulator / adapter:
            substrate components; sensible defaults are built if omitted.
        exploration: Epsilon for epsilon-greedy tendency selection.
        seed: Seed for the default ESN and the exploration RNG.
    """

    action_labels: List[str]
    encoder: EventEncoder = field(default_factory=EventEncoder)
    esn: Optional[ESN] = None
    readout: Optional[LinearReadout] = None
    learner: DeltaRuleLearner = field(default_factory=DeltaRuleLearner)
    habit: HabitReinforcement = field(default_factory=HabitReinforcement)
    modulator: LogosModulator = field(default_factory=LogosModulator)
    adapter: SolarisSignalAdapter = field(default_factory=SolarisSignalAdapter)
    telemetry: Telemetry = field(default_factory=Telemetry)
    trace: TraceMemory = field(default_factory=TraceMemory)
    exploration: float = 0.1
    seed: int = 0

    _logos: Optional[C.LogosTension] = field(default=None, init=False, repr=False)
    _steps: int = field(default=0, init=False)
    _last_features: Optional[List[float]] = field(default=None, init=False, repr=False)
    _last_chosen: Optional[int] = field(default=None, init=False, repr=False)
    _last_pattern_key: Optional[str] = field(default=None, init=False, repr=False)
    _last_action: Optional[C.Action] = field(default=None, init=False, repr=False)
    _last_desire: Optional[C.Desire] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.action_labels:
            raise ValueError("at least one action label is required")
        self._rng = random.Random(self.seed)
        if self.esn is None:
            self.esn = ESN(n_inputs=self.encoder.dim, seed=self.seed)
        if self.esn.n_inputs != self.encoder.dim:
            raise ValueError("ESN n_inputs must match encoder.dim")
        if self.readout is None:
            self.readout = LinearReadout(
                n_features=self.esn.feature_size(),
                n_outputs=len(self.action_labels),
                labels=list(self.action_labels),
            )

    # -- processing ---------------------------------------------------------

    def process(self, raw_signal: Any) -> Dict[str, Any]:
        """Process one raw Solaris-like signal; return a tendency dict.

        The returned dict is a *suggestion*, not a decision. Keys include the
        adapted signal kind, the suggested action/desire, confidence, per-action
        scores, current reservoir energy, and the active Logos fracture.
        """
        signal = self.adapter.to_nn_signal(raw_signal)
        self._steps += 1
        self.telemetry.tick()
        self.telemetry.event()

        # LogosTension signals update the modulation state for subsequent events.
        if isinstance(signal, C.LogosTension):
            self._logos = signal

        # Encode -> modulate (Logos) -> advance the reservoir.
        vector = self.encoder.encode(signal, heartbeat=True)
        vector = self.modulator.apply_to_input(vector, self._logos)
        self.esn.update(vector)
        self.telemetry.reservoir_update()
        features = self.esn.features()

        # Form a tendency: readout score + light habit bias, epsilon-greedy.
        pattern_key = self.encoder.pattern_key(signal)
        bias = self.habit.bias_vector(pattern_key, self.action_labels)
        scores = self.readout.predict(features)
        greedy = self.readout.argmax(features, bias=bias)
        if len(self.action_labels) > 1 and self._rng.random() < self.exploration:
            chosen = self._rng.randrange(len(self.action_labels))
        else:
            chosen = greedy
        label = self.action_labels[chosen]

        base_confidence = clamp((scores[chosen] + 1.0) / 2.0, 0.0, 1.0)
        confidence = self.modulator.apply_to_readout_confidence(base_confidence, self._logos)

        desire = self.adapter.from_nn_desire(
            proposal=label, motivation=abs(scores[chosen]), confidence=confidence
        )
        action = self.adapter.from_nn_action(name=label, payload=pattern_key)

        # Stash context for react(); expose the latest suggestions.
        self._last_features = features
        self._last_chosen = chosen
        self._last_pattern_key = pattern_key
        self._last_action = action
        self._last_desire = desire

        self.trace.record_event(
            self._steps,
            signal.kind,
            payload=str(getattr(signal, "payload", None)),
            is_absence=bool(getattr(signal, "is_absence", False)),
        )
        self.trace.record_action(self._steps, label, confidence=round(confidence, 4))
        self.telemetry.set_trace_length(len(self.trace))

        return {
            "step": self._steps,
            "input_type": signal.kind,
            "is_absence": bool(getattr(signal, "is_absence", False)),
            "pattern_key": pattern_key,
            "suggested_action": label,
            "suggested_desire": label,
            "confidence": confidence,
            "explored": chosen != greedy,
            "scores": dict(zip(self.action_labels, scores)),
            "reservoir_energy": norm(self.esn.state),
            "logos_fracture": self._logos.fracture if self._logos is not None else 0.0,
        }

    def process_many(self, raw_signals: List[Any]) -> List[Dict[str, Any]]:
        """Process a sequence of raw signals, returning one tendency dict each."""
        return [self.process(s) for s in raw_signals]

    # -- feedback -----------------------------------------------------------

    def react(self, reaction: Any) -> None:
        """Apply Reaction feedback for the most recent suggestion.

        Updates the readout online (NLMS) and reinforces the habit pathway.
        Safe to call with a :class:`Reaction`, a dict, or an object-like signal;
        a no-op if nothing has been processed yet.
        """
        if self._last_features is None or self._last_chosen is None:
            return
        signal = self.adapter.to_nn_signal(reaction)
        valence = float(getattr(signal, "valence", 0.0) or 0.0)

        error = self.learner.update(
            self.readout, self._last_features, self._last_chosen, valence
        )
        self.telemetry.readout_update(error)
        self.habit.observe(
            self._last_pattern_key, self.action_labels[self._last_chosen], valence
        )
        self.telemetry.update_habit(self.habit.total_weight())
        self.trace.record_reaction(self._steps, valence, error=round(error, 4))
        self.telemetry.set_trace_length(len(self.trace))

    # -- suggestions / inspection ------------------------------------------

    def suggest_action(self) -> Optional[C.Action]:
        """The most recent suggested Action (or ``None`` before any signal)."""
        return self._last_action

    def suggest_desire(self) -> Optional[C.Desire]:
        """The most recent suggested Desire (or ``None`` before any signal)."""
        return self._last_desire

    def snapshot(self) -> Dict[str, Any]:
        """Return a JSON-friendly view of the bridge's current state."""
        logos = None
        if self._logos is not None:
            logos = {
                "division": self._logos.division,
                "union": self._logos.union,
                "fracture": self._logos.fracture,
            }
        return {
            "steps": self._steps,
            "reservoir_energy": norm(self.esn.state),
            "reservoir_state_sample": self.esn.state[:5],
            "logos": logos,
            "habit_pathways": len(self.habit.weights),
            "habit_total_weight": round(self.habit.total_weight(), 6),
            "last_suggested_action": self._last_action.name if self._last_action else None,
            "last_confidence": round(self._last_desire.confidence, 6) if self._last_desire else None,
            "exploration": self.exploration,
            "telemetry": self.telemetry.report(),
        }
