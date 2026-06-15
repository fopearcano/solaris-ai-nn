"""Architecture decision records -- proposals on paper, never code changes.

An :class:`ArchitectureDecisionRecord` documents a proposed architecture change
(keep / promote / revise / prune / quarantine / ...), its evidence, alternatives,
expected benefit/risk, migration need, and rollback plan. ADRs are Markdown/JSON
planning artifacts: they do not modify code, and operator approval is recorded,
never executed automatically.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class DecisionType:
    KEEP_MODULE = "keep_module"
    PROMOTE_MODULE = "promote_module"
    REVISE_MODULE = "revise_module"
    PRUNE_MODULE = "prune_module"
    QUARANTINE_MODULE = "quarantine_module"
    DEPRECATE_MODULE = "deprecate_module"
    SPLIT_MODULE = "split_module"
    MERGE_MODULES = "merge_modules"
    ADD_EXPERIMENT = "add_experiment"
    REPEAT_EXPERIMENT = "repeat_experiment"
    FREEZE_ARCHITECTURE = "freeze_architecture"
    SAFETY_BLOCK_CHANGE = "safety_block_change"

    ALL = (KEEP_MODULE, PROMOTE_MODULE, REVISE_MODULE, PRUNE_MODULE,
           QUARANTINE_MODULE, DEPRECATE_MODULE, SPLIT_MODULE, MERGE_MODULES,
           ADD_EXPERIMENT, REPEAT_EXPERIMENT, FREEZE_ARCHITECTURE,
           SAFETY_BLOCK_CHANGE)


class DecisionStatus:
    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED_BY_OPERATOR = "approved_by_operator"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    IMPLEMENTED_EXTERNALLY = "implemented_externally"
    ARCHIVED = "archived"

    ALL = (DRAFT, PROPOSED, APPROVED_BY_OPERATOR, REJECTED, SUPERSEDED,
           IMPLEMENTED_EXTERNALLY, ARCHIVED)


@dataclass
class DecisionRationale:
    summary: str = ""
    evidence_summary: str = ""
    contradicting_evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ArchitectureDecisionRecord:
    """One ADR: a proposed change documented for operator review."""

    title: str
    decision_type: str
    affected_modules: List[str] = field(default_factory=list)
    status: str = DecisionStatus.DRAFT
    rationale: DecisionRationale = field(default_factory=DecisionRationale)
    evidence_refs: List[str] = field(default_factory=list)
    safety_refs: List[str] = field(default_factory=list)
    research_refs: List[str] = field(default_factory=list)
    alternatives_considered: List[str] = field(default_factory=list)
    expected_benefit: str = ""
    expected_risk: str = ""
    migration_required: bool = False
    rollback_plan: str = ""
    operator_review_required: bool = True
    adr_id: str = field(default_factory=lambda: f"ADR_{uuid.uuid4().hex[:8]}")
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.decision_type not in DecisionType.ALL:
            raise ValueError(f"unknown decision type {self.decision_type!r}")
        if self.status not in DecisionStatus.ALL:
            raise ValueError(f"unknown decision status {self.status!r}")
        # An ADR always requires operator review; it never self-applies.
        self.operator_review_required = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adr_id": self.adr_id, "title": self.title,
            "decision_type": self.decision_type,
            "affected_modules": self.affected_modules, "status": self.status,
            "rationale": self.rationale.to_dict(),
            "evidence_refs": self.evidence_refs, "safety_refs": self.safety_refs,
            "research_refs": self.research_refs,
            "alternatives_considered": self.alternatives_considered,
            "expected_benefit": self.expected_benefit,
            "expected_risk": self.expected_risk,
            "migration_required": self.migration_required,
            "rollback_plan": self.rollback_plan,
            "operator_review_required": True, "created_at": self.created_at,
            "metadata": self.metadata,
            "note": "planning artifact only; no code change was applied",
        }

    def render_markdown(self) -> str:
        lines = [
            f"# {self.adr_id}: {self.title}",
            "",
            "_This is an architecture decision record: a planning artifact. "
            "It does not modify code, and operator approval is a record, not an "
            "automatic implementation._",
            "",
            f"- decision type: {self.decision_type}",
            f"- status: {self.status}",
            f"- affected modules: {', '.join(self.affected_modules) or 'none'}",
            f"- operator review required: {self.operator_review_required}",
            f"- migration required: {self.migration_required}",
            "",
            "## Rationale",
            f"- {self.rationale.summary or 'n/a'}",
            f"- evidence: {self.rationale.evidence_summary or 'n/a'}",
            f"- contradicting evidence: "
            f"{self.rationale.contradicting_evidence or 'none recorded'}",
            "",
            "## Expected benefit / risk",
            f"- benefit: {self.expected_benefit or 'n/a'}",
            f"- risk: {self.expected_risk or 'n/a'}",
            "",
            "## Alternatives considered",
        ]
        lines += [f"- {a}" for a in self.alternatives_considered] or ["- none"]
        lines += ["", "## Rollback plan", f"- {self.rollback_plan or 'n/a'}"]
        return "\n".join(lines)


@dataclass
class ADRStore:
    """Persists ADRs as Markdown + JSON with an append-only index."""

    base_dir: str = ".solaris_ai_nn_architecture"

    def __post_init__(self) -> None:
        self.adr_dir = os.path.join(self.base_dir, "adr")
        self.index_path = os.path.join(self.base_dir, "adr_index.jsonl")
        self._adrs: List[ArchitectureDecisionRecord] = []

    def write(self, adr: ArchitectureDecisionRecord) -> Dict[str, str]:
        os.makedirs(self.adr_dir, exist_ok=True)
        md_path = os.path.join(self.adr_dir, f"{adr.adr_id}.md")
        json_path = os.path.join(self.adr_dir, f"{adr.adr_id}.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(adr.render_markdown())
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(adr.to_dict(), fh, indent=2, default=str)
        with open(self.index_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"adr_id": adr.adr_id, "title": adr.title,
                                 "decision_type": adr.decision_type,
                                 "status": adr.status}, default=str) + "\n")
        self._adrs.append(adr)
        return {"markdown": md_path, "json": json_path}

    def open_count(self) -> int:
        return sum(1 for a in self._adrs
                   if a.status in (DecisionStatus.DRAFT,
                                   DecisionStatus.PROPOSED))

    def snapshot(self) -> Dict[str, Any]:
        return {"adr_count": len(self._adrs), "open_adr_count":
                self.open_count(),
                "adr_ids": [a.adr_id for a in self._adrs]}
