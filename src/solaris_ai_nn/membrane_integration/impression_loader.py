"""Sensory impression loader -- read-only loading of membrane artifacts.

:class:`SensoryImpressionLoader` reads the membrane's sensory impressions and reports
(impression index, environmental membrane report, contamination, source pressure, and
membrane memory) read-only. Missing artifacts produce explicit warnings or blockers
depending on mode. Each loaded impression preserves its source-event reference and
exposes contamination, source pressure, receptor id, permeability status, and salience.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LoadedSensoryImpression:
    """One membrane sensory impression loaded for downstream consumption."""

    impression_id: str
    source_event_id: str
    source_id: str
    receptor_id: str
    impression_kind: str
    permeability_status: str
    salience: float = 0.0
    contamination: float = 0.0
    source_pressure: float = 0.0
    operator_pulse_weight: float = 0.0
    human_text_weight: float = 0.0
    grounding: str = "unknown"
    blocked: bool = False
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def clean(self) -> bool:
        return (not self.blocked) and self.contamination < 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "impression_id": self.impression_id,
            "source_event_id": self.source_event_id,
            "source_id": self.source_id, "receptor_id": self.receptor_id,
            "impression_kind": self.impression_kind,
            "permeability_status": self.permeability_status,
            "salience": round(self.salience, 3),
            "contamination": round(self.contamination, 3),
            "source_pressure": round(self.source_pressure, 3),
            "operator_pulse_weight": round(self.operator_pulse_weight, 3),
            "human_text_weight": round(self.human_text_weight, 3),
            "grounding": self.grounding, "blocked": self.blocked,
            "clean": self.clean,
        }


@dataclass
class ImpressionLoadResult:
    """The aggregate impression-load result + membrane report references."""

    impressions: List[LoadedSensoryImpression] = field(default_factory=list)
    membrane_present: bool = False
    impressions_present: bool = False
    membrane_report: Dict[str, Any] = field(default_factory=dict)
    contamination_report: Dict[str, Any] = field(default_factory=dict)
    source_pressure_report: Dict[str, Any] = field(default_factory=dict)
    membrane_memory: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)

    @property
    def clean_impressions(self) -> List[LoadedSensoryImpression]:
        return [i for i in self.impressions if i.clean]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "membrane_present": self.membrane_present,
            "impressions_present": self.impressions_present,
            "impression_count": len(self.impressions),
            "clean_impression_count": len(self.clean_impressions),
            "blocked_impression_count": sum(1 for i in self.impressions
                                            if i.blocked),
            "membrane_report_present": bool(self.membrane_report),
            "contamination_report_present": bool(self.contamination_report),
            "source_pressure_present": bool(self.source_pressure_report),
            "membrane_memory_present": bool(self.membrane_memory),
            "warnings": list(self.warnings), "blockers": list(self.blockers),
            "note": "loader is read-only; impressions preserve source-event "
                    "references and expose contamination/source-pressure/"
                    "receptor/permeability/salience",
        }


@dataclass
class SensoryImpressionLoader:
    """Loads membrane sensory impressions + reports (read-only)."""

    def load(self, state_dir: str, *, require_membrane: bool = False,
             require_impressions: bool = False) -> ImpressionLoadResult:
        result = ImpressionLoadResult()
        membrane = os.path.join(state_dir, "membrane")
        # "Membrane present" means real membrane *output* (impressions, a report,
        # or a receptor record) -- not merely the membrane directory, which the
        # integration layer itself creates for its own reports.
        result.membrane_present = any(os.path.exists(os.path.join(membrane, p))
            for p in ("impressions/SENSORY_IMPRESSIONS.jsonl",
                      "reports/ENVIRONMENTAL_MEMBRANE_REPORT.json",
                      "receptors"))

        jsonl = os.path.join(membrane, "impressions", "SENSORY_IMPRESSIONS.jsonl")
        if os.path.isfile(jsonl):
            result.impressions_present = True
            for line in self._read_lines(jsonl):
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                result.impressions.append(self._impression(d))

        result.membrane_report = self._read_json(
            os.path.join(membrane, "reports",
                         "ENVIRONMENTAL_MEMBRANE_REPORT.json"))
        result.contamination_report = self._read_json(
            os.path.join(membrane, "impressions",
                         "SENSORY_IMPRESSION_INDEX.json"))
        result.source_pressure_report = self._source_pressure(membrane)
        result.membrane_memory = self._read_json(
            os.path.join(membrane, "memory", "MEMBRANE_MEMORY.json"))

        if not result.membrane_present:
            msg = "no environmental membrane artifacts present"
            (result.blockers if require_membrane else result.warnings).append(
                msg)
        if not result.impressions_present:
            msg = "no sensory impressions present"
            (result.blockers if require_impressions else result.warnings).append(
                msg)
        return result

    @staticmethod
    def _read_lines(path: str) -> List[str]:
        try:
            with open(path, encoding="utf-8") as fh:
                return [l.strip() for l in fh if l.strip()]
        except Exception:
            return []

    @staticmethod
    def _read_json(path: str) -> Dict[str, Any]:
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}

    def _source_pressure(self, membrane: str) -> Dict[str, Any]:
        # The membrane writes source pressure under source_pressure/<run>.json.
        sp_dir = os.path.join(membrane, "source_pressure")
        if not os.path.isdir(sp_dir):
            return {}
        files = sorted(f for f in os.listdir(sp_dir) if f.endswith(".json"))
        if not files:
            return {}
        return self._read_json(os.path.join(sp_dir, files[-1]))

    @staticmethod
    def _impression(d: Dict[str, Any]) -> LoadedSensoryImpression:
        return LoadedSensoryImpression(
            impression_id=str(d.get("impression_id", "")),
            source_event_id=str(d.get("source_event_id", "")),
            source_id=str(d.get("source_id", "")),
            receptor_id=str(d.get("receptor_id", "")),
            impression_kind=str(d.get("impression_kind", "unknown")),
            permeability_status=str(d.get("permeability_status", "unknown")),
            salience=float(d.get("salience", 0.0) or 0.0),
            contamination=float(d.get("contamination", 0.0) or 0.0),
            source_pressure=float(d.get("source_pressure", 0.0) or 0.0),
            operator_pulse_weight=float(d.get("operator_pulse_weight", 0.0)
                                        or 0.0),
            human_text_weight=float(d.get("human_text_weight", 0.0) or 0.0),
            grounding=str(d.get("grounding", "unknown")),
            blocked=bool(d.get("blocked", False)), raw=dict(d))
