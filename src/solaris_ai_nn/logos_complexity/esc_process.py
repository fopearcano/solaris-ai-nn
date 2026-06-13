"""Esc process -- an operational instability signal, not panic.

The :class:`EscProcess` watches for rising complexity/instability (repeated
unresolved high-severity tensions, runaway complexity, Mysterium saturation,
unsafe-sampling repetition, executive no-action loops, repair loops, symbol/
contradiction explosion, degraded identity continuity, persistent
stagnation) and proposes bounded *responses* -- stabilization, latent replay,
auto-regeneration diagnostics, executive inhibition, safe shutdown,
governance review, or marking unresolved Mysterium. Esc cannot bypass safety
and cannot execute real-world actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _num(d: Optional[Dict[str, Any]], key: str, default: float = 0.0) -> float:
    try:
        return float((d or {}).get(key, default) or 0.0)
    except (TypeError, ValueError):
        return default


class EscResponse:
    REQUEST_STABILIZATION = "request_stabilization_mode"
    REQUEST_LATENT_REPLAY = "request_latent_replay"
    REQUEST_AUTO_REGENERATION = "request_auto_regeneration_diagnostics"
    REQUEST_EXECUTIVE_INHIBITION = "request_executive_inhibition"
    REQUEST_SAFE_SHUTDOWN = "request_safe_shutdown"
    REQUEST_REVIEW = "request_governance_operator_review"
    MARK_UNRESOLVED_MYSTERIUM = "mark_unresolved_mysterium"

    ALL = (REQUEST_STABILIZATION, REQUEST_LATENT_REPLAY,
           REQUEST_AUTO_REGENERATION, REQUEST_EXECUTIVE_INHIBITION,
           REQUEST_SAFE_SHUTDOWN, REQUEST_REVIEW, MARK_UNRESOLVED_MYSTERIUM)


@dataclass
class EscalationState:
    """The current Esc instability picture."""

    triggered: bool = False
    level: float = 0.0  # [0, 1]
    triggers: List[str] = field(default_factory=list)
    responses: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "triggered": self.triggered,
            "level": round(self.level, 4),
            "triggers": list(self.triggers),
            "responses": list(self.responses),
        }


@dataclass
class EscProcess:
    """Detects instability and proposes bounded stabilization responses."""

    trigger_count: int = field(default=0, init=False)
    last_state: Optional[EscalationState] = field(default=None, init=False)

    def evaluate(self, context: Dict[str, Any]) -> EscalationState:
        ctx = dict(context or {})
        triggers: List[str] = []

        if _num(ctx, "unresolved_high_severity_count") >= 2:
            triggers.append("repeated unresolved high-severity tensions")
        if str((ctx.get("complexity") or {}).get("band")) == "overloaded":
            triggers.append("runaway complexity")
        if _num(ctx, "mysterium_pressure") >= 0.95:
            triggers.append("Mysterium saturation")
        ap = ctx.get("active_perception") or {}
        if _num(ap, "blocked_count") >= 10:
            triggers.append("repeated unsafe sampling")
        executive = ctx.get("executive") or {}
        if _num(executive, "no_safe_action_count") >= 5:
            triggers.append("executive no-action loop")
        ar = ctx.get("autoregeneration") or {}
        if _num(ar, "rollback_count") >= 3 \
                or _num(ar, "refused_repair_count") >= 10:
            triggers.append("repair loop")
        proto = ctx.get("proto_language") or {}
        if _num(proto, "symbol_count") > 500:
            triggers.append("symbol explosion")
        wm = ctx.get("world_model") or {}
        if len(wm.get("contradiction_edges") or []) >= 5:
            triggers.append("contradiction explosion")
        identity = ctx.get("identity") or {}
        if identity.get("continuity_score") is not None \
                and float(identity["continuity_score"]) < 0.5:
            triggers.append("degraded identity continuity")
        if ctx.get("stagnation_status") in ("stagnating", "inert") \
                and _num(ctx, "stagnation_windows") >= 5:
            triggers.append("persistent stagnation")

        level = min(1.0, len(triggers) / 4.0)
        triggered = len(triggers) >= 2 or (
            len(triggers) >= 1 and _num(ctx, "mysterium_pressure") >= 0.95)
        responses = self._responses(triggers, ctx) if triggered else []
        state = EscalationState(triggered=triggered, level=level,
                                triggers=triggers, responses=responses)
        if triggered:
            self.trigger_count += 1
        self.last_state = state
        return state

    def _responses(self, triggers: List[str],
                   ctx: Dict[str, Any]) -> List[str]:
        responses = [EscResponse.REQUEST_STABILIZATION]
        if "runaway complexity" in triggers or "repair loop" in triggers \
                or "contradiction explosion" in triggers:
            responses.append(EscResponse.REQUEST_AUTO_REGENERATION)
        if "Mysterium saturation" in triggers:
            responses.append(EscResponse.MARK_UNRESOLVED_MYSTERIUM)
            responses.append(EscResponse.REQUEST_LATENT_REPLAY)
        if "executive no-action loop" in triggers \
                or "repeated unsafe sampling" in triggers:
            responses.append(EscResponse.REQUEST_EXECUTIVE_INHIBITION)
        if "degraded identity continuity" in triggers:
            responses.append(EscResponse.REQUEST_REVIEW)
        # A critical ops state escalates to a safe-shutdown request only --
        # Esc never performs it; the ops watchdog decides.
        if ctx.get("emergency") or ctx.get("health_level") == "critical":
            responses.append(EscResponse.REQUEST_SAFE_SHUTDOWN)
        return responses

    def snapshot(self) -> Dict[str, Any]:
        return {
            "trigger_count": self.trigger_count,
            "last_state": (self.last_state.to_dict()
                           if self.last_state else None),
        }
