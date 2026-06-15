"""Decision board -- the open operator decisions, each backed by evidence.

:class:`OperatorDecisionBoard` compiles the decisions an operator currently faces
(safety blockers, pilot/research next steps, architecture reviews, pruning
proposals, ADR reviews, run/export choices, manual reviews, archive/stop) into a
Markdown + JSON board. Each :class:`DecisionItem` carries evidence refs, a
recommendation, a risk note, and what (if anything) blocks it. The board
recommends; it never acts.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class DecisionCategory:
    SAFETY_BLOCKER = "safety_blocker"
    PILOT_NEXT_STEP = "pilot_next_step"
    RESEARCH_NEXT_STEP = "research_next_step"
    ARCHITECTURE_REVIEW = "architecture_review"
    PRUNING_PROPOSAL = "pruning_proposal"
    ADR_REVIEW = "ADR_review"
    RUN_PROFILE = "run_profile"
    EXPORT_BUNDLE = "export_bundle"
    MANUAL_REVIEW = "manual_review"
    ARCHIVE_STOP = "archive_stop"

    ALL = (SAFETY_BLOCKER, PILOT_NEXT_STEP, RESEARCH_NEXT_STEP,
           ARCHITECTURE_REVIEW, PRUNING_PROPOSAL, ADR_REVIEW, RUN_PROFILE,
           EXPORT_BUNDLE, MANUAL_REVIEW, ARCHIVE_STOP)


class DecisionStatus:
    OPEN = "open"
    BLOCKED = "blocked"
    RESOLVED = "resolved"
    DEFERRED = "deferred"

    ALL = (OPEN, BLOCKED, RESOLVED, DEFERRED)


@dataclass
class DecisionItem:
    decision_id: str
    title: str
    category: str
    recommendation: str
    risk: str = ""
    required_action: str = ""
    optional_action: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    blocked_by: List[str] = field(default_factory=list)
    status: str = DecisionStatus.OPEN
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class OperatorDecisionBoard:
    """Compiles and writes the operator decision board."""

    state_dir: str = ".solaris_ai_nn_operator"
    items: List[DecisionItem] = field(default_factory=list)
    _seq: int = field(default=0, init=False)

    def add(self, title: str, category: str, recommendation: str, *,
            risk: str = "", required_action: str = "", optional_action: str = "",
            evidence_refs: Optional[List[str]] = None,
            blocked_by: Optional[List[str]] = None,
            status: str = DecisionStatus.OPEN) -> DecisionItem:
        if category not in DecisionCategory.ALL:
            raise ValueError(f"unknown decision category {category!r}")
        self._seq += 1
        item = DecisionItem(
            decision_id=f"DEC_{self._seq:04d}", title=title, category=category,
            recommendation=recommendation, risk=risk,
            required_action=required_action, optional_action=optional_action,
            evidence_refs=list(evidence_refs or []),
            blocked_by=list(blocked_by or []), status=status)
        self.items.append(item)
        return item

    def build(self, *, safety_status: Optional[Dict[str, Any]] = None,
              research_findings: Optional[Dict[str, Any]] = None,
              architecture_status: Optional[Dict[str, Any]] = None,
              pilot_status: Optional[Dict[str, Any]] = None,
              ) -> "OperatorDecisionBoard":
        """Synthesise decision items from the current evidence."""
        critical = bool(safety_status and (
            safety_status.get("critical_failure")
            or int(safety_status.get("unresolved_blocker_count", 0) or 0) > 0))
        if critical or safety_status is None:
            self.add(
                "Resolve safety before any run", DecisionCategory.SAFETY_BLOCKER,
                "run the full safety check and triage open blockers first",
                risk="launching while a blocker is open is unsafe",
                required_action="run safety_full_check; triage",
                evidence_refs=["safety_status"],
                status=DecisionStatus.BLOCKED if critical else DecisionStatus.OPEN)
        if not research_findings:
            self.add(
                "Establish a research baseline", DecisionCategory.RESEARCH_NEXT_STEP,
                "run a baseline so later claims have a reference",
                optional_action="run research_baseline_random")
        else:
            self.add(
                "Compile an architecture review",
                DecisionCategory.ARCHITECTURE_REVIEW,
                "turn research evidence into keep/revise/prune recommendations",
                evidence_refs=["research_findings"],
                optional_action="run architecture_review")
        if architecture_status and int(
                architecture_status.get("open_adr_count", 0) or 0) > 0:
            self.add(
                "Review open ADRs", DecisionCategory.ADR_REVIEW,
                f"{architecture_status['open_adr_count']} open ADR(s) await "
                "operator review",
                evidence_refs=["architecture_status"])
        if pilot_status and pilot_status.get("ready_for_next"):
            self.add(
                "Generate the next pilot plan", DecisionCategory.PILOT_NEXT_STEP,
                "generate a plan-only pilot artifact for review",
                optional_action="run the relevant pilot plan_only profile")
        return self

    # -- rendering -----------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        by_status: Dict[str, int] = {}
        for item in self.items:
            by_status[item.status] = by_status.get(item.status, 0) + 1
        return {
            "decision_count": len(self.items),
            "by_status": by_status,
            "items": [i.to_dict() for i in self.items],
            "note": "the board recommends; it never acts",
        }

    def render_markdown(self) -> str:
        lines = ["# Operator Decision Board", "",
                 "_Recommendations only. The console never acts on these "
                 "decisions; a human does._", "",
                 f"Open decisions: {len(self.items)}", ""]
        for item in self.items:
            lines.append(f"## {item.decision_id}: {item.title}")
            lines.append(f"- category: `{item.category}`")
            lines.append(f"- status: `{item.status}`")
            lines.append(f"- recommendation: {item.recommendation}")
            if item.risk:
                lines.append(f"- risk: {item.risk}")
            if item.required_action:
                lines.append(f"- required action: {item.required_action}")
            if item.optional_action:
                lines.append(f"- optional action: {item.optional_action}")
            if item.blocked_by:
                lines.append(f"- blocked by: {', '.join(item.blocked_by)}")
            if item.evidence_refs:
                lines.append(f"- evidence: {', '.join(item.evidence_refs)}")
            lines.append("")
        return "\n".join(lines)

    def write(self) -> Dict[str, str]:
        os.makedirs(self.state_dir, exist_ok=True)
        md_path = os.path.join(self.state_dir, "DECISION_BOARD.md")
        json_path = os.path.join(self.state_dir, "DECISION_BOARD.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(self.render_markdown())
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}
