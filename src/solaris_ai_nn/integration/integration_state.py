"""IntegrationState -- the sidecar's own bookkeeping, serializable to JSON.

A single mutable record of everything the integration layer is doing: whether
it is attached, what it has observed, what it has suggested, and what went
wrong. The Inner MAP reads this (via the sidecar) so integration status is part
of the system's self-model. ``action_authority`` is a constant ``False`` --
the NN sidecar never holds it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class IntegrationState:
    """Counters and status flags for one sidecar attachment."""

    attached: bool = False
    observing: bool = False
    observe_only: bool = False
    compatibility_level: str = "unavailable"
    signals_observed: int = 0
    signals_by_type: Dict[str, int] = field(default_factory=dict)
    suggestions_produced: int = 0
    suggestions_published: int = 0
    suggestions_rejected: int = 0
    reactions_learned: int = 0
    errors: List[str] = field(default_factory=list)
    last_signal_ts: float = 0.0
    last_suggestion_ts: float = 0.0
    bus_type: Optional[str] = None
    conscience_summary: Optional[Dict[str, Any]] = None
    substrate_type: Optional[str] = None
    telemetry_summary: Dict[str, Any] = field(default_factory=dict)
    # The sidecar can never commit Actions inside Solaris_Ai. Constant.
    action_authority: bool = False

    # -- recording ------------------------------------------------------------

    def record_signal(self, kind: str) -> None:
        self.signals_observed += 1
        self.signals_by_type[kind] = self.signals_by_type.get(kind, 0) + 1
        self.last_signal_ts = time.time()

    def record_suggestion(self, published: bool) -> None:
        self.suggestions_produced += 1
        if published:
            self.suggestions_published += 1
        self.last_suggestion_ts = time.time()

    def record_rejection(self) -> None:
        self.suggestions_rejected += 1

    def record_reaction(self) -> None:
        self.reactions_learned += 1

    def record_error(self, message: str, cap: int = 50) -> None:
        self.errors.append(message)
        if len(self.errors) > cap:
            self.errors = self.errors[-cap:]

    # -- serialization ----------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attached": self.attached,
            "observing": self.observing,
            "observe_only": self.observe_only,
            "compatibility_level": self.compatibility_level,
            "signals_observed": self.signals_observed,
            "signals_by_type": dict(self.signals_by_type),
            "suggestions_produced": self.suggestions_produced,
            "suggestions_published": self.suggestions_published,
            "suggestions_rejected": self.suggestions_rejected,
            "reactions_learned": self.reactions_learned,
            "errors": list(self.errors),
            "error_count": len(self.errors),
            "last_signal_ts": self.last_signal_ts,
            "last_suggestion_ts": self.last_suggestion_ts,
            "bus_type": self.bus_type,
            "conscience_summary": self.conscience_summary,
            "substrate_type": self.substrate_type,
            "telemetry_summary": dict(self.telemetry_summary),
            "action_authority": False,  # invariant: the sidecar never holds it
        }
