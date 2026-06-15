"""Internal/external classification -- with explicit mixed records.

The :class:`InternalExternalClassifier` classifies records from across the stack
(sensorium, live field, feeder SDK, metabolism, ontogenesis, semiogenesis,
cognition, memory, latent replay, operator console) as internal, external, or
*mixed*. A record may be mixed, mixed classification is explicit, and processed
sensory data is never silently collapsed into "internal self".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class InternalExternalLabel:
    INTERNAL = "internal"
    EXTERNAL = "external"
    MIXED = "mixed"
    UNKNOWN = "unknown"

    ALL = (INTERNAL, EXTERNAL, MIXED, UNKNOWN)


# Coarse origin -> (internal?, external?). Mixed when both are true.
_ORIGIN_SIDES = {
    "plural_sensorium": (True, True),    # receptor (internal) reads world (ext)
    "live_field": (False, True),
    "feeder_sdk": (False, True),
    "perceptual_metabolism": (True, False),
    "perceptual_ontogenesis": (True, False),
    "semiogenesis": (True, False),
    "sensorium_cognition": (True, False),
    "memory": (True, False),
    "latent_replay": (True, False),
    "operator_console": (False, True),   # operator is external to Solaris
}


@dataclass
class InternalExternalClassification:
    ref: str
    origin: str
    label: str
    internal_component: bool
    external_component: bool
    detail: str = ""

    @property
    def is_mixed(self) -> bool:
        return self.label == InternalExternalLabel.MIXED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ref": self.ref,
            "origin": self.origin,
            "label": self.label,
            "internal_component": self.internal_component,
            "external_component": self.external_component,
            "is_mixed": self.is_mixed,
            "detail": self.detail,
            "note": "processed sensory data is not silently collapsed into "
                    "internal-self; mixed records are explicit",
        }


@dataclass
class InternalExternalClassifier:
    classifications: List[InternalExternalClassification] = field(
        default_factory=list)

    def classify(self, ref: str, origin: str, *,
                 detail: str = "") -> InternalExternalClassification:
        internal, external = _ORIGIN_SIDES.get(origin, (False, False))
        if internal and external:
            label = InternalExternalLabel.MIXED
        elif internal:
            label = InternalExternalLabel.INTERNAL
        elif external:
            label = InternalExternalLabel.EXTERNAL
        else:
            label = InternalExternalLabel.UNKNOWN
        c = InternalExternalClassification(
            ref=ref, origin=origin, label=label,
            internal_component=internal, external_component=external,
            detail=detail)
        self.classifications.append(c)
        return c

    def mixed(self) -> List[InternalExternalClassification]:
        return [c for c in self.classifications if c.is_mixed]

    def distribution(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for c in self.classifications:
            out[c.label] = out.get(c.label, 0) + 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "classification_count": len(self.classifications),
            "mixed_count": len(self.mixed()),
            "distribution": self.distribution(),
            "classifications": [c.to_dict() for c in self.classifications],
        }
