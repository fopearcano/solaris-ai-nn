"""The adaptive event loop -- Solaris-AI-NN's beating heart.

This is the mechanism that ties the substrate together. It preserves the
Solaris_Ai conceptual spine on every step::

    Stimulus -> Push -> Desire -> Action   (then a Reaction feeds back)

Per step the loop:

1. produces a heartbeat tick (continuity), echoing AION/Impulse;
2. takes the next external Stimulus, or -- after silence -- synthesises an
   *absence* Stimulus ("I exist!"), the Subtraction Principle;
3. encodes the event to a vector and advances the reservoir;
4. forms a Desire (the readout's preferred action + confidence), lightly biased
   by Habit, and commits it as an Action;
5. on Reaction feedback, updates the readout online and reinforces the habit;
6. periodically runs synthesis-through-subtraction and snapshots memory;
7. records telemetry throughout.

There is nothing conscious here. It is an adaptive event loop with cheap,
continuous, observable learning -- a *continuous cognition prototype*.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional, Protocol, runtime_checkable

from ..memory.state_memory import StateMemory
from ..memory.trace_memory import TraceMemory
from ..plasticity.drift import DriftMonitor
from ..plasticity.habit_reinforcement import HabitReinforcement
from ..plasticity.synthesis_pruning import SynthesisPruner
from ..reservoir.esn import ESN
from ..reservoir.online_learning import DeltaRuleLearner
from ..reservoir.readout import LinearReadout
from ..signals import canonical as C
from ..signals.encoding import EventEncoder
from ..utils.logging import get_logger
from .telemetry import Telemetry

logger = get_logger(__name__)


@runtime_checkable
class Environment(Protocol):
    """Optional driver supplying stimuli and reactions to the loop.

    Experiments implement this to close the feedback loop. Both methods may
    return ``None`` (no stimulus this step / no reaction to the action).
    """

    def next_stimulus(self, step: int) -> Optional[C.Stimulus]:
        ...

    def react(self, stimulus: Optional[C.Stimulus], action: C.Action) -> Optional[float]:
        ...


@dataclass
class StepResult:
    """What one loop step produced (handy for tests and inspection)."""

    step: int
    stimulus: Optional[C.Stimulus]
    desire: C.Desire
    action: C.Action
    chosen_index: int
    is_absence: bool
    reaction_valence: Optional[float] = None
    prediction_error: Optional[float] = None


@dataclass
class ExperimentLoop:
    """Composes substrate + plasticity + memory into one adaptive loop.

    Args:
        action_labels: The discrete actions the loop can choose between.
        encoder: Event -> vector encoder (defaults to a fresh EventEncoder).
        esn / readout / learner / habit / synthesis: substrate components;
            sensible defaults are built if omitted.
        silence_steps: Steps of external silence before an absence Stimulus is
            synthesised (the Subtraction Principle).
        prune_every: Run a synthesis pass every N steps (0 disables).
        snapshot_every: Reservoir-state snapshot interval (steps).
        exploration: Epsilon for epsilon-greedy action selection. A greedy
            readout never tries actions it has not yet valued, so a little
            exploration is required for the substrate to discover better
            pathways. Decays toward 0 as confidence in habits grows.
        seed: Seed for the default ESN and the exploration RNG.
    """

    action_labels: List[str]
    encoder: EventEncoder = field(default_factory=EventEncoder)
    esn: Optional[ESN] = None
    readout: Optional[LinearReadout] = None
    learner: DeltaRuleLearner = field(default_factory=DeltaRuleLearner)
    habit: HabitReinforcement = field(default_factory=HabitReinforcement)
    synthesis: SynthesisPruner = field(default_factory=SynthesisPruner)
    drift: DriftMonitor = field(default_factory=DriftMonitor)
    trace: TraceMemory = field(default_factory=TraceMemory)
    state_memory: StateMemory = field(default_factory=StateMemory)
    telemetry: Telemetry = field(default_factory=Telemetry)

    silence_steps: int = 10
    prune_every: int = 200
    snapshot_every: int = 25
    exploration: float = 0.1
    seed: int = 0

    _step: int = 0
    _pending: List[C.Stimulus] = field(default_factory=list)
    _steps_since_stimulus: int = 0
    _absence_intensity: float = 0.0

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
        # Keep state-memory interval in sync with the loop's configured cadence.
        self.state_memory.interval = self.snapshot_every

    # -- inputs -------------------------------------------------------------

    def inject(self, stimulus: C.Stimulus) -> None:
        """Queue an external stimulus to be consumed on the next step."""
        self._pending.append(stimulus)

    def _heartbeat(self) -> C.Push:
        """Emit the low-intensity continuity Push (echoes AION/Impulse)."""
        self.telemetry.heartbeat()
        return C.Push(origin="aion", intensity=0.05, direction="continuity")

    def _absence_stimulus(self) -> C.Stimulus:
        """Synthesise an escalating absence Stimulus after prolonged silence."""
        self._absence_intensity = min(1.0, self._absence_intensity + 0.2)
        return C.Stimulus(
            origin="aion",
            modality="internal",
            payload="I exist!",
            intensity=self._absence_intensity,
            is_absence=True,
        )

    # -- one step -----------------------------------------------------------

    def step(self, environment: Optional[Environment] = None) -> StepResult:
        """Run exactly one loop step. Returns a :class:`StepResult`."""
        self._step += 1
        self.telemetry.tick()
        self._heartbeat()  # continuity / heartbeat tick

        # 1. Choose the event driving this step.
        stimulus = self._next_stimulus(environment)
        is_absence = False
        if stimulus is None:
            self._steps_since_stimulus += 1
            if self._steps_since_stimulus >= self.silence_steps:
                stimulus = self._absence_stimulus()
                is_absence = True
                self._steps_since_stimulus = 0
        else:
            self._steps_since_stimulus = 0
            self._absence_intensity = 0.0

        # The event fed to the substrate: the stimulus, or a continuity Push.
        event: C.Signal = stimulus if stimulus is not None else self._heartbeat_event()
        pattern_key = self.encoder.pattern_key(event)
        self.telemetry.event()

        # 2. Encode and advance the reservoir.
        features_in = self.encoder.encode(event, heartbeat=True)
        self.esn.update(features_in)
        self.telemetry.reservoir_update()
        features = self.esn.features()

        # 3. Form a Desire (preferred action + confidence), biased by Habit.
        #    Epsilon-greedy: mostly exploit the readout's preference, but
        #    occasionally explore so unvalued actions can be discovered.
        bias = self.habit.bias_vector(pattern_key, self.action_labels)
        scores = self.readout.predict(features)
        greedy = self.readout.argmax(features, bias=bias)
        if len(self.action_labels) > 1 and self._rng.random() < self.exploration:
            chosen = self._rng.randrange(len(self.action_labels))
        else:
            chosen = greedy
        label = self.action_labels[chosen]
        confidence = max(0.0, min(1.0, (scores[chosen] + 1.0) / 2.0))
        desire = C.Desire(
            origin="readout",
            proposal=label,
            motivation=abs(scores[chosen]),
            confidence=confidence,
        )

        # 4. Commit the Action.
        action = C.Action(origin="loop", name=label, payload=pattern_key)

        # Stash context needed for feedback().
        self._last_features = features
        self._last_chosen = chosen
        self._last_pattern_key = pattern_key

        self.trace.record_event(
            self._step, event.kind, payload=str(getattr(event, "payload", None)),
            is_absence=is_absence,
        )
        self.trace.record_action(self._step, label, confidence=round(confidence, 4))

        result = StepResult(
            step=self._step,
            stimulus=stimulus,
            desire=desire,
            action=action,
            chosen_index=chosen,
            is_absence=is_absence,
        )

        # 5. Reaction feedback (if the environment provides one).
        if environment is not None:
            valence = environment.react(stimulus, action)
            if valence is not None:
                error = self.feedback(valence)
                result.reaction_valence = valence
                result.prediction_error = error

        # 6. Periodic synthesis + memory snapshot.
        self._maybe_prune()
        self.state_memory.maybe_snapshot(self._step, self.esn.state)
        self.telemetry.set_trace_length(len(self.trace))

        return result

    def feedback(self, valence: float) -> float:
        """Apply Reaction feedback for the most recent action.

        Updates the readout online and reinforces the habit pathway. Returns the
        readout's signed prediction error.
        """
        error = self.learner.update(
            self.readout, self._last_features, self._last_chosen, valence
        )
        self.telemetry.readout_update(error)
        self.habit.observe(
            self._last_pattern_key, self.action_labels[self._last_chosen], valence
        )
        self.telemetry.update_habit(self.habit.total_weight())
        self.trace.record_reaction(self._step, valence, error=round(error, 4))
        self.drift.sample(self.readout)
        return error

    # -- multi-step drivers -------------------------------------------------

    def run(self, max_steps: int, environment: Optional[Environment] = None) -> Telemetry:
        """Run a bounded number of steps. ``max_steps`` is required (never infinite)."""
        if max_steps is None or max_steps <= 0:
            raise ValueError("max_steps must be a positive integer")
        for _ in range(max_steps):
            self.step(environment)
        self.telemetry.finish()
        logger.info("run complete: %s", self.telemetry.report())
        return self.telemetry

    def run_until(
        self,
        stop,
        environment: Optional[Environment] = None,
        safety_limit: int = 1_000_000,
    ) -> Telemetry:
        """Conceptual long/"infinite" mode with an explicit stop predicate.

        This is how the substrate's continuous, long-running nature is expressed
        without ever defaulting to a truly unbounded loop: callers must pass a
        ``stop(loop) -> bool`` predicate, and a hard ``safety_limit`` always
        backstops it.
        """
        steps = 0
        while not stop(self) and steps < safety_limit:
            self.step(environment)
            steps += 1
        self.telemetry.finish()
        return self.telemetry

    # -- helpers ------------------------------------------------------------

    def _next_stimulus(self, environment: Optional[Environment]) -> Optional[C.Stimulus]:
        if environment is not None:
            s = environment.next_stimulus(self._step)
            if s is not None:
                return s
        if self._pending:
            return self._pending.pop(0)
        return None

    def _heartbeat_event(self) -> C.Push:
        return C.Push(origin="aion", intensity=0.05, direction="continuity")

    def _maybe_prune(self) -> None:
        if self.prune_every > 0 and self._step % self.prune_every == 0:
            report = self.synthesis.prune(self.readout, self.habit)
            self.telemetry.pruning(report.total_removed)
            if report.total_removed:
                logger.info(report.summary())
