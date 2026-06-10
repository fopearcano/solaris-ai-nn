"""SolarisBusConnector -- observe a Solaris_Ai-like Bus, never act on it.

The connector subscribes to a bus (real Solaris_Ai's async Bus or any
duck-typed fake), forwards observed signals into the
:class:`SolarisNeuralBridge`, and routes resulting *suggestions* through a
:class:`SuggestionChannel`. Hard rules, enforced here:

* **observe-only mode publishes nothing**, ever;
* even with publishing on, only :class:`NeuralSuggestion` objects leave --
  never committed Actions;
* Reaction signals drive learning (``bridge.react``) before being processed as
  events, so feedback lands on the suggestion that earned it;
* our own published suggestions are ignored on the way back in (no feedback
  loop);
* ``detach()`` unsubscribes when the bus supports it, otherwise the connector
  goes inactive and drops everything it receives.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..utils.logging import get_logger
from .integration_state import IntegrationState
from .signal_mirror import SignalMirror
from .suggestion_channel import (
    ACTION_SUGGESTION,
    NeuralSuggestion,
    SuggestionChannel,
)

logger = get_logger(__name__)


@dataclass
class SolarisBusConnector:
    """Reversible, observe-first attachment between a bus and the NN bridge.

    Args:
        bridge: The :class:`SolarisNeuralBridge` that consumes signals.
        publish_suggestions: Allow publishing suggestions to the bus.
        observe_only: Hard mute -- nothing is ever published.
        allowed_signal_types: Only process these signal kinds (None = all).
        suggestion_threshold: Minimum confidence for a suggestion to be
            published (below it, the suggestion is stored but held back).
    """

    bridge: Any
    publish_suggestions: bool = True
    observe_only: bool = False
    allowed_signal_types: Optional[List[str]] = None
    suggestion_threshold: float = 0.5
    mirror: Optional[SignalMirror] = None
    channel: Optional[SuggestionChannel] = None
    state: IntegrationState = field(default_factory=IntegrationState)

    _bus: Any = field(default=None, init=False, repr=False)
    _active: bool = field(default=False, init=False)
    _handler: Any = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.channel is None:
            self.channel = SuggestionChannel(publish_enabled=self.publish_suggestions)

    # -- attach / detach -------------------------------------------------------

    def attach(self, bus: Any) -> None:
        """Subscribe to ``bus`` (prefers ``subscribe_all``; async-aware)."""
        if self._active:
            raise RuntimeError("connector is already attached; detach first")
        # Async buses (the real Solaris Bus) await their handlers; sync fakes
        # call them directly. Pick the handler flavour by duck-typing publish.
        if inspect.iscoroutinefunction(getattr(bus, "publish", None)):
            async def handler(signal: Any) -> None:  # pragma: no cover - async path
                self.on_signal(signal)
        else:
            def handler(signal: Any) -> None:
                self.on_signal(signal)
        self._handler = handler

        subscribe_all = getattr(bus, "subscribe_all", None)
        if callable(subscribe_all):
            subscribe_all(handler)
        elif callable(getattr(bus, "subscribe", None)):
            # Per-type subscription needs signal classes; without subscribe_all
            # we subscribe to whatever types the bus knows about, if it tells us.
            raise ValueError(
                "bus has no subscribe_all; per-type subscription requires "
                "signal classes -- attach via the sidecar with a probed runtime")
        else:
            raise ValueError("object does not look like a bus (no subscribe_all/subscribe)")

        self._bus = bus
        self._active = True
        self.state.attached = True
        self.state.observing = True
        self.state.observe_only = self.observe_only
        self.state.bus_type = type(bus).__name__
        self.state.substrate_type = self.bridge.substrate.name
        if not self.observe_only and self.channel is not None:
            self.channel.bus = bus

    def detach(self) -> None:
        """Unsubscribe if the bus supports it; otherwise go inactive.

        Either way the connector stops processing and publishing immediately.
        """
        bus = self._bus
        unsubscribed = False
        if bus is not None and callable(getattr(bus, "unsubscribe", None)):
            try:
                bus.unsubscribe(self._handler)
                unsubscribed = True
            except Exception as exc:
                self.state.record_error(f"unsubscribe failed: {exc}")
        self._active = False
        self.state.attached = False
        self.state.observing = False
        if self.channel is not None:
            self.channel.bus = None
        if not unsubscribed and bus is not None:
            logger.info("bus does not support unsubscribe; connector marked inactive")
        self._bus = None

    # -- signal flow ------------------------------------------------------------

    def on_signal(self, signal: Any) -> None:
        """Bus entry point: filter, then process. Inactive => drop."""
        if not self._active:
            return
        # Never re-consume our own suggestions (no feedback loop).
        if getattr(signal, "kind", None) == "NeuralSuggestion" or \
                isinstance(signal, NeuralSuggestion):
            return
        kind = type(signal).__name__
        if isinstance(signal, dict):
            kind = str(signal.get("kind", "dict"))
        if self.allowed_signal_types is not None and kind not in self.allowed_signal_types:
            return
        try:
            self.process_signal(signal)
        except Exception as exc:
            self.state.record_error(f"processing {kind}: {exc}")
            logger.warning("sidecar failed to process %s: %s", kind, exc)

    def process_signal(self, signal: Any) -> Optional[Dict[str, Any]]:
        """Adapt, learn (Reactions), process, mirror, and maybe suggest."""
        adapted = self.bridge.adapter.to_nn_signal(signal)
        self.state.record_signal(adapted.kind)

        # Reactions teach first (the readout context is still the suggestion
        # that earned this feedback), then flow through as events like any other.
        if adapted.kind == "Reaction":
            self.bridge.react(adapted)
            self.state.record_reaction()

        result = self.bridge.process(adapted)
        if self.mirror is not None:
            vector = self.bridge.encoder.encode(adapted, heartbeat=True)
            self.mirror.mirror(signal, adapted, vector)

        # Reactions are feedback, not contexts worth suggesting on.
        if adapted.kind != "Reaction":
            self._suggest_from(result, adapted)
        self.state.telemetry_summary = {
            "events": self.bridge.telemetry.events,
            "readout_updates": self.bridge.telemetry.readout_updates,
            "recent_prediction_error": self.bridge.telemetry.recent_prediction_error,
        }
        return result

    def _suggest_from(self, result: Dict[str, Any], adapted: Any) -> None:
        suggestion = NeuralSuggestion(
            suggested_type=ACTION_SUGGESTION,
            payload={
                "action": result["suggested_action"],
                "desire": result["suggested_desire"],
                "scores": result["scores"],
                "pattern_key": result["pattern_key"],
            },
            confidence=result["confidence"],
            substrate_type=self.bridge.substrate.name,
            substrate_summary=self.bridge.substrate_summary(),
            reason=f"readout tendency after {adapted.kind}",
            source_signal_id=getattr(adapted, "id", None),
        )
        publish = (
            not self.observe_only
            and self.publish_suggestions
            and suggestion.confidence >= self.suggestion_threshold
        )
        if not publish and suggestion.confidence < self.suggestion_threshold:
            suggestion.safety_status = "held: below suggestion threshold"
        if self.observe_only:
            suggestion.safety_status = "held: observe-only mode"
        published = self.channel.submit(suggestion, publish=publish)
        self.state.record_suggestion(published)

    def publish_suggestion(self, suggestion: NeuralSuggestion) -> bool:
        """Explicitly publish a prepared suggestion (still suggestion-only)."""
        if self.observe_only:
            self.channel.reject(suggestion, "observe-only mode publishes nothing")
            self.state.record_rejection()
            return False
        published = self.channel.submit(suggestion, publish=True)
        self.state.record_suggestion(published)
        return published

    # -- inspection ---------------------------------------------------------------

    @property
    def active(self) -> bool:
        return self._active

    def snapshot(self) -> Dict[str, Any]:
        return {
            "active": self._active,
            "observe_only": self.observe_only,
            "publish_suggestions": self.publish_suggestions,
            "suggestion_threshold": self.suggestion_threshold,
            "allowed_signal_types": (list(self.allowed_signal_types)
                                     if self.allowed_signal_types else None),
            "state": self.state.to_dict(),
            "channel": self.channel.snapshot() if self.channel else None,
            "mirror": self.mirror.snapshot() if self.mirror else None,
        }
