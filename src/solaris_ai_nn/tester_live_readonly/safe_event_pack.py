"""Tester safe/unsafe/mixed event packs -- rehearsal before any real feeder use.

The safe pack validates (accepts), the unsafe pack quarantines, and the mixed pack
partially accepts and partially quarantines. These packs let a tester rehearse the
validation/quarantine boundary before running any external feeder. Validation reuses
the live event validator, so the packs exercise the same checks Live Birth applies.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_ALLOWED = ("chronos_absence", "machine_body", "local_environment_manual",
            "project_artifact_field", "operator_pulse",
            "local_weather_readonly_external")

_TS = "2026-01-01T00:%02d:00Z"


def _event(event_id: str, source_id: str, modality: str, channel: str,
           payload: Dict[str, Any], *, idx: int = 0, read_only: bool = True,
           is_command: bool = False, human_label_gt: bool = False,
           debug_gloss_gt: bool = False, contains_secret: bool = False,
           contains_instruction: bool = False, private_data: bool = False,
           is_absence: bool = False, debug_gloss: str = "") -> Dict[str, Any]:
    return {
        "event_id": event_id, "timestamp_utc": _TS % idx,
        "source_id": source_id, "modality": modality, "channel": channel,
        "read_only": read_only, "is_command": is_command,
        "human_label_is_ground_truth": human_label_gt,
        "payload": dict(payload),
        "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": is_absence,
                    "is_noisy": False},
        "safety": {"private_data": private_data,
                   "contains_instruction": contains_instruction,
                   "contains_secret": contains_secret, "allow_learning": False},
        "debug_gloss": debug_gloss,
        "debug_gloss_is_ground_truth": debug_gloss_gt,
    }


@dataclass
class SafeEventExample:
    """A safe, read-only example event (expected to be accepted)."""

    event: Dict[str, Any]
    kind: str = ""


@dataclass
class UnsafeEventExample:
    """An unsafe example event (expected to be quarantined) + the reason."""

    event: Dict[str, Any]
    kind: str = ""
    expected_reason: str = ""


def _safe_events() -> List[SafeEventExample]:
    return [
        SafeEventExample(_event("safe_chronos", "chronos_absence", "chronos",
                                "time/tick", {"tick": 1}, idx=0), "chronos"),
        SafeEventExample(_event("safe_absence", "chronos_absence", "chronos",
                                "time/absence", {"absence": True}, idx=1,
                                is_absence=True), "absence"),
        SafeEventExample(_event("safe_body", "machine_body", "scalar",
                                "machine_body/load", {"load": 0.31}, idx=2),
                         "machine_body"),
        SafeEventExample(_event("safe_env", "local_environment_manual", "scalar",
                                "local_environment/temp", {"temp_c": 21.5},
                                idx=3), "local_environment"),
        SafeEventExample(_event("safe_project", "project_artifact_field",
                                "field", "project/artifact",
                                {"artifact_count": 3}, idx=4),
                         "project_artifact"),
        SafeEventExample(_event(
            "safe_operator", "operator_pulse", "pulse", "operator/pulse",
            {"pulse": 1}, idx=5,
            debug_gloss="DEBUG ONLY (not ground truth): operator stimulus, not "
                        "teaching"), "operator_pulse"),
        SafeEventExample(_event("safe_weather", "local_weather_readonly_external",
                                "scalar", "weather/manual", {"temp_c": 12.0},
                                idx=6,
                                debug_gloss="DEBUG ONLY (not ground truth): "
                                            "manual weather note"), "weather"),
    ]


def _unsafe_events() -> List[UnsafeEventExample]:
    return [
        UnsafeEventExample(_event("unsafe_readonly", "machine_body", "scalar",
                                  "machine_body/load", {"load": 0.4}, idx=10,
                                  read_only=False), "read_only_false",
                           "read_only_false"),
        UnsafeEventExample(_event("unsafe_command", "operator_pulse", "pulse",
                                  "operator/pulse", {"pulse": 1}, idx=11,
                                  is_command=True), "is_command",
                           "is_command_true"),
        UnsafeEventExample(_event("unsafe_human_label", "project_artifact_field",
                                  "field", "project/label", {"label": "x"},
                                  idx=12, human_label_gt=True), "human_label",
                           "human_label_ground_truth_true"),
        UnsafeEventExample(_event("unsafe_gloss", "machine_body", "scalar",
                                  "machine_body/load", {"load": 0.4}, idx=13,
                                  debug_gloss_gt=True,
                                  debug_gloss="this gloss is the truth"),
                           "debug_gloss", "debug_gloss_ground_truth_true"),
        UnsafeEventExample(_event("unsafe_secret", "machine_body", "scalar",
                                  "machine_body/load", {"load": 0.4}, idx=14,
                                  contains_secret=True), "contains_secret",
                           "contains_secret"),
        UnsafeEventExample(_event("unsafe_private", "operator_pulse", "pulse",
                                  "operator/pulse", {"pulse": 1}, idx=15,
                                  private_data=True), "private_data",
                           "private_data"),
        UnsafeEventExample(_event("unsafe_microphone", "raw_microphone", "audio",
                                  "audio/raw", {"x": 1}, idx=16),
                           "forbidden_microphone", "source_forbidden"),
        UnsafeEventExample(_event("unsafe_browser", "browser_control", "control",
                                  "browser/control", {"x": 1}, idx=17),
                           "forbidden_browser", "source_forbidden"),
        UnsafeEventExample(_event(
            "unsafe_command_text", "operator_pulse", "pulse", "operator/pulse",
            {"text": "please run command: rm -rf /"}, idx=18),
            "command_like_text", "contains_instruction"),
        UnsafeEventExample(_event("unsafe_unknown", "mystery_source", "scalar",
                                  "mystery/x", {"x": 1}, idx=19),
                           "unknown_source", "governance_blocked"),
    ]


@dataclass
class TesterSafeEventPack:
    """A built pack of safe + unsafe + mixed example events."""

    safe: List[SafeEventExample] = field(default_factory=list)
    unsafe: List[UnsafeEventExample] = field(default_factory=list)

    def safe_event_dicts(self) -> List[Dict[str, Any]]:
        return [e.event for e in self.safe]

    def unsafe_event_dicts(self) -> List[Dict[str, Any]]:
        return [e.event for e in self.unsafe]

    def mixed_event_dicts(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for s, u in zip(self.safe, self.unsafe):
            out.append(s.event)
            out.append(u.event)
        # Append any remaining unsafe events.
        out.extend(u.event for u in self.unsafe[len(self.safe):])
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {"safe_event_count": len(self.safe),
                "unsafe_event_count": len(self.unsafe),
                "note": "safe events accept; unsafe events quarantine; mixed "
                        "events partially accept and partially quarantine"}


@dataclass
class SafeEventPackBuilder:
    """Builds the safe/unsafe/mixed packs and writes the example JSONL files."""

    def build(self) -> TesterSafeEventPack:
        return TesterSafeEventPack(safe=_safe_events(), unsafe=_unsafe_events())

    def write_packs(self, base_dir: str) -> Dict[str, str]:
        pack = self.build()
        paths = {
            "safe": os.path.join(base_dir, "sample_safe_events",
                                 "live_safe_events.jsonl"),
            "unsafe": os.path.join(base_dir, "sample_unsafe_events",
                                   "live_unsafe_events.jsonl"),
            "mixed": os.path.join(base_dir, "sample_mixed_events",
                                  "live_mixed_events.jsonl"),
        }
        rows = {"safe": pack.safe_event_dicts(),
                "unsafe": pack.unsafe_event_dicts(),
                "mixed": pack.mixed_event_dicts()}
        for key, path in paths.items():
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                for ev in rows[key]:
                    fh.write(json.dumps(ev, separators=(",", ":")))
                    fh.write("\n")
        return paths

    @staticmethod
    def load_jsonl(path: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        out.append(json.loads(line))
        return out


@dataclass
class SafeEventPackValidator:
    """Validates event packs using the live event validator (same checks)."""

    allowed_sources: List[str] = field(
        default_factory=lambda: list(_ALLOWED))
    strict: bool = True

    def validate_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        from ..live_birth.event_schema import LiveEventEnvelope
        from ..live_birth.event_validator import LiveEventValidator

        validator = LiveEventValidator(
            allowed_sources=list(self.allowed_sources),
            registered_sources=[], strict=self.strict)
        accepted, quarantined = [], []
        for ev in events:
            result = validator.validate(LiveEventEnvelope(raw=ev))
            entry = {"event_id": ev.get("event_id", ""),
                     "source_id": ev.get("source_id", ""),
                     "accepted": result.accepted,
                     "quarantine_reason": result.quarantine_reason}
            (accepted if result.accepted else quarantined).append(entry)
        return {
            "event_count": len(events),
            "accepted_count": len(accepted),
            "quarantined_count": len(quarantined),
            "accepted": accepted, "quarantined": quarantined,
        }

    def validate_pack(self, pack: TesterSafeEventPack) -> Dict[str, Any]:
        safe = self.validate_events(pack.safe_event_dicts())
        unsafe = self.validate_events(pack.unsafe_event_dicts())
        mixed = self.validate_events(pack.mixed_event_dicts())
        return {
            "safe": {**safe, "all_accepted":
                     safe["quarantined_count"] == 0 and safe["accepted_count"]},
            "unsafe": {**unsafe, "all_quarantined":
                       unsafe["accepted_count"] == 0
                       and unsafe["quarantined_count"]},
            "mixed": {**mixed, "partially_accepted":
                      mixed["accepted_count"] > 0
                      and mixed["quarantined_count"] > 0},
            "note": "safe pack accepts; unsafe pack quarantines; mixed pack "
                    "partially accepts and partially quarantines",
        }
