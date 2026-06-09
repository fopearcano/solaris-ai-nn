"""High-level bridge to a future Solaris_Ai runtime.

Where ``signals/adapters.py`` handles the dataclass <-> dict mechanics, this
module is the runtime-facing seam: it is where Solaris-AI-NN will eventually
*subscribe* to a real Solaris_Ai Bus, translate inbound signals into the NN
vocabulary, push them into an :class:`ExperimentLoop`, and translate the loop's
Actions/Desires back out.

For now it works on plain dicts (which a thin adapter can produce from real
``solaris.runtime.signals`` instances), so no dependency on the reference repo
is introduced. This keeps Phase-1 (signal-bridge compatibility) a small, well-
scoped change rather than a rewrite.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..runtime.experiment_loop import ExperimentLoop
from ..signals import canonical as C
from ..signals.adapters import dict_to_signal, signal_to_dict


def inbound(loop: ExperimentLoop, solaris_signal: Dict[str, Any]) -> Optional[C.Stimulus]:
    """Translate an inbound Solaris_Ai signal (as a dict) into the loop.

    Only Stimulus-like signals are injected; other kinds are converted and
    returned for inspection but not fed as drivers (the loop generates its own
    Pushes/Desires/Actions).

    Returns the injected Stimulus, or ``None`` if the signal was not a stimulus.
    """
    signal = dict_to_signal(solaris_signal)
    if isinstance(signal, C.Stimulus):
        loop.inject(signal)
        return signal
    return None


def outbound(action: C.Action) -> Dict[str, Any]:
    """Translate a loop Action back into a Solaris_Ai-shaped dict."""
    return signal_to_dict(action)
