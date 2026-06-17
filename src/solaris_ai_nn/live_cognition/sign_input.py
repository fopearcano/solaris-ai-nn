"""Live sign input -- load eligible private signs from live semiogenesis.

:class:`SignInputLoader` reads the Prompt 70 live sign memory + private syntax graph
and returns the private signs eligible to seed cognition traces. Only born or stable
signs are eligible by default; contaminated signs are not eligible; rejected signs
remain visible as counterevidence; and human labels / debug gloss are loaded only as
non-ground-truth annotations. Signs remain internal/private structures, never human
words.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

_ELIGIBLE_STATUSES = ("born", "stable_candidate")
_COUNTEREVIDENCE_STATUSES = ("rejected", "weak", "suspended", "contaminated",
                             "label_dependent", "gloss_dependent",
                             "operator_dependent")


class SignInputStatus:
    LOADED = "loaded"
    MISSING_SIGN_MEMORY = "missing_sign_memory"
    NO_ELIGIBLE_SIGNS = "no_eligible_signs"
    SYNTHETIC = "synthetic"
    UNKNOWN = "unknown"

    ALL = (LOADED, MISSING_SIGN_MEMORY, NO_ELIGIBLE_SIGNS, SYNTHETIC, UNKNOWN)


@dataclass
class LiveSignInput:
    """One eligible (or context) private sign loaded for cognition."""

    sign_id: str
    private_token: str
    status: str
    linked_concept_ids: List[str] = field(default_factory=list)
    utility_score: float = 0.0
    source_distribution: Dict[str, int] = field(default_factory=dict)
    supporting_refs: List[str] = field(default_factory=list)
    contradicting_refs: List[str] = field(default_factory=list)
    contamination_findings: List[str] = field(default_factory=list)
    eligible: bool = False
    is_counterevidence: bool = False
    annotations: Dict[str, Any] = field(default_factory=dict)

    @property
    def contaminated(self) -> bool:
        return bool(self.contamination_findings)

    @property
    def is_operator_only(self) -> bool:
        srcs = set(self.source_distribution)
        return srcs == {"operator_pulse"} and bool(srcs)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sign_id": self.sign_id, "private_token": self.private_token,
            "status": self.status,
            "linked_concept_ids": list(self.linked_concept_ids),
            "utility_score": round(self.utility_score, 3),
            "source_distribution": dict(self.source_distribution),
            "supporting_refs": self.supporting_refs[:50],
            "contradicting_refs": self.contradicting_refs[:50],
            "contamination_findings": list(self.contamination_findings),
            "eligible": self.eligible,
            "is_counterevidence": self.is_counterevidence,
            "contaminated": self.contaminated,
            "annotations": dict(self.annotations),
            "annotations_are_ground_truth": False,
            "is_language": False,
        }


@dataclass
class SignInputResult:
    """The aggregate sign-input loading result."""

    status: str = SignInputStatus.UNKNOWN
    signs: List[LiveSignInput] = field(default_factory=list)
    sign_memory_path: str = ""
    private_syntax: Dict[str, Any] = field(default_factory=dict)
    semiogenesis_report_present: bool = False
    notes: List[str] = field(default_factory=list)

    @property
    def eligible(self) -> List[LiveSignInput]:
        return [s for s in self.signs if s.eligible]

    @property
    def counterevidence(self) -> List[LiveSignInput]:
        return [s for s in self.signs if s.is_counterevidence]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sign_input_status": self.status,
            "sign_memory_path": self.sign_memory_path,
            "semiogenesis_report_present": self.semiogenesis_report_present,
            "live_eligible_sign_count": len(self.eligible),
            "counterevidence_sign_count": len(self.counterevidence),
            "contaminated_sign_count": sum(1 for s in self.signs
                                           if s.contaminated),
            "private_syntax_relation_count": self.private_syntax.get(
                "live_private_syntax_relation_count", 0),
            "signs": [s.to_dict() for s in self.signs],
            "notes": list(self.notes),
            "note": "only born/stable signs are eligible; contaminated signs are "
                    "not eligible; rejected signs remain visible as "
                    "counterevidence; labels/gloss are non-ground-truth "
                    "annotations; signs are private internal structures, not "
                    "human words",
        }


@dataclass
class SignInputLoader:
    """Loads eligible private signs + counterevidence from live semiogenesis."""

    def load(self, state_dir: str) -> SignInputResult:
        result = SignInputResult()
        semio = os.path.join(state_dir, "semiogenesis")
        report = os.path.join(semio, "reports", "LIVE_SEMIOGENESIS_REPORT.json")
        result.semiogenesis_report_present = os.path.isfile(report)
        result.private_syntax = self._load_private_syntax(report)
        mem_path = os.path.join(semio, "signs", "LIVE_SIGN_MEMORY.json")
        result.sign_memory_path = mem_path
        if not os.path.isfile(mem_path):
            result.status = SignInputStatus.MISSING_SIGN_MEMORY
            result.notes.append("live sign memory not found")
            return result
        try:
            with open(mem_path, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            result.status = SignInputStatus.MISSING_SIGN_MEMORY
            result.notes.append("live sign memory could not be read")
            return result
        for rec in data.get("records", []):
            result.signs.append(self._sign_from_record(rec))
        result.status = (SignInputStatus.LOADED if result.eligible
                         else SignInputStatus.NO_ELIGIBLE_SIGNS)
        return result

    def from_records(self, records: List[Dict[str, Any]], *,
                     private_syntax: Dict[str, Any] = None,
                     synthetic: bool = False) -> SignInputResult:
        """Build sign input directly from sign records (demo / synthetic)."""
        result = SignInputResult(private_syntax=private_syntax or {})
        for rec in records:
            result.signs.append(self._sign_from_record(rec))
        if synthetic:
            result.status = SignInputStatus.SYNTHETIC
            result.notes.append("synthetic safe signs (demo mode)")
        else:
            result.status = (SignInputStatus.LOADED if result.eligible
                             else SignInputStatus.NO_ELIGIBLE_SIGNS)
        return result

    @staticmethod
    def _load_private_syntax(report_path: str) -> Dict[str, Any]:
        if not os.path.isfile(report_path):
            return {}
        try:
            with open(report_path, encoding="utf-8") as fh:
                sections = (json.load(fh).get("sections", {}) or {})
            return sections.get("private_syntax", {}) or {}
        except Exception:
            return {}

    @staticmethod
    def _sign_from_record(rec: Dict[str, Any]) -> LiveSignInput:
        status = str(rec.get("status", "unknown"))
        contamination = list(rec.get("contamination_findings", []) or [])
        eligible = status in _ELIGIBLE_STATUSES and not contamination
        annotations: Dict[str, Any] = {}
        if rec.get("debug_alias"):
            annotations["debug_alias"] = rec.get("debug_alias")
        return LiveSignInput(
            sign_id=str(rec.get("sign_id", "")),
            private_token=str(rec.get("private_token", "")),
            status=status,
            linked_concept_ids=list(rec.get("linked_concept_ids", []) or []),
            utility_score=float(rec.get("utility_score", 0.0) or 0.0),
            source_distribution=dict(rec.get("source_distribution", {}) or {}),
            supporting_refs=list(rec.get("supporting_refs", []) or []),
            contradicting_refs=list(rec.get("contradicting_refs", []) or []),
            contamination_findings=contamination,
            eligible=eligible,
            is_counterevidence=status in _COUNTEREVIDENCE_STATUSES,
            annotations=annotations)
