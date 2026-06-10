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
from ..substrates.base import BaseSubstrate
from ..substrates.esn_substrate import EchoStateSubstrate
from ..substrates.registry import SubstrateRegistry
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
        substrate_name: Which substrate to build (``esn`` | ``liquid_state`` |
            ``spiking_recurrent``). Default stays ``esn`` for compatibility.
        substrate_config: Optional config dict (state_size, params...) for the
            named substrate.
        substrate: An already-built :class:`BaseSubstrate` to drive instead.
        exploration: Epsilon for epsilon-greedy tendency selection.
        seed: Seed for the substrate and the exploration RNG.
    """

    action_labels: List[str]
    encoder: EventEncoder = field(default_factory=EventEncoder)
    esn: Optional[ESN] = None
    readout: Optional[LinearReadout] = None
    substrate_name: str = "esn"
    substrate_config: Optional[Dict[str, Any]] = None
    substrate: Optional[BaseSubstrate] = None
    learner: DeltaRuleLearner = field(default_factory=DeltaRuleLearner)
    habit: HabitReinforcement = field(default_factory=HabitReinforcement)
    modulator: LogosModulator = field(default_factory=LogosModulator)
    adapter: SolarisSignalAdapter = field(default_factory=SolarisSignalAdapter)
    telemetry: Telemetry = field(default_factory=Telemetry)
    trace: TraceMemory = field(default_factory=TraceMemory)
    exploration: float = 0.1
    stabilization: float = 0.0
    confidence_threshold: float = 0.0
    suggestion_threshold: float = 0.0
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

        # Build the substrate: an explicit instance wins; a legacy explicit ESN
        # is wrapped; otherwise the registry creates the named substrate.
        if self.substrate is None:
            if self.esn is not None:
                self.substrate = EchoStateSubstrate.from_esn(self.esn)
            else:
                cfg = dict(self.substrate_config or {})
                cfg.pop("input_size", None)
                self.substrate = SubstrateRegistry.create(
                    self.substrate_name,
                    input_size=self.encoder.dim,
                    state_size=cfg.pop("state_size", None),
                    seed=int(cfg.pop("seed", self.seed)),
                    **cfg,
                )
        self.substrate_name = self.substrate.name
        # Keep ``bridge.esn`` alive on the ESN path (back-compat: runner,
        # observer, plasticity targets, and older experiments all use it).
        self.esn = self.substrate.esn if isinstance(self.substrate, EchoStateSubstrate) else None

        if self.substrate.input_size != self.encoder.dim:
            raise ValueError("substrate input_size must match encoder.dim")
        if self.readout is None:
            self.readout = LinearReadout(
                n_features=self.substrate.state_size + 1,  # state + bias term
                n_outputs=len(self.action_labels),
                labels=list(self.action_labels),
            )

    # -- substrate access -----------------------------------------------------

    def _features(self) -> List[float]:
        """Substrate state plus a constant bias feature (what the readout sees)."""
        return [float(x) for x in self.substrate.get_state()] + [1.0]

    def substrate_state_norm(self) -> float:
        """L2 norm of the current substrate state."""
        return norm([float(x) for x in self.substrate.get_state()])

    def attach_substrate(self, substrate: BaseSubstrate) -> None:
        """Swap in a different substrate (used by the explicit SubstrateSwitcher).

        If the new substrate's state size differs, the readout is rebuilt (its
        learned weights cannot be meaningfully mapped across dimensions); same
        size keeps the readout. Pending reaction context is cleared either way
        so feedback never lands on mismatched features.
        """
        if substrate.input_size != self.encoder.dim:
            raise ValueError("substrate input_size must match encoder.dim")
        self.substrate = substrate
        self.substrate_name = substrate.name
        self.esn = substrate.esn if isinstance(substrate, EchoStateSubstrate) else None
        needed = substrate.state_size + 1
        if self.readout.n_features != needed:
            self.readout = LinearReadout(
                n_features=needed,
                n_outputs=len(self.action_labels),
                labels=list(self.action_labels),
            )
        self._last_features = None
        self._last_chosen = None

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

        # Encode -> modulate (Logos) -> advance the substrate.
        vector = self.encoder.encode(signal, heartbeat=True)
        vector = self.modulator.apply_to_input(vector, self._logos)
        self.substrate.update(vector)
        self.telemetry.reservoir_update()
        features = self._features()

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
            "substrate": self.substrate.name,
            "reservoir_energy": self.substrate_state_norm(),
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

    # -- integration helpers (Solaris sidecar) -------------------------------

    def process_raw_solaris_signal(self, raw_signal: Any) -> Dict[str, Any]:
        """Process a raw Solaris_Ai signal (object/dict); alias of :meth:`process`.

        Exists as an explicit, named seam for the integration layer; the
        adapter inside :meth:`process` already accepts raw Solaris shapes.
        """
        return self.process(raw_signal)

    def last_suggestion(self) -> Optional[Dict[str, Any]]:
        """The most recent suggestion as a plain dict (or ``None``)."""
        if self._last_action is None or self._last_desire is None:
            return None
        return {
            "action": self._last_action.name,
            "desire": self._last_desire.proposal,
            "confidence": self._last_desire.confidence,
            "motivation": self._last_desire.motivation,
            "committed": False,  # the bridge never commits; suggestions only
        }

    def suggestion_confidence(self) -> float:
        """Confidence of the most recent suggestion (0.0 before any signal)."""
        return self._last_desire.confidence if self._last_desire else 0.0

    def substrate_summary(self) -> Dict[str, Any]:
        """Compact substrate description for suggestions / integration status."""
        m = self.substrate.metrics()
        return {
            "name": self.substrate.name,
            "state_size": self.substrate.state_size,
            "state_norm": m.state_norm,
            "activity_rate": m.activity_rate,
            "spike_rate": m.spike_rate,
            "updates": m.updates,
        }

    def snapshot(self) -> Dict[str, Any]:
        """Return a JSON-friendly view of the bridge's current state."""
        logos = None
        if self._logos is not None:
            logos = {
                "division": self._logos.division,
                "union": self._logos.union,
                "fracture": self._logos.fracture,
            }
        substrate_metrics = self.substrate.metrics()
        return {
            "steps": self._steps,
            "substrate_type": self.substrate.name,
            "substrate_config": self.substrate.config.to_dict(),
            "substrate_metrics": substrate_metrics.to_dict(),
            "substrate_state_norm": substrate_metrics.state_norm,
            "substrate_activity_rate": substrate_metrics.activity_rate,
            "substrate_switches": list(getattr(self, "substrate_switches", [])),
            "reservoir_energy": self.substrate_state_norm(),
            "reservoir_state_sample": [float(x) for x in self.substrate.get_state()[:5]],
            "logos": logos,
            "habit_pathways": len(self.habit.weights),
            "habit_total_weight": round(self.habit.total_weight(), 6),
            "last_suggested_action": self._last_action.name if self._last_action else None,
            "last_confidence": round(self._last_desire.confidence, 6) if self._last_desire else None,
            "exploration": self.exploration,
            "telemetry": self.telemetry.report(),
        }
