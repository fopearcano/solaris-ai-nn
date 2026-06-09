"""LogosTension -> substrate modulation.

Solaris_Ai's Logos engine produces a tension between two opposing pulls:

* ``division`` -- presence of data / the rational (dia-ballein)
* ``union``    -- absence of data / the irrational (sun-ballein)
* ``fracture`` -- ``|division - union|``, "the substrate of choice"

This module lets that tension *modulate* the neural substrate. It is a plain
gain/noise mechanism -- nothing mystical -- with three documented effects:

1. **High fracture -> larger input gain.** When the system is being pulled hard
   in conflicting directions, inputs are amplified so the reservoir reacts more
   strongly to the current event.
2. **High union -> more exploratory noise.** Union is data-*absence*; with less
   to go on, we inject more input noise, widening exploration.
3. **High division -> steadier, more confident readout.** Division is
   data-*presence*; rational grounding raises confidence in the readout's
   tendency. (High union lowers it.)

Modulation is the identity when no LogosTension is supplied, so it is safe to
apply unconditionally.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence

from ..utils.math import clamp


def _read(logos: Any, attr: str) -> float:
    """Read ``division`` / ``union`` / ``fracture`` from a signal, dict, or None."""
    if logos is None:
        return 0.0
    if isinstance(logos, dict):
        value = logos.get(attr, 0.0)
    else:
        value = getattr(logos, attr, 0.0)
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _fracture(logos: Any) -> float:
    """fracture = explicit value if present, else |division - union|."""
    if logos is None:
        return 0.0
    if not isinstance(logos, dict) and hasattr(logos, "fracture"):
        return _read(logos, "fracture")
    if isinstance(logos, dict) and "fracture" in logos:
        return _read(logos, "fracture")
    return abs(_read(logos, "division") - _read(logos, "union"))


@dataclass
class LogosModulator:
    """Modulate reservoir input and readout confidence from a LogosTension.

    Args:
        input_gain: How strongly fracture amplifies the input (gain = 1 + k*fracture).
        union_noise: Input-noise amplitude per unit of union (exploration).
        division_confidence: Confidence boost per unit of division.
        union_confidence_penalty: Confidence reduction per unit of union.
        seed: Seed for the exploration-noise RNG (determinism).
    """

    input_gain: float = 0.5
    union_noise: float = 0.2
    division_confidence: float = 0.4
    union_confidence_penalty: float = 0.4
    seed: int = 0
    _rng: random.Random = field(default_factory=lambda: random.Random(0), init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def apply_to_input(self, vector: Sequence[float], logos_tension: Optional[Any]) -> List[float]:
        """Return a modulated copy of ``vector`` given the current LogosTension.

        ``logos_tension`` may be a :class:`LogosTension`, a dict, or ``None``
        (identity). Gain scales with fracture; additive noise scales with union.
        """
        if logos_tension is None:
            return list(vector)
        fracture = max(0.0, _fracture(logos_tension))
        union = max(0.0, _read(logos_tension, "union"))
        gain = 1.0 + self.input_gain * fracture
        noise = self.union_noise * union
        if noise <= 0.0:
            return [v * gain for v in vector]
        return [v * gain + self._rng.uniform(-noise, noise) for v in vector]

    def apply_to_readout_confidence(
        self, confidence: float, logos_tension: Optional[Any]
    ) -> float:
        """Adjust a readout confidence in ``[0, 1]`` by the LogosTension.

        Division raises confidence (rational grounding); union lowers it
        (irrational / data-absent). Result is clamped to ``[0, 1]``.
        """
        if logos_tension is None:
            return clamp(confidence, 0.0, 1.0)
        division = _read(logos_tension, "division")
        union = _read(logos_tension, "union")
        adjusted = (
            confidence
            + self.division_confidence * division
            - self.union_confidence_penalty * union
        )
        return clamp(adjusted, 0.0, 1.0)
