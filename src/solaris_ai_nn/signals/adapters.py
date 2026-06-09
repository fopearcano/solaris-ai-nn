"""Conversion helpers between Solaris_Ai signals and Solaris-AI-NN signals.

This module is the seam between the two signal ecologies. It has two layers:

* low-level serialisation (:func:`signal_to_dict` / :func:`dict_to_signal`),
  which knows the field layout of each canonical type; and
* :class:`SolarisSignalAdapter`, a robust, duck-typed adapter that accepts
  *any* of three shapes and produces a canonical Solaris-AI-NN signal:

    A. native ``solaris_ai_nn`` dataclasses (returned as-is);
    B. dict-like serialised events;
    C. object-like Solaris_Ai dataclasses exposing attributes such as ``id``,
       ``timestamp``, ``origin``, ``modality``, ``payload``, ``intensity``,
       ``valence``, ``novelty``, ``division``, ``union``.

Crucially, this module does **not** import ``solaris-ai``. It relies on duck
typing so the bridge stays independent and testable; a real Solaris_Ai signal
just needs the right attributes (or a ``kind``/class name) to convert.
"""

from __future__ import annotations

from dataclasses import asdict, fields
from typing import Any, Dict, Type, Union

from . import canonical as C

# Registry of canonical types by name, used to rebuild a signal from a dict.
_TYPES: Dict[str, Type[C.Signal]] = {
    cls.__name__: cls
    for cls in (
        C.Signal,
        C.Stimulus,
        C.Push,
        C.Desire,
        C.Action,
        C.Reaction,
        C.MeaningEvent,
        C.MapUpdate,
        C.LogosTension,
    )
}


def signal_to_dict(signal: C.Signal) -> Dict[str, Any]:
    """Serialise any canonical signal to a JSON-friendly dict.

    The dict always carries a ``"kind"`` key so it can be rebuilt later.
    """
    data = asdict(signal)
    data["kind"] = signal.kind
    # ``fracture`` is a computed property, not a field; surface it for consumers.
    if isinstance(signal, C.LogosTension):
        data["fracture"] = signal.fracture
    return data


def dict_to_signal(data: Dict[str, Any]) -> C.Signal:
    """Rebuild a canonical signal from a dict produced by :func:`signal_to_dict`.

    Unknown keys (e.g. the computed ``fracture``) are ignored. Missing keys fall
    back to the dataclass defaults, so partial Solaris_Ai payloads still convert.
    """
    kind = data.get("kind", "Signal")
    cls = _TYPES.get(kind, C.Signal)
    valid = {f.name for f in fields(cls)}
    kwargs = {k: v for k, v in data.items() if k in valid}
    return cls(**kwargs)


def remap_fields(data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
    """Rename keys in ``data`` according to ``mapping`` (old -> new).

    A small helper for when the reference repo and this repo diverge on a field
    name; lets the bridge translate without bespoke code per signal type.
    """
    return {mapping.get(k, k): v for k, v in data.items()}


# --------------------------------------------------------------------------- #
# Robust, duck-typed adapter                                                  #
# --------------------------------------------------------------------------- #

# Attribute / key names we are willing to copy off an arbitrary raw signal.
# (Union of all canonical dataclass fields plus a couple of common aliases.)
_CANDIDATE_FIELDS = (
    "id",
    "timestamp",
    "origin",
    "modality",
    "payload",
    "intensity",
    "is_absence",
    "direction",
    "source_stimulus_id",
    "proposal",
    "motivation",
    "confidence",
    "name",
    "action_id",
    "valence",
    "stimulus_id",
    "meaning",
    "novelty",
    "key",
    "value",
    "boundary",
    "division",
    "union",
)

RawSignal = Union[C.Signal, Dict[str, Any], object]


def extract_payload(raw_signal: RawSignal) -> Dict[str, Any]:
    """Return a plain dict of the signal's fields, regardless of source shape.

    Computed/derived markers (``kind``, ``type``, ``fracture``) are not included
    -- ``fracture`` is recomputed by :class:`~...LogosTension`. Works for native
    dataclasses, dicts, and attribute-bearing objects (duck typing).
    """
    if isinstance(raw_signal, C.Signal):
        return asdict(raw_signal)
    if isinstance(raw_signal, dict):
        return {
            k: v
            for k, v in raw_signal.items()
            if k not in ("kind", "type", "signal_type", "fracture")
        }
    # Object-like (e.g. a Solaris_Ai dataclass we have not imported).
    payload: Dict[str, Any] = {}
    for name in _CANDIDATE_FIELDS:
        if hasattr(raw_signal, name):
            value = getattr(raw_signal, name)
            if not callable(value):
                payload[name] = value
    return payload


def _infer_type(fields_present: Dict[str, Any]) -> str:
    """Heuristically infer a canonical signal type from the fields present."""
    f = fields_present
    if "division" in f and "union" in f:
        return "LogosTension"
    if "action_id" in f and "valence" in f:
        return "Reaction"
    if "meaning" in f:
        return "MeaningEvent"
    if "proposal" in f or ("motivation" in f and "confidence" in f):
        return "Desire"
    if "boundary" in f or ("key" in f and "value" in f):
        return "MapUpdate"
    if "direction" in f or "source_stimulus_id" in f:
        return "Push"
    if "name" in f and "action_id" not in f:
        return "Action"
    # Stimulus is the most common inbound signal; treat it as the default.
    return "Stimulus"


def extract_signal_type(raw_signal: RawSignal) -> str:
    """Return the canonical signal-type name for any raw signal shape.

    Resolution order: native ``kind`` -> explicit ``kind``/``type`` key ->
    class name (if it matches a canonical type) -> field-based inference.
    """
    if isinstance(raw_signal, C.Signal):
        return raw_signal.kind
    if isinstance(raw_signal, dict):
        for key in ("kind", "type", "signal_type"):
            value = raw_signal.get(key)
            if isinstance(value, str) and value in _TYPES:
                return value
        return _infer_type(raw_signal)
    # Object-like: prefer a matching class name, then a ``kind`` attr, then infer.
    name = type(raw_signal).__name__
    if name in _TYPES:
        return name
    kind_attr = getattr(raw_signal, "kind", None)
    if isinstance(kind_attr, str) and kind_attr in _TYPES:
        return kind_attr
    return _infer_type(extract_payload(raw_signal))


class SolarisSignalAdapter:
    """Translate between Solaris_Ai-style signals and canonical NN signals.

    Stateless and cheap to construct. Methods are also exposed as module-level
    functions (``to_nn_signal`` etc.) backed by a shared default instance.
    """

    def to_nn_signal(self, raw_signal: RawSignal) -> C.Signal:
        """Convert any raw signal (dataclass / dict / object) to a canonical one.

        Native ``solaris_ai_nn`` signals are returned unchanged. Missing optional
        fields fall back to canonical dataclass defaults.
        """
        if isinstance(raw_signal, C.Signal):
            return raw_signal
        kind = extract_signal_type(raw_signal)
        payload = extract_payload(raw_signal)
        cls = _TYPES.get(kind, C.Stimulus)
        valid = {fld.name for fld in fields(cls)}
        kwargs = {k: v for k, v in payload.items() if k in valid}
        return cls(**kwargs)

    @staticmethod
    def extract_signal_type(raw_signal: RawSignal) -> str:
        """See module-level :func:`extract_signal_type`."""
        return extract_signal_type(raw_signal)

    @staticmethod
    def extract_payload(raw_signal: RawSignal) -> Dict[str, Any]:
        """See module-level :func:`extract_payload`."""
        return extract_payload(raw_signal)

    @staticmethod
    def from_nn_action(
        name: str,
        payload: Any = None,
        origin: str = "solaris_ai_nn",
    ) -> C.Action:
        """Build a Solaris-compatible :class:`Action` *suggestion* from the NN side.

        The NN layer suggests; it does not decide. The returned Action is a
        proposal for a Solaris_Ai I/O / integration layer to accept or reject.
        """
        return C.Action(origin=origin, name=name, payload=payload)

    @staticmethod
    def from_nn_desire(
        proposal: str,
        motivation: float = 0.0,
        confidence: float = 0.0,
        origin: str = "solaris_ai_nn",
    ) -> C.Desire:
        """Build a Solaris-compatible :class:`Desire` tendency from the NN side."""
        return C.Desire(
            origin=origin,
            proposal=proposal,
            motivation=motivation,
            confidence=confidence,
        )


# Shared default instance + module-level convenience functions.
_DEFAULT_ADAPTER = SolarisSignalAdapter()


def to_nn_signal(raw_signal: RawSignal) -> C.Signal:
    """Module-level shortcut for :meth:`SolarisSignalAdapter.to_nn_signal`."""
    return _DEFAULT_ADAPTER.to_nn_signal(raw_signal)


def from_nn_action(name: str, payload: Any = None, origin: str = "solaris_ai_nn") -> C.Action:
    """Module-level shortcut for :meth:`SolarisSignalAdapter.from_nn_action`."""
    return SolarisSignalAdapter.from_nn_action(name, payload=payload, origin=origin)


def from_nn_desire(
    proposal: str,
    motivation: float = 0.0,
    confidence: float = 0.0,
    origin: str = "solaris_ai_nn",
) -> C.Desire:
    """Module-level shortcut for :meth:`SolarisSignalAdapter.from_nn_desire`."""
    return SolarisSignalAdapter.from_nn_desire(
        proposal, motivation=motivation, confidence=confidence, origin=origin
    )
