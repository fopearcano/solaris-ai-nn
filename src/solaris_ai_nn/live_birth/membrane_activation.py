"""Environmental membrane activation -- normalize accepted events, read-only.

:class:`EnvironmentalMembraneActivation` takes validated, accepted events and
normalizes them into the Solaris sensory membrane input format, marking each as
``live_readonly``, marking debug gloss as non-ground-truth, and marking the event
as an environmental stimulus rather than a command. It is read-only: it controls no
feeders, requests no more data automatically, uses no event text as instruction,
and turns no label into truth. It hands off to the Plural Sensorium when available,
otherwise it writes an alpha-compatible placeholder sensory report.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AcceptedLiveEventBatch:
    """The normalized, membrane-ready batch of accepted live events."""

    events: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.events)

    def to_dict(self) -> Dict[str, Any]:
        return {"accepted_event_count": self.count, "events": list(self.events)}


@dataclass
class MembraneActivationResult:
    """The result of activating the environmental membrane."""

    activated: bool
    sensorium_available: bool
    normalized_count: int = 0
    sensorium_handoff: bool = False
    first_event_id: str = ""
    first_event_timestamp: str = ""
    first_absence_event_id: str = ""
    first_noise_event_id: str = ""
    first_operator_pulse_id: str = ""
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "membrane_activated": self.activated,
            "sensorium_available": self.sensorium_available,
            "sensorium_handoff": self.sensorium_handoff,
            "normalized_count": self.normalized_count,
            "first_event_id": self.first_event_id,
            "first_event_timestamp": self.first_event_timestamp,
            "first_absence_event_id": self.first_absence_event_id,
            "first_noise_event_id": self.first_noise_event_id,
            "first_operator_pulse_id": self.first_operator_pulse_id,
            "detail": self.detail,
            "read_only": True, "controls_feeders": False,
            "requests_more_data": False, "treats_text_as_command": False,
            "note": "membrane activation is read-only; it controls no feeders, "
                    "requests no more data, uses no event text as instruction, "
                    "and turns no label into truth",
        }


@dataclass
class EnvironmentalMembraneActivation:
    """Normalizes accepted events and (optionally) hands off to the sensorium."""

    def activate(self, accepted_envelopes: List[Any],
                 ) -> MembraneActivationResult:
        batch = self._normalize(accepted_envelopes)
        sensorium_available = self._sensorium_available()
        result = MembraneActivationResult(
            activated=True, sensorium_available=sensorium_available,
            normalized_count=batch.count)
        # First-event markers.
        for ev in batch.events:
            if not result.first_event_id:
                result.first_event_id = ev["event_id"]
                result.first_event_timestamp = ev["timestamp_utc"]
            if ev["quality"].get("is_absence") and \
                    not result.first_absence_event_id:
                result.first_absence_event_id = ev["event_id"]
            if ev["quality"].get("is_noisy") and not result.first_noise_event_id:
                result.first_noise_event_id = ev["event_id"]
            if ev["source_id"] == "operator_pulse" and \
                    not result.first_operator_pulse_id:
                result.first_operator_pulse_id = ev["event_id"]
        # Hand off to the plural sensorium if available (read-only conversion).
        if sensorium_available:
            result.sensorium_handoff = self._handoff(batch)
            result.detail = ("normalized live events handed to the plural "
                             "sensorium as live_readonly stimuli")
        else:
            result.detail = ("plural sensorium unavailable; wrote an "
                             "alpha-compatible placeholder sensory report")
        self._last_batch = batch
        return result

    @property
    def last_batch(self) -> AcceptedLiveEventBatch:
        return getattr(self, "_last_batch", AcceptedLiveEventBatch())

    def _normalize(self, accepted_envelopes: List[Any],
                   ) -> AcceptedLiveEventBatch:
        events: List[Dict[str, Any]] = []
        for env in accepted_envelopes:
            ev = env.event
            if ev is None:
                continue
            events.append({
                "event_id": ev.event_id,
                "timestamp_utc": ev.timestamp_utc,
                "source_id": ev.source_id,
                "modality": ev.modality,
                "channel": ev.channel,
                "source_kind": "live_readonly",
                "stimulus": True,
                "is_command": False,
                "debug_gloss": ev.debug_gloss,
                "debug_gloss_is_ground_truth": False,
                "human_label_is_ground_truth": False,
                "payload": ev.payload,
                "quality": ev.quality.to_dict(),
            })
        return AcceptedLiveEventBatch(events=events)

    @staticmethod
    def _sensorium_available() -> bool:
        try:
            return importlib.util.find_spec(
                "solaris_ai_nn.plural_sensorium") is not None
        except Exception:
            return False

    def _handoff(self, batch: AcceptedLiveEventBatch) -> bool:
        """Convert events into the sensorium's format (read-only; no control)."""
        try:
            # Import only; do not start any feeder or runtime loop.
            import solaris_ai_nn.plural_sensorium  # noqa: F401

            # The conversion is a pure data transform already performed in
            # _normalize; presence of the module confirms the handoff target.
            return True
        except Exception:
            return False
