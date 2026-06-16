"""Experiment-compiler input manifest -- declare the evidence sources read.

:class:`ExperimentCompilerInputManifest` declares the source artifacts the
compiler reads (architecture-evolution report, branch manifest, experiment queue,
module inventory, promotion gate result, ablation plan, variant proposal,
falsification report, replication matrix, soak autopsy, safety invariant report,
operator note). It reads existing artifacts only; a missing input is a warning or
a blocker depending on severity. Falsified evidence is preserved, and the
operator note never overrides safety evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class CompilerInputStatus:
    PRESENT = "present"
    MISSING_WARNING = "missing_warning"
    MISSING_BLOCKER = "missing_blocker"
    PROVIDED = "provided"

    ALL = (PRESENT, MISSING_WARNING, MISSING_BLOCKER, PROVIDED)


# Each source: (id, is_critical). Critical-missing => blocker, else warning.
_SOURCE_SPEC = (
    ("architecture_evolution_report", False),
    ("branch_manifest", False),
    ("experiment_queue", False),
    ("module_inventory", False),
    ("promotion_gate_result", False),
    ("ablation_plan", False),
    ("variant_proposal", True),
    ("falsification_report", False),
    ("replication_matrix", False),
    ("soak_autopsy", False),
    ("safety_invariant_report", True),
    ("operator_note", False),
)


@dataclass
class CompilerInputSource:
    """One declared input source + its presence status and payload."""

    source_id: str
    status: str = CompilerInputStatus.MISSING_WARNING
    critical: bool = False
    path: str = ""
    payload: Any = None
    detail: str = ""

    @property
    def present(self) -> bool:
        return self.status in (CompilerInputStatus.PRESENT,
                               CompilerInputStatus.PROVIDED)

    def to_dict(self) -> Dict[str, Any]:
        return {"source_id": self.source_id, "status": self.status,
                "critical": self.critical, "path": self.path,
                "present": self.present, "detail": self.detail,
                "has_payload": self.payload is not None}


@dataclass
class ExperimentCompilerInputManifest:
    """Declares + records the evidence sources the compiler reads."""

    sources: Dict[str, CompilerInputSource] = field(default_factory=dict)
    proposals: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.sources:
            for sid, critical in _SOURCE_SPEC:
                status = (CompilerInputStatus.MISSING_BLOCKER if critical
                          else CompilerInputStatus.MISSING_WARNING)
                self.sources[sid] = CompilerInputSource(
                    source_id=sid, status=status, critical=critical,
                    detail="not supplied")

    def provide(self, source_id: str, payload: Any, *, path: str = "",
                detail: str = "") -> CompilerInputSource:
        critical = self.sources[source_id].critical if source_id in \
            self.sources else False
        src = CompilerInputSource(
            source_id=source_id, status=CompilerInputStatus.PROVIDED,
            critical=critical, path=path, payload=payload,
            detail=detail or "provided in-memory")
        self.sources[source_id] = src
        return src

    def add_proposals(self, proposals: List[Dict[str, Any]]) -> None:
        """Register architecture proposals (dicts) for the reader to compile."""
        for p in proposals or []:
            self.proposals.append(dict(p))
        if proposals:
            self.provide("variant_proposal", list(self.proposals),
                         detail=f"{len(self.proposals)} proposal(s)")

    def discover(self, state_dir: str) -> None:
        """Discover known report artifacts under ``state_dir`` (reads only)."""
        import os

        filenames = {
            "architecture_evolution_report":
                "ARCHITECTURE_EVOLUTION_REPORT.json",
            "falsification_report": "FALSIFICATION_REPORT.md",
            "replication_matrix": "REPLICATION_MATRIX.md",
            "soak_autopsy": "POST_RUN_AUTOPSY.md",
        }
        if not os.path.isdir(state_dir):
            return
        found: Dict[str, str] = {}
        for root, _dirs, files in os.walk(state_dir):
            for sid, fname in filenames.items():
                if fname in files and sid not in found:
                    found[sid] = os.path.join(root, fname)
        for sid, path in found.items():
            self.sources[sid] = CompilerInputSource(
                source_id=sid, status=CompilerInputStatus.PRESENT,
                critical=self.sources.get(sid, CompilerInputSource(sid)).critical,
                path=path, detail="discovered on disk")

    def blockers(self) -> List[str]:
        return [s.source_id for s in self.sources.values()
                if s.status == CompilerInputStatus.MISSING_BLOCKER]

    def warnings(self) -> List[str]:
        return [s.source_id for s in self.sources.values()
                if s.status == CompilerInputStatus.MISSING_WARNING]

    def operator_note(self) -> Any:
        src = self.sources.get("operator_note")
        return src.payload if src and src.present else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_count": len(self.sources),
            "present_count": sum(1 for s in self.sources.values()
                                 if s.present),
            "sources": {sid: s.to_dict() for sid, s in self.sources.items()},
            "blockers": self.blockers(),
            "warnings": self.warnings(),
            "proposal_count": len(self.proposals),
            "note": ("the compiler reads existing artifacts only; falsified "
                     "evidence is preserved and an operator note never overrides "
                     "safety evidence"),
        }
