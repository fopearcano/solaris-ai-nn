"""Tester feeder registry templates -- descriptive metadata for external feeders.

The feeder registry is descriptive metadata only. Every feeder is external, read-only,
and started by the tester/operator; Solaris never controls one. Any record with
``solaris_may_control=true`` or ``started_by_solaris=true`` is invalid, and an unknown
feeder is blocked by default.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TesterFeederTemplateRecord:
    """One descriptive external-feeder record (no control metadata)."""

    feeder_id: str
    source_id: str
    modality: str
    channel: str
    description: str
    writes_to: str
    privacy_level: str = "low"
    expected_event_rate: str = "low"
    read_only: bool = True
    started_externally: bool = True
    solaris_may_control: bool = False
    allowed: bool = True
    limitations: List[str] = field(default_factory=list)
    tester_instructions: str = ""
    safety_notes: str = ""

    @property
    def valid(self) -> bool:
        return (self.read_only and self.started_externally
                and not self.solaris_may_control)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feeder_id": self.feeder_id, "source_id": self.source_id,
            "modality": self.modality, "channel": self.channel,
            "description": self.description, "writes_to": self.writes_to,
            "read_only": self.read_only,
            "started_externally": self.started_externally,
            "started_by_solaris": False,
            "solaris_may_control": self.solaris_may_control,
            "privacy_level": self.privacy_level,
            "expected_event_rate": self.expected_event_rate,
            "allowed": self.allowed,
            "limitations": list(self.limitations),
            "tester_instructions": self.tester_instructions,
            "safety_notes": self.safety_notes,
        }


@dataclass
class TesterFeederRegistryTemplate:
    """A loaded/parsed tester feeder registry (descriptive metadata only)."""

    feeders: List[TesterFeederTemplateRecord] = field(default_factory=list)

    @property
    def invalid_records(self) -> List[TesterFeederTemplateRecord]:
        return [f for f in self.feeders if not f.valid]

    def source_ids(self) -> List[str]:
        return [f.source_id for f in self.feeders]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feeders": [f.to_dict() for f in self.feeders],
            "feeder_count": len(self.feeders),
            "invalid_record_count": len(self.invalid_records),
            "note": "descriptive metadata only; all feeders are external, "
                    "read-only, operator-started, and never controlled by "
                    "Solaris. Unknown feeders are blocked by default.",
        }


_SPECS = (
    ("chronos_absence", "chronos", "time/absence",
     "wall-clock ticks and absence/silence markers", "low",
     "Run tools/external_feeders/chronos_absence_feeder.py with --out pointing "
     "at the inbox.",
     "Writes only the current UTC time and manual absence reasons."),
    ("machine_body", "scalar", "machine_body/load",
     "local machine scalar state (cpu/mem/disk percent) read-only", "low",
     "Run tools/external_feeders/machine_body_feeder.py with --out.",
     "No process command lines, no usernames, no hardware control."),
    ("local_environment_manual", "scalar", "local_environment/manual",
     "manually-entered local environment scalars (temp/light/noise)", "low",
     "Run tools/external_feeders/manual_environment_writer.py and type values.",
     "No raw microphone/camera; weather notes are annotation only."),
    ("project_artifact_field", "field", "project/artifact",
     "read-only project artifact presence/count/mtime (no file content)", "low",
     "Run tools/external_feeders/project_artifact_feeder.py with --dir.",
     "No file content, no Git, no full-repo scan, no secrets."),
    ("operator_pulse", "pulse", "operator/pulse",
     "operator short note as a stimulus event (never a command)", "low",
     "Run tools/external_feeders/operator_pulse_writer.py --note '...'.",
     "Operator note is stimulus only; never a teaching label or command."),
)

_OPTIONAL_SPEC = (
    "local_weather_readonly_external", "scalar", "weather/manual",
    "operator-provided read-only local weather scalars (manual)", "low",
    "Run tools/external_feeders/local_weather_manual_writer.py and type values.",
    "Manually entered; no network calls; annotation only.")


@dataclass
class TesterFeederTemplateBuilder:
    """Builds, writes, and loads the tester feeder registry template."""

    def build(self, include_optional: bool = True) -> TesterFeederRegistryTemplate:
        specs = list(_SPECS)
        if include_optional:
            specs.append(_OPTIONAL_SPEC)
        feeders = []
        for (source_id, modality, channel, desc, privacy, instr,
             safety) in specs:
            feeders.append(TesterFeederTemplateRecord(
                feeder_id=f"feeder_{source_id}", source_id=source_id,
                modality=modality, channel=channel, description=desc,
                writes_to=f".solaris_ai_nn_live/inbox/{source_id}.jsonl",
                privacy_level=privacy, expected_event_rate="low",
                limitations=["read-only; Solaris never starts, stops, "
                             "schedules, or controls this feeder"],
                tester_instructions=instr, safety_notes=safety))
        return TesterFeederRegistryTemplate(feeders=feeders)

    def write_template(self, path: str) -> str:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.build().to_dict(), fh, indent=2)
        return path

    def write_live_registry(self, state_dir: str, *,
                            overwrite: bool = False) -> Dict[str, Any]:
        """Write the template into the live feeders dir if absent.

        Never overwrites a customized registry unless ``overwrite`` is set.
        """
        from ..live_birth.feeder_registry import REGISTRY_FILENAME

        feeders_dir = os.path.join(state_dir, "feeders")
        os.makedirs(feeders_dir, exist_ok=True)
        path = os.path.join(feeders_dir, REGISTRY_FILENAME)
        existed = os.path.isfile(path)
        if existed and not overwrite:
            return {"path": path, "written": False, "existed": True,
                    "note": "feeder registry already present; not overwritten "
                            "(customized registry is preserved)"}
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.build().to_dict(), fh, indent=2)
        return {"path": path, "written": True, "existed": existed,
                "note": "wrote tester feeder registry template (descriptive "
                        "metadata only; all feeders external and uncontrolled)"}

    @staticmethod
    def load(state_dir: str) -> TesterFeederRegistryTemplate:
        from ..live_birth.feeder_registry import REGISTRY_FILENAME

        path = os.path.join(state_dir, "feeders", REGISTRY_FILENAME)
        if not os.path.isfile(path):
            return TesterFeederRegistryTemplate(feeders=[])
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            return TesterFeederRegistryTemplate(feeders=[])
        feeders = []
        for f in data.get("feeders", []):
            feeders.append(TesterFeederTemplateRecord(
                feeder_id=f.get("feeder_id", ""),
                source_id=f.get("source_id", ""),
                modality=f.get("modality", ""), channel=f.get("channel", ""),
                description=f.get("description", ""),
                writes_to=f.get("writes_to", ""),
                privacy_level=f.get("privacy_level", "low"),
                expected_event_rate=f.get("expected_event_rate", "low"),
                read_only=bool(f.get("read_only", True)),
                started_externally=bool(f.get("started_externally", True)),
                solaris_may_control=bool(f.get("solaris_may_control", False))
                or bool(f.get("started_by_solaris", False)),
                allowed=bool(f.get("allowed", True)),
                limitations=list(f.get("limitations", [])),
                tester_instructions=f.get("tester_instructions", ""),
                safety_notes=f.get("safety_notes", "")))
        return TesterFeederRegistryTemplate(feeders=feeders)
