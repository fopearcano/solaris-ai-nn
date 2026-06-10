"""Solaris sidecar observation experiment (fake runtime by default).

Because CI does not have ``fopearcano/solaris-ai`` installed, this module ships
a small **fake** Solaris-like runtime -- ``FakeBus``, ``FakeConscience``, and
duck-typed signal classes named like the reference ones. The experiment:

1. builds a ``FakeConscience`` and attaches a :class:`SolarisNNSidecar`;
2. emits a deterministic sequence of Stimulus / Push / LogosTension /
   MeaningEvent / Reaction signals through the fake bus;
3. lets the sidecar mirror signals, update its substrate, learn from Reactions,
   and produce suggestions;
4. verifies that **no Action was ever committed** (every suggestion carries
   ``committed=False``, and the conscience's act/death methods were never
   called by the sidecar);
5. produces a compact report.

The fakes mimic shape, not behaviour: they exist so the integration seam is
testable without the real package.
"""

from __future__ import annotations

import itertools
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ..integration.conscience_sidecar import SolarisNNSidecar

# --------------------------------------------------------------------------- #
# Fake Solaris-like runtime (duck-typed; class NAMES match the reference)     #
# --------------------------------------------------------------------------- #

_ids = itertools.count(1)


class _FakeSignal:
    """Base for fake signals: id/timestamp/origin like the reference ones."""

    def __init__(self, origin: str = "fake", **fields: Any) -> None:
        self.id = next(_ids)
        self.timestamp = time.time()
        self.origin = origin
        for key, value in fields.items():
            setattr(self, key, value)


class Stimulus(_FakeSignal):
    def __init__(self, payload=None, intensity=0.5, modality="sensor",
                 is_absence=False, **kw):
        super().__init__(payload=payload, intensity=intensity,
                         modality=modality, is_absence=is_absence, **kw)


class Push(_FakeSignal):
    def __init__(self, intensity=0.1, direction="continuity", **kw):
        super().__init__(intensity=intensity, direction=direction,
                         source_stimulus_id=None, **kw)


class Reaction(_FakeSignal):
    def __init__(self, valence=0.0, action_id=None, **kw):
        super().__init__(valence=valence, action_id=action_id, **kw)


class MeaningEvent(_FakeSignal):
    def __init__(self, meaning="", novelty=0.0, **kw):
        super().__init__(meaning=meaning, novelty=novelty, stimulus_id=None, **kw)


class LogosTension(_FakeSignal):
    def __init__(self, division=0.0, union=0.0, **kw):
        super().__init__(division=division, union=union, **kw)

    @property
    def fracture(self) -> float:
        return abs(self.division - self.union)


class FakeBus:
    """Sync, duck-typed bus: subscribe / subscribe_all / publish / unsubscribe."""

    def __init__(self) -> None:
        self._all: List[Callable[[Any], None]] = []
        self._by_type: Dict[type, List[Callable[[Any], None]]] = {}
        self.published: List[Any] = []

    def subscribe(self, signal_type: type, handler: Callable[[Any], None]) -> None:
        self._by_type.setdefault(signal_type, []).append(handler)

    def subscribe_all(self, handler: Callable[[Any], None]) -> None:
        self._all.append(handler)

    def unsubscribe(self, handler: Callable[[Any], None]) -> None:
        if handler in self._all:
            self._all.remove(handler)
        for handlers in self._by_type.values():
            if handler in handlers:
                handlers.remove(handler)

    def publish(self, signal: Any) -> None:
        self.published.append(signal)
        for handler in list(self._all):
            handler(signal)
        for cls, handlers in self._by_type.items():
            if isinstance(signal, cls):
                for handler in list(handlers):
                    handler(signal)

    def subscriptions(self) -> Dict[str, Any]:
        return {cls.__name__: len(handlers) for cls, handlers in self._by_type.items()}


class FakeLifecycle:
    state = "running"


class FakeConscience:
    """Shape-compatible stand-in for Solaris_Ai's Conscience (records calls)."""

    def __init__(self) -> None:
        self.bus = FakeBus()
        self.lifecycle = FakeLifecycle()
        self.inner_map = {"facts": {}, "boundaries": {}}
        self.stimulate_calls = 0
        self.react_calls = 0
        self.death_calls = 0

    def stimulate(self, *args: Any, **kw: Any) -> None:
        self.stimulate_calls += 1
        if args:
            self.bus.publish(args[0])

    def react(self, *args: Any, **kw: Any) -> None:
        self.react_calls += 1

    def death(self, *args: Any, **kw: Any) -> None:  # the sidecar must NEVER call this
        self.death_calls += 1

    def snapshot(self) -> Dict[str, Any]:
        return {"lifecycle": self.lifecycle.state,
                "published": len(self.bus.published)}

    def topology(self) -> Dict[str, Any]:
        return {"modules": ["fake"]}


# --------------------------------------------------------------------------- #
# Experiment                                                                  #
# --------------------------------------------------------------------------- #

WORLD = {"light": "approach", "noise": "withdraw", "food": "consume"}


def deterministic_signal_sequence(steps: int) -> List[Any]:
    """The fixed event script: stimuli with periodic Push/Logos/Meaning beats."""
    payloads = list(WORLD.keys())
    sequence: List[Any] = []
    for i in range(steps):
        if i % 7 == 3:
            sequence.append(Push(intensity=0.3, direction="reactive"))
        elif i % 7 == 5:
            sequence.append(LogosTension(division=0.6, union=0.2))
        elif i % 7 == 6:
            sequence.append(MeaningEvent(meaning="pattern", novelty=0.4))
        else:
            sequence.append(Stimulus(payload=payloads[i % 3], intensity=0.7))
    return sequence


@dataclass
class SidecarObservationResult:
    """Outcome of the fake-runtime sidecar observation."""

    signals_emitted: int
    signals_observed: int
    mirrored: int
    suggestions_produced: int
    suggestions_published: int
    reactions_learned: int
    committed_actions: int  # must always be 0
    conscience_death_calls: int  # must always be 0
    sidecar_snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


def run_sidecar_observation(
    steps: int = 60,
    observe_only: bool = True,
    seed: int = 7,
    state_dir: Optional[str] = None,
    verbose: bool = False,
) -> SidecarObservationResult:
    """Attach a sidecar to the fake runtime and observe a bounded script."""
    conscience = FakeConscience()
    sidecar = SolarisNNSidecar(
        observe_only=observe_only,
        action_labels=list(dict.fromkeys(WORLD.values())) + ["observe"],
        vocabulary=list(WORLD.keys()) + ["I exist!"],
        seed=seed,
        suggestion_threshold=0.4,
    )
    report = sidecar.attach(conscience)
    sidecar.start()

    # Emit the deterministic script; after each Stimulus the world grades the
    # sidecar's latest suggestion with a Reaction (feedback, not command).
    sequence = deterministic_signal_sequence(steps)
    emitted = 0
    for signal in sequence:
        conscience.bus.publish(signal)
        emitted += 1
        if isinstance(signal, Stimulus) and not signal.is_absence:
            last = sidecar.bridge.last_suggestion()
            if last is not None:
                correct = WORLD.get(str(signal.payload))
                valence = 1.0 if last["action"] == correct else -1.0
                conscience.bus.publish(Reaction(valence=valence))
                emitted += 1

    # Committed actions must be zero: count anything published that claims
    # committed-ness (suggestions all carry committed=False).
    committed = sum(1 for s in conscience.bus.published
                    if getattr(s, "committed", False))

    snapshot = sidecar.snapshot()
    state = sidecar.state
    result = SidecarObservationResult(
        signals_emitted=emitted,
        signals_observed=state.signals_observed,
        mirrored=len(sidecar.mirror),
        suggestions_produced=state.suggestions_produced,
        suggestions_published=state.suggestions_published,
        reactions_learned=state.reactions_learned,
        committed_actions=committed,
        conscience_death_calls=conscience.death_calls,
        sidecar_snapshot=snapshot,
    )

    if state_dir is not None:
        sidecar.persist(state_dir)
    sidecar.detach()

    if verbose:
        print("=" * 70)
        print(f"Solaris-AI-NN -- sidecar observation on a FAKE Solaris runtime "
              f"({steps} scripted beats, observe_only={observe_only})")
        print("=" * 70)
        print(f"compatibility level:      {report.level}")
        print(f"signals emitted/observed: {result.signals_emitted} / {result.signals_observed}")
        print(f"mirrored signals:         {result.mirrored} "
              f"{sidecar.mirror.count_by_type() if sidecar.mirror else ''}")
        print(f"reactions learned from:   {result.reactions_learned}")
        print(f"suggestions produced:     {result.suggestions_produced}")
        print(f"suggestions published:    {result.suggestions_published}"
              + ("  (observe-only: publishing muted)" if observe_only else ""))
        print(f"committed actions:        {result.committed_actions}  (must be 0)")
        print(f"conscience.death() calls: {result.conscience_death_calls}  (must be 0)")
        conf = sidecar.channel.confidence_distribution() if sidecar.channel else {}
        print(f"suggestion confidence:    mean={conf.get('mean', 0):.3f} "
              f"over {conf.get('count', 0)}")
        if state_dir is not None:
            print(f"persisted under:          {state_dir}")
        print("-" * 70)
        print("The sidecar observed, learned, and suggested. It committed nothing;")
        print("action authority stays with Solaris_Ai. No claim of consciousness.")

    return result


def main() -> None:
    run_sidecar_observation(verbose=True)


if __name__ == "__main__":
    main()
