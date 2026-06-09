"""Event -> numeric vector encoder.

The reservoir consumes plain float vectors, so every canonical signal must be
turned into a small, fixed-length feature vector. This is **not** language
understanding -- it is *event-continuity* encoding. The aim is just enough
structure for a temporal substrate to learn "this kind of event tends to be
followed by that kind of reaction".

Vector layout (fixed, deterministic):

    [ one-hot signal kind                    ]  len(KINDS)
    [ intensity, valence, novelty, fracture  ]  4 scalar slots
    [ one-hot payload category               ]  PAYLOAD_BUCKETS
    [ heartbeat flag, normalised time delta  ]  2 temporal slots

Payload categories use a small *dictionary* of known payloads (distinct slots
for distinct words) plus a hashing fallback for anything unseen. A pure hash
into a handful of buckets collides too easily (e.g. "light"/"noise"/"food" all
land in the same bucket), which would make distinct stimuli indistinguishable to
the substrate. The dictionary guarantees separation for a known small
vocabulary, which is exactly the regime these first experiments live in.
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

PAYLOAD_BUCKETS = 16


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
    def dim(self) -> int:
        """Length of every encoded vector."""
        return len(KINDS) + 4 + PAYLOAD_BUCKETS + 2

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

    def _payload_of(self, signal: C.Signal) -> object:
        payload = getattr(signal, "payload", None)
        if payload is None:
            payload = getattr(signal, "meaning", None) or getattr(signal, "name", None)
        return payload

    def encode(self, signal: C.Signal, dt: float = 0.0, heartbeat: bool = False) -> List[float]:
        """Encode ``signal`` into a feature vector.

        Args:
            signal: Any canonical signal.
            dt: Seconds since the previous event (temporal continuity slot).
            heartbeat: Whether this event coincides with a heartbeat tick.
        """
        vec = [0.0] * self.dim

        # --- one-hot signal kind ---
        kind = signal.kind
        if kind in KINDS:
            vec[KINDS.index(kind)] = 1.0
        offset = len(KINDS)

        # --- scalar slots: intensity / valence / novelty / fracture ---
        vec[offset + 0] = float(getattr(signal, "intensity", 0.0))
        vec[offset + 1] = float(getattr(signal, "valence", 0.0))
        vec[offset + 2] = float(getattr(signal, "novelty", 0.0))
        vec[offset + 3] = float(getattr(signal, "fracture", 0.0)) if hasattr(signal, "fracture") else 0.0
        offset += 4

        # --- payload category one-hot ---
        vec[offset + self._payload_category(self._payload_of(signal))] = 1.0
        offset += PAYLOAD_BUCKETS

        # --- temporal slots ---
        vec[offset + 0] = 1.0 if heartbeat else 0.0
        vec[offset + 1] = max(0.0, min(1.0, dt / self.max_dt)) if self.max_dt > 0 else 0.0

        return vec

    def pattern_key(self, signal: C.Signal) -> str:
        """A coarse, hashable signature of an event for habit bookkeeping.

        Habits should reinforce *kinds of situations*, not unique events, so the
        key is intentionally lossy: kind + payload category.
        """
        return f"{signal.kind}:{self._payload_category(self._payload_of(signal))}"
