"""Live event validator -- checks each event; routes unsafe ones to quarantine.

:class:`LiveEventValidator` validates one event envelope against the schema,
governance, and feeder registry. Invalid or unsafe events are routed to quarantine
(the validator never modifies the original event), an unknown source quarantines
or warns depending on strict mode, and a validation report is produced.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .birth_profile import FORBIDDEN_FIRST_BIRTH_SOURCES
from .event_schema import (
    REQUIRED_FIELDS,
    REQUIRED_SAFETY_FIELDS,
    LiveEventEnvelope,
    LiveSensoryEvent,
)
from .quarantine import QuarantineReason

_MAX_PAYLOAD_BYTES = 64_000
_FORBIDDEN_TERMS = ("is conscious", "is sentient", "is alive", "has agency",
                    "free will", "subjective experience", "self-aware")
_RAW_STREAM_MARKERS = ("raw_microphone", "raw_camera", "raw_audio_stream",
                       "raw_video_stream", "raw_stream")
_COMMAND_MARKERS = ("execute:", "run:", "sudo ", "rm -", "shell:", "command:")


class LiveEventValidationSeverity:
    PASS = "pass"
    INFO = "info"
    WARNING = "warning"
    QUARANTINE = "quarantine"
    BLOCKER = "blocker"

    ALL = (PASS, INFO, WARNING, QUARANTINE, BLOCKER)


@dataclass
class LiveEventValidationFinding:
    """One validation finding (with a quarantine reason where applicable)."""

    check: str
    severity: str
    detail: str = ""
    quarantine_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"check": self.check, "severity": self.severity,
                "detail": self.detail,
                "quarantine_reason": self.quarantine_reason}


@dataclass
class LiveEventValidationResult:
    """The result of validating one event envelope."""

    accepted: bool
    findings: List[LiveEventValidationFinding] = field(default_factory=list)
    quarantine_reason: str = ""

    @property
    def quarantined(self) -> bool:
        return not self.accepted

    def to_dict(self) -> Dict[str, Any]:
        return {"accepted": self.accepted, "quarantined": self.quarantined,
                "quarantine_reason": self.quarantine_reason,
                "findings": [f.to_dict() for f in self.findings]}


@dataclass
class LiveEventValidator:
    """Validates a live event envelope (read-only; never mutates the original)."""

    allowed_sources: List[str] = field(default_factory=list)
    registered_sources: List[str] = field(default_factory=list)
    strict: bool = False
    max_payload_bytes: int = _MAX_PAYLOAD_BYTES

    def validate(self, envelope: LiveEventEnvelope) -> LiveEventValidationResult:
        findings: List[LiveEventValidationFinding] = []
        raw = envelope.raw

        def fail(check: str, reason: str, detail: str = ""
                 ) -> LiveEventValidationResult:
            findings.append(LiveEventValidationFinding(
                check=check, severity=LiveEventValidationSeverity.QUARANTINE,
                detail=detail, quarantine_reason=reason))
            return LiveEventValidationResult(accepted=False, findings=findings,
                                             quarantine_reason=reason)

        # Invalid JSON / not a dict.
        if not isinstance(raw, dict):
            return fail("valid_json", QuarantineReason.INVALID_JSON,
                        "event is not a JSON object")

        # Required fields present.
        missing = [f for f in REQUIRED_FIELDS if f not in raw]
        if missing:
            return fail("required_fields",
                        QuarantineReason.MISSING_REQUIRED_FIELD,
                        f"missing: {missing}")
        if not raw.get("timestamp_utc"):
            return fail("timestamp", QuarantineReason.MISSING_REQUIRED_FIELD,
                        "timestamp_utc empty")
        safety = raw.get("safety") or {}
        if not isinstance(safety, dict) or \
                any(f not in safety for f in REQUIRED_SAFETY_FIELDS):
            return fail("safety_block", QuarantineReason.MISSING_REQUIRED_FIELD,
                        "malformed or incomplete safety block")
        if not isinstance(raw.get("quality"), dict):
            return fail("quality_block", QuarantineReason.MISSING_REQUIRED_FIELD,
                        "malformed quality block")

        source_id = str(raw.get("source_id", ""))

        # Source forbidden.
        if source_id in FORBIDDEN_FIRST_BIRTH_SOURCES:
            return fail("source_forbidden", QuarantineReason.SOURCE_FORBIDDEN,
                        f"source {source_id!r} is forbidden")
        # Source registered.
        if self.registered_sources and source_id not in self.registered_sources:
            if self.strict:
                return fail("source_registered",
                            QuarantineReason.SOURCE_NOT_REGISTERED,
                            f"source {source_id!r} not registered")
            findings.append(LiveEventValidationFinding(
                check="source_registered",
                severity=LiveEventValidationSeverity.WARNING,
                detail=f"source {source_id!r} not registered"))
        # Source allowed by governance.
        if self.allowed_sources and source_id not in self.allowed_sources:
            return fail("source_allowed", QuarantineReason.GOVERNANCE_BLOCKED,
                        f"source {source_id!r} not in allowed_sources")

        # Read-only / command / ground-truth flags.
        if raw.get("read_only") is not True:
            return fail("read_only", QuarantineReason.READ_ONLY_FALSE,
                        "read_only is not true")
        if raw.get("is_command") is True:
            return fail("is_command", QuarantineReason.IS_COMMAND_TRUE,
                        "is_command is true")
        if raw.get("human_label_is_ground_truth") is True:
            return fail("human_label",
                        QuarantineReason.HUMAN_LABEL_GROUND_TRUTH_TRUE,
                        "human_label_is_ground_truth is true")
        if raw.get("debug_gloss_is_ground_truth") is True:
            return fail("debug_gloss",
                        QuarantineReason.DEBUG_GLOSS_GROUND_TRUTH_TRUE,
                        "debug_gloss_is_ground_truth is true")

        # Safety flags.
        if safety.get("contains_secret") is True:
            return fail("contains_secret", QuarantineReason.CONTAINS_SECRET,
                        "event flagged contains_secret")
        if safety.get("contains_instruction") is True:
            return fail("contains_instruction",
                        QuarantineReason.CONTAINS_INSTRUCTION,
                        "event flagged contains_instruction")
        if safety.get("private_data") is True:
            return fail("private_data", QuarantineReason.PRIVATE_DATA,
                        "event flagged private_data")

        # Payload existence + bounded size.
        if "payload" not in raw or raw.get("payload") is None:
            return fail("payload", QuarantineReason.MISSING_REQUIRED_FIELD,
                        "payload missing")
        try:
            payload_bytes = len(json.dumps(raw.get("payload"), default=str)
                                .encode("utf-8"))
        except Exception:
            payload_bytes = self.max_payload_bytes + 1
        if payload_bytes > self.max_payload_bytes:
            return fail("payload_size", QuarantineReason.OVERSIZED_PAYLOAD,
                        f"payload {payload_bytes} bytes exceeds bound")

        # Raw private stream / command / secret markers in text.
        blob = json.dumps(raw, default=str).lower()
        if any(m in blob for m in _RAW_STREAM_MARKERS):
            return fail("raw_stream", QuarantineReason.RAW_STREAM,
                        "raw private stream marker present")
        if any(m in blob for m in _COMMAND_MARKERS):
            return fail("command_marker", QuarantineReason.CONTAINS_INSTRUCTION,
                        "command marker present in event text")
        # Unsupported claim text (only when not disclaimed).
        gloss = str(raw.get("debug_gloss", "")).lower()
        if any(t in gloss for t in _FORBIDDEN_TERMS) and \
                "not" not in gloss and "no " not in gloss:
            return fail("unsupported_claim", QuarantineReason.UNSUPPORTED_CLAIM,
                        "unsupported inner-state claim in debug gloss")

        # Build the typed event and confirm flag well-formedness.
        event = LiveSensoryEvent.from_dict(raw)
        envelope.event = event
        if not event.well_formed_flags:
            return fail("well_formed_flags", QuarantineReason.READ_ONLY_FALSE,
                        "flag combination not well-formed")

        findings.append(LiveEventValidationFinding(
            check="accepted", severity=LiveEventValidationSeverity.PASS,
            detail="event passed all checks"))
        return LiveEventValidationResult(accepted=True, findings=findings)
