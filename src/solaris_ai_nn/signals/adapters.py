"""Conversion helpers between Solaris_Ai signals and Solaris-AI-NN signals.

This module is the *low-level* seam: it converts canonical signals to/from
plain dictionaries. Because Solaris-AI-NN does not yet import the reference
package, the bridge works on dicts (which a future adapter can produce from real
``solaris.runtime.signals`` instances). ``bridges/signal_bridge.py`` builds the
higher-level, runtime-facing bridge on top of these helpers.

Keeping serialisation here means there is exactly one place that knows the field
layout of each signal type.
"""

from __future__ import annotations

from dataclasses import asdict, fields
from typing import Any, Dict, Type

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
