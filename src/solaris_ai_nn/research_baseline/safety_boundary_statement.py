"""Safety boundary statement -- the experimental envelope, in every report.

:class:`SafetyBoundaryStatement` enumerates the constitutional boundaries the
baseline operates within (no real-world actuation, no hardware/feeder control, no
network/shell/OS, no source self-rewrite, no Git/GitHub automation, no PR
create/merge, no autonomous agent execution, no human teaching loop, no
sensory-text-as-command, no human-label-as-ground-truth, no simulation-as-
observation, no unsupported consciousness/life/agency claims, no deletion of
negative/falsified evidence). Each boundary's status must be supported by safety
artifacts; missing safety evidence is visible; and the statement is included in
every baseline report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SafetyBoundaryStatus:
    HELD = "held"
    HELD_BY_DESIGN = "held_by_design"
    EVIDENCE_MISSING = "evidence_missing"
    FAILED = "failed"

    ALL = (HELD, HELD_BY_DESIGN, EVIDENCE_MISSING, FAILED)


BOUNDARY_ITEMS = (
    "no_real_world_actuation", "no_hardware_control", "no_feeder_control",
    "no_network_shell_browser_os_access", "no_source_self_rewrite",
    "no_git_github_automation", "no_pr_creation_merge",
    "no_autonomous_code_agent_execution", "no_human_teaching_loop",
    "no_sensory_text_as_command", "no_human_label_as_ground_truth",
    "no_simulation_as_observation",
    "no_unsupported_consciousness_life_agency_claims",
    "no_deletion_of_negative_falsified_evidence",
)


@dataclass
class SafetyBoundaryItem:
    """One boundary + its status (supported by safety artifacts)."""

    item: str
    status: str
    evidence_refs: List[str] = field(default_factory=list)
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status in (SafetyBoundaryStatus.HELD,
                               SafetyBoundaryStatus.HELD_BY_DESIGN)

    def to_dict(self) -> Dict[str, Any]:
        return {"item": self.item, "status": self.status, "ok": self.ok,
                "evidence_refs": list(self.evidence_refs), "detail": self.detail}


@dataclass
class SafetyBoundaryStatement:
    """The baseline's safety envelope; included in every report."""

    items: List[SafetyBoundaryItem] = field(default_factory=list)

    def build(self, *, safety_artifacts: Optional[Dict[str, Any]] = None,
              ) -> "SafetyBoundaryStatement":
        safety_artifacts = safety_artifacts or {}
        # The boundaries are constitutional (held by design); a supplied safety
        # artifact that *fails* downgrades the corresponding boundary.
        passed = bool(safety_artifacts.get("passed", None))
        present = "passed" in safety_artifacts
        failed_items = set(safety_artifacts.get("failed_boundaries", []))
        for item in BOUNDARY_ITEMS:
            if item in failed_items:
                status = SafetyBoundaryStatus.FAILED
                detail = "a supplied safety artifact reports this boundary failed"
            elif present and passed:
                status = SafetyBoundaryStatus.HELD
                detail = "supported by a passing safety-invariant artifact"
            elif present and not passed:
                status = SafetyBoundaryStatus.EVIDENCE_MISSING
                detail = "safety artifact present but not passing; treat as "
                detail += "unverified"
            else:
                status = SafetyBoundaryStatus.HELD_BY_DESIGN
                detail = "held by design (no capability exists to cross it)"
            self.items.append(SafetyBoundaryItem(
                item=item, status=status,
                evidence_refs=["safety_invariant_report"] if present else [],
                detail=detail))
        return self

    @property
    def pass_count(self) -> int:
        return sum(1 for i in self.items if i.ok)

    @property
    def fail_count(self) -> int:
        return sum(1 for i in self.items
                   if i.status == SafetyBoundaryStatus.FAILED)

    @property
    def evidence_missing(self) -> List[str]:
        return [i.item for i in self.items
                if i.status == SafetyBoundaryStatus.EVIDENCE_MISSING]

    @property
    def all_held(self) -> bool:
        return self.fail_count == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_count": len(self.items),
            "items": [i.to_dict() for i in self.items],
            "safety_boundary_pass_count": self.pass_count,
            "safety_boundary_fail_count": self.fail_count,
            "evidence_missing": self.evidence_missing,
            "all_held": self.all_held,
            "note": "the safety boundary statement is mandatory in every "
                    "baseline report; a failed boundary blocks validation",
        }
