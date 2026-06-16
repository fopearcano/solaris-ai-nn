"""Baseline capability map -- what is implemented/available, with evidence.

:class:`BaselineCapabilityMap` records, per capability area, whether it is
available / validated / experimental / blocked / missing. "Capability" means an
implemented module with available evidence -- NOT intelligence, understanding, or
any inner state. Every record carries its limitations and evidence refs, and a
capability is not stated as validated without validation evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class CapabilityStatus:
    AVAILABLE = "available"
    VALIDATED = "validated"
    VALIDATED_WITH_WARNINGS = "validated_with_warnings"
    EXPERIMENTAL = "experimental"
    BLOCKED = "blocked"
    MISSING = "missing"
    UNKNOWN = "unknown"

    ALL = (AVAILABLE, VALIDATED, VALIDATED_WITH_WARNINGS, EXPERIMENTAL, BLOCKED,
           MISSING, UNKNOWN)

    VALIDATED_KINDS = (VALIDATED, VALIDATED_WITH_WARNINGS)


# Capability area -> the package that implements it (for availability checks).
CAPABILITY_AREAS = (
    ("plural_sensorium", "plural_sensorium"),
    ("live_field_intake", "live_field"),
    ("feeder_sdk", "feeder_sdk"),
    ("sensorium_differentiation", "sensorium_lab"),
    ("perceptual_metabolism", "perceptual_metabolism"),
    ("perceptual_ontogenesis", "perceptual_ontogenesis"),
    ("semiogenesis", "semiogenesis"),
    ("sensorium_cognition", "sensorium_cognition"),
    ("self_boundary", "self_boundary"),
    ("desire_formation", "desire_formation"),
    ("action_reaction", "action_reaction"),
    ("developmental_life", "developmental_life"),
    ("developmental_soak", "developmental_soak"),
    ("replication_falsification", "developmental_replication"),
    ("architecture_evolution", "architecture_evolution"),
    ("experiment_compiler", "experiment_compiler"),
    ("implementation_intake", "implementation_intake"),
    ("post_merge_assimilation", "post_merge_assimilation"),
    ("evaluation", "evaluation"),
    ("safety_invariants", "safety_invariants"),
    ("operator_console", "operator_console"),
    ("inner_map", "inner_map"),
)


@dataclass
class CapabilityRecord:
    """One capability area's status + limitations + evidence refs."""

    area: str
    status: str
    evidence_refs: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"area": self.area, "status": self.status,
                "evidence_refs": list(self.evidence_refs),
                "limitations": list(self.limitations), "detail": self.detail,
                "means_implemented_not_intelligence": True}


@dataclass
class BaselineCapabilityMap:
    """Maps capability areas to availability/validation status (conservatively)."""

    records: Dict[str, CapabilityRecord] = field(default_factory=dict)

    def build(self, *, evidence: Optional[Dict[str, Dict[str, Any]]] = None,
              coverage_matrix: Optional[Dict[str, Any]] = None,
              ) -> "BaselineCapabilityMap":
        evidence = evidence or {}
        for area, module in CAPABILITY_AREAS:
            available = self._importable(f"solaris_ai_nn.{module}")
            ev = evidence.get(area, {})
            refs = list(ev.get("evidence_refs", []))
            limitations = list(ev.get("limitations", []))
            declared = ev.get("status")
            if declared in CapabilityStatus.ALL:
                status = declared
                # Never claim validated without validation evidence refs.
                if status in CapabilityStatus.VALIDATED_KINDS and not refs:
                    status = CapabilityStatus.AVAILABLE
                    limitations.append("claimed validated without evidence "
                                       "refs; downgraded to available")
            elif not available:
                status = CapabilityStatus.MISSING
            else:
                status = (CapabilityStatus.AVAILABLE if not refs
                          else CapabilityStatus.EXPERIMENTAL)
            self.records[area] = CapabilityRecord(
                area=area, status=status, evidence_refs=refs,
                limitations=limitations,
                detail="implemented module available" if available
                else "module not importable")
        return self

    @staticmethod
    def _importable(module: str) -> bool:
        import importlib

        try:
            importlib.import_module(module)
            return True
        except Exception:
            return False

    def counts(self) -> Dict[str, int]:
        out = {s: 0 for s in CapabilityStatus.ALL}
        for r in self.records.values():
            out[r.status] = out.get(r.status, 0) + 1
        return out

    @property
    def validated_count(self) -> int:
        return sum(1 for r in self.records.values()
                   if r.status in CapabilityStatus.VALIDATED_KINDS)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability_count": len(self.records),
            "validated_capability_count": self.validated_count,
            "counts": self.counts(),
            "records": {a: r.to_dict() for a, r in self.records.items()},
            "note": "capability means an implemented module with available "
                    "evidence, not intelligence, understanding, or inner state",
        }
