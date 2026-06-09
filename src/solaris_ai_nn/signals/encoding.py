"""Event -> numeric vector encoder.

The reservoir consumes plain float vectors, so every canonical signal must be
turned into a small, fixed-length feature vector. This is **not** language
understanding -- it is *event-continuity* encoding. The aim is just enough
structure for a temporal substrate to learn "this kind of event tends to be
followed by that kind of reaction".

Vector layout (fixed, deterministic):

    [ one-hot signal kind                                ]  len(KINDS) = 8
    [ intensity, valence, novelty,                       ]
    [ division, union, fracture,                         ]  8 scalar slots
    [ is_absence, time_delta                             ]
    [ heartbeat flag                                     ]  1 slot
    [ one-hot payload category                           ]  PAYLOAD_BUCKETS = 16
    [ one-hot origin bucket                              ]  ORIGIN_BUCKETS = 8

Why these features? They cover the Solaris signal spine and side-streams:
intensity (Stimulus/Push drive), valence (Reaction reinforcement), novelty
(MeaningEvent / Mysterium), division+union+fracture (LogosTension), is_absence
(the Subtraction Principle), plus continuity slots (time delta, heartbeat) and
coarse identity slots (payload category, origin).

Payload categories use a small *dictionary* of known payloads (distinct slots
for distinct words) plus a hashing fallback for anything unseen -- a pure hash
into a handful of buckets collides too readily, which would make distinct
stimuli indistinguishable to the substrate.

Note on return type: vectors are plain ``list[float]`` (not ``numpy.ndarray``).
The reservoir, readout, and math helpers are deliberately pure-stdlib and
list-based (see README / RESEARCH_NOTES); a list flows through them unchanged.
A NumPy-backed backend remains an optional future step, not a requirement here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from . import canonical as C

# Canonical kinds the substrate can see on its input side. Order is fixed so
# the one-hot mapping is stable across runs and processes.
KINDS: List[str] = [
    "Stimulus",
    "Push",
    "Desire",
    "Action",
    "Reaction",
    "MeaningEvent",
    "MapUpdate",
    "LogosTension",
]

# Scalar feature slots, in fixed order (after the kind one-hot block).
SCALAR_FIELDS: List[str] = [
    "intensity",
    "valence",
    "novelty",
    "division",
    "union",
    "fracture",
    "is_absence",
    "time_delta",
]

PAYLOAD_BUCKETS = 16
ORIGIN_BUCKETS = 8


def _hash(text: str) -> int:
    """Stable, process-independent string hash (unlike the salted builtin)."""
    h = 0
    for ch in text:
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    return h


@dataclass
class EventEncoder:
    """Convert canonical signals into fixed-length feature vectors.

    Payload-category slot layout:

    * index 0 -- empty / ``None`` payload
    * indices ``1..len(vocabulary)`` -- known vocabulary words (distinct slots)
    * remaining indices -- hashing buckets for unknown payloads

    Args:
        vocabulary: Known payload strings to give dedicated, collision-free
            slots. ``None`` => everything hashes (still fine, just collision-prone
            for tiny bucket counts).
        max_dt: Time delta (seconds) that maps to a normalised value of 1.0.
    """

    vocabulary: Optional[Sequence[str]] = None
    max_dt: float = 1.0
    _vocab_index: Dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        vocab = list(self.vocabulary or [])
        if len(vocab) + 1 > PAYLOAD_BUCKETS:
            raise ValueError(
                f"vocabulary too large for {PAYLOAD_BUCKETS} payload buckets"
            )
        # Reserve index 0 for None/empty; vocabulary occupies 1..len(vocab).
        self._vocab_index = {word: i + 1 for i, word in enumerate(vocab)}

    @property
    def vector_size(self) -> int:
        """Length of every encoded vector."""
        return len(KINDS) + len(SCALAR_FIELDS) + 1 + PAYLOAD_BUCKETS + ORIGIN_BUCKETS

    # Backwards-compatible alias used by the runtime loop / existing code.
    @property
    def dim(self) -> int:
        """Alias of :attr:`vector_size`."""
        return self.vector_size

    # -- payload / origin bucketing ----------------------------------------

    def _payload_category(self, payload: object) -> int:
        """Map a payload to a payload-bucket index (see class docstring)."""
        if payload is None:
            return 0
        text = str(payload)
        if text == "":
            return 0
        if text in self._vocab_index:
            return self._vocab_index[text]
        reserved = len(self._vocab_index) + 1  # slots 0..reserved-1 are taken
        tail = PAYLOAD_BUCKETS - reserved
        if tail <= 0:
            return _hash(text) % PAYLOAD_BUCKETS
        return reserved + (_hash(text) % tail)

    def _origin_bucket(self, origin: object) -> int:
        """Map an origin label to one of ``ORIGIN_BUCKETS`` buckets."""
        text = str(origin) if origin is not None else ""
        if text == "":
            return 0
        return _hash(text) % ORIGIN_BUCKETS

    def _payload_of(self, signal: C.Signal) -> object:
        payload = getattr(signal, "payload", None)
        if payload is None:
            payload = getattr(signal, "meaning", None) or getattr(signal, "name", None)
        return payload

    @staticmethod
    def _fracture_of(signal: C.Signal) -> float:
        """fracture = |division - union|, using the property when present."""
        if hasattr(signal, "fracture"):
            try:
                return float(getattr(signal, "fracture"))
            except (TypeError, ValueError):
                pass
        division = float(getattr(signal, "division", 0.0) or 0.0)
        union = float(getattr(signal, "union", 0.0) or 0.0)
        return abs(division - union)

    # -- encoding -----------------------------------------------------------

    def encode(self, signal: C.Signal, dt: float = 0.0, heartbeat: bool = False) -> List[float]:
        """Encode ``signal`` into a fixed-length feature vector (``list[float]``).

        Args:
            signal: Any canonical signal.
            dt: Seconds since the previous event (temporal continuity slot).
            heartbeat: Whether this event coincides with a heartbeat tick.
        """
        vec = [0.0] * self.vector_size

        # --- one-hot signal kind ---
        kind = signal.kind
        if kind in KINDS:
            vec[KINDS.index(kind)] = 1.0
        offset = len(KINDS)

        # --- scalar slots (order = SCALAR_FIELDS) ---
        time_delta = max(0.0, min(1.0, dt / self.max_dt)) if self.max_dt > 0 else 0.0
        scalars = {
            "intensity": float(getattr(signal, "intensity", 0.0) or 0.0),
            "valence": float(getattr(signal, "valence", 0.0) or 0.0),
            "novelty": float(getattr(signal, "novelty", 0.0) or 0.0),
            "division": float(getattr(signal, "division", 0.0) or 0.0),
            "union": float(getattr(signal, "union", 0.0) or 0.0),
            "fracture": self._fracture_of(signal),
            "is_absence": 1.0 if getattr(signal, "is_absence", False) else 0.0,
            "time_delta": time_delta,
        }
        for i, name in enumerate(SCALAR_FIELDS):
            vec[offset + i] = scalars[name]
        offset += len(SCALAR_FIELDS)

        # --- heartbeat flag ---
        vec[offset] = 1.0 if heartbeat else 0.0
        offset += 1

        # --- payload category one-hot ---
        vec[offset + self._payload_category(self._payload_of(signal))] = 1.0
        offset += PAYLOAD_BUCKETS

        # --- origin bucket one-hot ---
        vec[offset + self._origin_bucket(getattr(signal, "origin", None))] = 1.0
        offset += ORIGIN_BUCKETS

        return vec

    def pattern_key(self, signal: C.Signal) -> str:
        """A coarse, hashable signature of an event for habit bookkeeping.

        Habits should reinforce *kinds of situations*, not unique events, so the
        key is intentionally lossy: kind + payload category.
        """
        return f"{signal.kind}:{self._payload_category(self._payload_of(signal))}"
