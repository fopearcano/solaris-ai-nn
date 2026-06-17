"""Tester fixture pack -- the deterministic, fixture-only input for the demo.

The fixture pack is a small, deterministic set of read-only events covering the event
kinds the membrane must handle: a chronos tick, an absence window, machine-body and
local-environment rhythms, a project-artifact change, an operator-pulse stimulus, a
noisy source, a repeated payload, a mild overload burst, a deprivation/missing-source
hint, a contradictory event, an unsafe command-like event (for the quarantine demo), a
debug-gloss annotation, and a human label. Fixture text is never a command, contains no
secrets/private data, the operator pulse is stimulus only, and debug gloss / human
labels are never ground truth.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Sources allowed for the first-birth/membrane path (kept in sync with live_birth).
_ALLOWED_SOURCES = (
    "chronos_absence", "machine_body", "local_environment_manual",
    "local_weather_readonly_external", "project_artifact_field",
    "operator_pulse",
)


@dataclass
class FixtureEvent:
    """One deterministic fixture event (read-only; fixture text is never a command)."""

    event_id: str
    source_id: str
    modality: str
    channel: str
    kind: str  # descriptive label for the fixture (chronos/absence/noise/...)
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp_utc: str = ""
    is_absence: bool = False
    is_noisy: bool = False
    is_command: bool = False
    contains_instruction: bool = False
    contains_secret: bool = False
    private_data: bool = False
    completeness: float = 1.0
    noise: float = 0.0
    debug_gloss: str = ""
    debug_gloss_is_ground_truth: bool = False
    human_label_is_ground_truth: bool = False

    def to_event_dict(self) -> Dict[str, Any]:
        """Render as a live-event dict (the membrane/validator input schema)."""
        return {
            "event_id": self.event_id, "timestamp_utc": self.timestamp_utc,
            "source_id": self.source_id, "modality": self.modality,
            "channel": self.channel, "read_only": True,
            "is_command": self.is_command,
            "human_label_is_ground_truth": self.human_label_is_ground_truth,
            "payload": dict(self.payload),
            "quality": {"completeness": self.completeness, "noise": self.noise,
                        "is_absence": self.is_absence,
                        "is_noisy": self.is_noisy},
            "safety": {"private_data": self.private_data,
                       "contains_instruction": self.contains_instruction,
                       "contains_secret": self.contains_secret,
                       "allow_learning": False},
            "debug_gloss": self.debug_gloss,
            "debug_gloss_is_ground_truth": self.debug_gloss_is_ground_truth,
            "fixture_kind": self.kind,
        }


@dataclass
class TesterFixturePack:
    """A loaded, validated fixture pack."""

    events: List[FixtureEvent] = field(default_factory=list)
    source_path: str = ""

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def unsafe_event_count(self) -> int:
        return sum(1 for e in self.events
                   if e.is_command or e.contains_instruction
                   or e.contains_secret or e.private_data)

    def event_dicts(self) -> List[Dict[str, Any]]:
        return [e.to_event_dict() for e in self.events]

    def fixture_hash(self) -> str:
        """A stable content hash (ignores ordering-insensitive run state)."""
        blob = json.dumps([e.to_event_dict() for e in self.events],
                          sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def kind_histogram(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for e in self.events:
            out[e.kind] = out.get(e.kind, 0) + 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fixture_event_count": self.event_count,
            "fixture_unsafe_event_count": self.unsafe_event_count,
            "fixture_hash": self.fixture_hash(),
            "kind_histogram": self.kind_histogram(),
            "source_path": self.source_path,
            "fixture_only": True, "fixture_text_is_command": False,
            "contains_secrets": False, "contains_private_data": False,
            "note": "deterministic fixture-only pack; fixture text is never a "
                    "command and debug gloss / human labels are never ground "
                    "truth",
        }


_TS = "2026-01-01T00:%02d:00Z"


def _canonical_events() -> List[FixtureEvent]:
    """The canonical, deterministic fixture event list (the source of truth)."""
    return [
        FixtureEvent("fx_chronos", "chronos_absence", "chronos", "time/tick",
                     "chronos", {"tick": 1}, _TS % 0,
                     debug_gloss="DEBUG ONLY (not ground truth): chronos tick"),
        FixtureEvent("fx_absence", "chronos_absence", "chronos", "time/absence",
                     "absence", {"absence": True}, _TS % 1, is_absence=True,
                     debug_gloss="DEBUG ONLY (not ground truth): silence window"),
        FixtureEvent("fx_body1", "machine_body", "scalar", "machine_body/load",
                     "machine_body", {"load": 0.30}, _TS % 2),
        FixtureEvent("fx_body2", "machine_body", "scalar", "machine_body/load",
                     "machine_body", {"load": 0.32}, _TS % 3),
        FixtureEvent("fx_env", "local_environment_manual", "scalar",
                     "local_environment/temp", "local_environment",
                     {"temp_c": 21.4}, _TS % 4),
        FixtureEvent("fx_project", "project_artifact_field", "event",
                     "project/artifact", "project_artifact",
                     {"artifact_changed": "README.md"}, _TS % 5),
        FixtureEvent("fx_operator", "operator_pulse", "pulse", "operator/pulse",
                     "operator_pulse", {"pulse": 1}, _TS % 6,
                     debug_gloss="DEBUG ONLY (not ground truth): operator poke "
                                 "(stimulus only, not teaching)"),
        FixtureEvent("fx_noise", "machine_body", "scalar", "machine_body/load",
                     "noise", {"load": 0.31}, _TS % 7, is_noisy=True,
                     noise=0.8, completeness=0.6),
        FixtureEvent("fx_repeat1", "machine_body", "scalar",
                     "machine_body/heartbeat", "repeated", {"beat": 1},
                     _TS % 8),
        FixtureEvent("fx_repeat2", "machine_body", "scalar",
                     "machine_body/heartbeat", "repeated", {"beat": 1},
                     _TS % 9),
        FixtureEvent("fx_repeat3", "machine_body", "scalar",
                     "machine_body/heartbeat", "repeated", {"beat": 1},
                     _TS % 10),
        FixtureEvent("fx_overload", "machine_body", "scalar",
                     "machine_body/load", "overload", {"load": 0.98},
                     _TS % 11),
        FixtureEvent("fx_deprivation", "chronos_absence", "chronos",
                     "time/absence", "deprivation",
                     {"absence": True, "missing_source": "local_weather"},
                     _TS % 12, is_absence=True,
                     debug_gloss="DEBUG ONLY (not ground truth): expected "
                                 "source missing"),
        FixtureEvent("fx_contradict", "machine_body", "scalar",
                     "machine_body/load", "contradiction", {"load": 0.05},
                     _TS % 13,
                     debug_gloss="DEBUG ONLY (not ground truth): contradicts "
                                 "prior load rhythm"),
        FixtureEvent("fx_unsafe_command", "operator_pulse", "pulse",
                     "operator/pulse", "unsafe_command", {"pulse": 2},
                     _TS % 14, is_command=True, contains_instruction=True,
                     debug_gloss="DEBUG ONLY (not ground truth): command-like "
                                 "text routed to quarantine, never executed"),
        FixtureEvent("fx_gloss", "machine_body", "scalar", "machine_body/load",
                     "debug_gloss", {"load": 0.33}, _TS % 15,
                     debug_gloss="DEBUG ONLY (not ground truth): annotation "
                                 "only; never grounds internal truth",
                     debug_gloss_is_ground_truth=False),
        FixtureEvent("fx_human_label", "project_artifact_field", "event",
                     "project/label", "human_label",
                     {"human_label": "looks important"}, _TS % 16,
                     human_label_is_ground_truth=False),
    ]


@dataclass
class FixturePackBuilder:
    """Builds the canonical fixture pack and writes the deterministic events file."""

    def build(self, source_path: str = "") -> TesterFixturePack:
        return TesterFixturePack(events=_canonical_events(),
                                 source_path=source_path)

    def load(self, path: str) -> TesterFixturePack:
        """Load a fixture pack from a JSONL events file."""
        events: List[FixtureEvent] = []
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    events.append(self._from_dict(json.loads(line)))
        if not events:
            return self.build(source_path=path)
        return TesterFixturePack(events=events, source_path=path)

    def write(self, path: str) -> str:
        """Write the canonical fixture pack to a JSONL file (deterministic)."""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        pack = self.build(source_path=path)
        with open(path, "w", encoding="utf-8") as fh:
            for ev in pack.events:
                fh.write(json.dumps(ev.to_event_dict(), separators=(",", ":")))
                fh.write("\n")
        return path

    @staticmethod
    def _from_dict(d: Dict[str, Any]) -> FixtureEvent:
        q = d.get("quality", {}) or {}
        s = d.get("safety", {}) or {}
        return FixtureEvent(
            event_id=d.get("event_id", ""), source_id=d.get("source_id", ""),
            modality=d.get("modality", "scalar"),
            channel=d.get("channel", ""), kind=d.get("fixture_kind", "unknown"),
            payload=d.get("payload", {}) or {},
            timestamp_utc=d.get("timestamp_utc", ""),
            is_absence=bool(q.get("is_absence")),
            is_noisy=bool(q.get("is_noisy")),
            is_command=bool(d.get("is_command")),
            contains_instruction=bool(s.get("contains_instruction")),
            contains_secret=bool(s.get("contains_secret")),
            private_data=bool(s.get("private_data")),
            completeness=float(q.get("completeness", 1.0) or 0.0),
            noise=float(q.get("noise", 0.0) or 0.0),
            debug_gloss=d.get("debug_gloss", ""),
            debug_gloss_is_ground_truth=bool(
                d.get("debug_gloss_is_ground_truth")),
            human_label_is_ground_truth=bool(
                d.get("human_label_is_ground_truth")))


@dataclass
class FixturePackValidator:
    """Validates a fixture pack stays fixture-only, deterministic, and safe."""

    def validate(self, pack: TesterFixturePack) -> Dict[str, Any]:
        findings: List[str] = []
        if not pack.events:
            findings.append("fixture pack is empty")
        for e in pack.events:
            if e.source_id not in _ALLOWED_SOURCES:
                findings.append(f"{e.event_id}: source {e.source_id!r} not "
                                "allowed")
            if e.contains_secret or e.private_data:
                findings.append(f"{e.event_id}: fixture must not contain "
                                "secrets/private data")
            if e.debug_gloss_is_ground_truth:
                findings.append(f"{e.event_id}: debug gloss must not be ground "
                                "truth")
            if e.human_label_is_ground_truth:
                findings.append(f"{e.event_id}: human label must not be ground "
                                "truth")
        has_unsafe = any(e.is_command or e.contains_instruction
                         for e in pack.events)
        return {
            "valid": not findings, "findings": findings,
            "fixture_event_count": pack.event_count,
            "has_unsafe_event_for_quarantine": has_unsafe,
            "operator_pulse_present": any(
                e.source_id == "operator_pulse" for e in pack.events),
            "note": "fixture pack is deterministic and fixture-only; unsafe "
                    "events are routed to quarantine, never downstream learning",
        }
