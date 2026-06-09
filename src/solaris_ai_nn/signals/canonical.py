"""Canonical Solaris signal vocabulary, re-expressed for Solaris-AI-NN.

These dataclasses mirror the signal types defined in the reference repository
``fopearcano/solaris-ai`` (``src/solaris/runtime/signals.py``). They are kept
*intentionally close* to the originals so that the neural substrate speaks the
same language as the conceptual system, but this package does **not** import
from the reference repo. Solaris-AI-NN must stay self-contained for now;
``signals/adapters.py`` and ``bridges/signal_bridge.py`` provide the seam where
the two vocabularies can later be wired together.

Conceptual spine (preserved verbatim from Solaris_Ai):

    Stimulus -> Push -> Desire -> Action

Side streams:

    MeaningEvent, MapUpdate, LogosTension, Reaction

Nothing here is "conscious". Each type is a plain data record that flows through
an adaptive event loop. Read every name as *consciousness-inspired*, never as a
claim about subjective experience.
"""

from __future__ import annotations

import itertools
import time
from dataclasses import dataclass, field
from typing import Any, Optional

# Monotonic, process-local id source. Mirrors the reference Bus' auto-id idea
# without sharing global state across processes.
_id_counter = itertools.count(1)


def _next_id() -> int:
    return next(_id_counter)


@dataclass
class Signal:
    """Root of every signal type.

    Attributes:
        id: Monotonic per-process identifier.
        timestamp: Unix time (seconds) at construction.
        origin: Free-text label naming the emitting component.
    """

    id: int = field(default_factory=_next_id)
    timestamp: float = field(default_factory=time.time)
    origin: str = "unknown"

    @property
    def kind(self) -> str:
        """Stable type tag used by the event encoder (the class name)."""
        return type(self).__name__


@dataclass
class Stimulus(Signal):
    """Sensory or internal input event.

    ``is_absence`` carries the Solaris "Subtraction Principle": the *absence* of
    expected input is itself a meaningful stimulus (see AION/Impulse).
    """

    modality: str = "generic"
    payload: Any = None
    intensity: float = 0.0  # [0, 1]
    is_absence: bool = False


@dataclass
class Push(Signal):
    """Motivational force toward action.

    Emitted continuously ("continuity") or reactively in response to a stimulus.
    """

    intensity: float = 0.0  # [0, 1]
    direction: str = "continuity"  # e.g. "continuity" | "reactive"
    source_stimulus_id: Optional[int] = None


@dataclass
class Desire(Signal):
    """A formulated intention awaiting enough confidence/motivation to act."""

    proposal: str = ""
    motivation: float = 0.0  # [0, 1]
    confidence: float = 0.0  # [0, 1]


@dataclass
class Action(Signal):
    """A behavioural unit. Also re-enters the loop as a stimulus source."""

    name: str = ""
    payload: Any = None


@dataclass
class Reaction(Signal):
    """Consequence of an action, scored for reinforcement.

    ``valence`` in [-1, +1]: negative = aversive, positive = rewarding.
    """

    action_id: Optional[int] = None
    valence: float = 0.0  # [-1, +1]


@dataclass
class MeaningEvent(Signal):
    """Cognitive interpretation of a stimulus, with a novelty score."""

    stimulus_id: Optional[int] = None
    meaning: str = ""
    novelty: float = 0.0  # [0, 1]


@dataclass
class MapUpdate(Signal):
    """A change to the system's self-representation (Inner MAP)."""

    key: str = ""
    value: Any = None
    boundary: bool = False  # True => updates a self-limit, not a plain fact


@dataclass
class LogosTension(Signal):
    """Balance between division (dia-ballein) and union (sun-ballein).

    ``fracture`` is the magnitude of their mismatch and is the substrate of
    choice in Solaris_Ai. Here it is just a scalar the substrate can consume.
    """

    division: float = 0.0  # rational / data-present pull
    union: float = 0.0  # irrational / data-absent pull

    @property
    def fracture(self) -> float:
        """Absolute mismatch between division and union (>= 0)."""
        return abs(self.division - self.union)
