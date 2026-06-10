"""Safe optional imports of the real ``fopearcano/solaris-ai`` package.

Solaris_Ai is NEVER a required dependency. Everything in this module degrades
gracefully: if the ``solaris`` package is not importable, functions return
False / None / empty containers and record a clear error message instead of
raising. Tests can mock availability by inserting fake modules into
``sys.modules`` (imports are resolved per call, never cached as failures).
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, Optional

# Module paths in the reference repo (src/solaris/...).
SOLARIS_ROOT = "solaris"
SOLARIS_SIGNALS_MODULE = "solaris.runtime.signals"
SOLARIS_CONSCIENCE_MODULE = "solaris.conscience"

# Canonical signal class names we look for in the reference signals module.
SIGNAL_CLASS_NAMES = (
    "Signal", "Stimulus", "Push", "Desire", "Action", "Reaction",
    "MeaningEvent", "MapUpdate", "LogosTension",
)

_last_error: Optional[str] = None


def _record_error(context: str, exc: Exception) -> None:
    global _last_error
    _last_error = f"{context}: {type(exc).__name__}: {exc}"


def get_solaris_import_error() -> Optional[str]:
    """The most recent import failure message, or ``None`` if none recorded."""
    return _last_error


def is_solaris_available() -> bool:
    """True if the real ``solaris`` package can be imported right now.

    Never raises; a failed import is recorded via
    :func:`get_solaris_import_error`.
    """
    try:
        importlib.import_module(SOLARIS_ROOT)
        return True
    except Exception as exc:  # ImportError and anything a broken install raises
        _record_error(f"import {SOLARIS_ROOT!r} failed", exc)
        return False


def import_solaris_signals() -> Dict[str, Any]:
    """Import the reference signal classes, keyed by class name.

    Returns an empty dict (and records the error) if Solaris_Ai is
    unavailable or its signals module lacks the expected classes.
    """
    try:
        module = importlib.import_module(SOLARIS_SIGNALS_MODULE)
    except Exception as exc:
        _record_error(f"import {SOLARIS_SIGNALS_MODULE!r} failed", exc)
        return {}
    found: Dict[str, Any] = {}
    for name in SIGNAL_CLASS_NAMES:
        cls = getattr(module, name, None)
        if cls is not None:
            found[name] = cls
    if not found:
        _record_error(
            f"inspect {SOLARIS_SIGNALS_MODULE!r}",
            ImportError("module importable but no canonical signal classes found"),
        )
    return found


def import_solaris_conscience() -> Optional[type]:
    """Import the reference ``Conscience`` class, or ``None`` if unavailable."""
    try:
        module = importlib.import_module(SOLARIS_CONSCIENCE_MODULE)
    except Exception as exc:
        _record_error(f"import {SOLARIS_CONSCIENCE_MODULE!r} failed", exc)
        return None
    cls = getattr(module, "Conscience", None)
    if cls is None:
        _record_error(
            f"inspect {SOLARIS_CONSCIENCE_MODULE!r}",
            ImportError("module importable but has no Conscience class"),
        )
    return cls
