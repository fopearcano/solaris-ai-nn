"""Next-cycle roadmap reset -- planning only; runs nothing.

:class:`NextCycleRoadmapReset` resets the research loop after a baseline is
established: it lists the next experiments (validation, soak, replication,
falsification, architecture evolution, compile/audit/assimilate, evidence-
improvement) with a required/recommended/optional/blocked priority. It is
planning only -- it runs no task, creates no branch, and calls no external tool.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class RoadmapPriority:
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"
    BLOCKED = "blocked"

    ALL = (REQUIRED, RECOMMENDED, OPTIONAL, BLOCKED)


class RoadmapStatus:
    PLANNED = "planned"
    OPERATOR_PENDING = "operator_pending"
    DEFERRED = "deferred"

    ALL = (PLANNED, OPERATOR_PENDING, DEFERRED)


class RoadmapItemType:
    RUN_SHORT_VALIDATION = "run_short_validation"
    RUN_MINI_SOAK = "run_mini_soak"
    RUN_30_DAY_SOAK = "run_30_day_soak"
    RUN_REPLICATION = "run_replication"
    RUN_FALSIFICATION = "run_falsification"
    RUN_ARCHITECTURE_EVOLUTION = "run_architecture_evolution"
    COMPILE_NEXT_EXPERIMENT = "compile_next_experiment"
    AUDIT_IMPLEMENTATION = "audit_implementation"
    ASSIMILATE_POST_MERGE = "assimilate_post_merge"
    IMPROVE_SAFETY_EVIDENCE = "improve_safety_evidence"
    IMPROVE_LIVE_FIELD_EVIDENCE = "improve_live_field_evidence"
    REDUCE_HUMAN_LABEL_CONTAMINATION = "reduce_human_label_contamination"
    IMPROVE_FIXTURE_CONTROLS = "improve_fixture_controls"
    COLLECT_MISSING_EVIDENCE = "collect_missing_evidence"
    ARCHIVE_BLOCKED_BASELINE = "archive_blocked_baseline"

    ALL = (RUN_SHORT_VALIDATION, RUN_MINI_SOAK, RUN_30_DAY_SOAK, RUN_REPLICATION,
           RUN_FALSIFICATION, RUN_ARCHITECTURE_EVOLUTION,
           COMPILE_NEXT_EXPERIMENT, AUDIT_IMPLEMENTATION, ASSIMILATE_POST_MERGE,
           IMPROVE_SAFETY_EVIDENCE, IMPROVE_LIVE_FIELD_EVIDENCE,
           REDUCE_HUMAN_LABEL_CONTAMINATION, IMPROVE_FIXTURE_CONTROLS,
           COLLECT_MISSING_EVIDENCE, ARCHIVE_BLOCKED_BASELINE)


@dataclass
class RoadmapItem:
    """One planned next-cycle item (planning only; never executed)."""

    item_type: str
    priority: str = RoadmapPriority.RECOMMENDED
    status: str = RoadmapStatus.PLANNED
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"item_type": self.item_type, "priority": self.priority,
                "status": self.status, "detail": self.detail, "executed": False}


@dataclass
class NextCycleRoadmapReset:
    """The reset roadmap for the next research cycle (planning only)."""

    items: List[RoadmapItem] = field(default_factory=list)

    def add(self, item_type: str, priority: str = RoadmapPriority.RECOMMENDED,
            *, status: str = RoadmapStatus.PLANNED, detail: str = "") -> None:
        if item_type not in RoadmapItemType.ALL:
            return
        if priority not in RoadmapPriority.ALL:
            priority = RoadmapPriority.RECOMMENDED
        self.items.append(RoadmapItem(item_type=item_type, priority=priority,
                                      status=status, detail=detail))

    def by_priority(self, priority: str) -> List[RoadmapItem]:
        return [i for i in self.items if i.priority == priority]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "roadmap_item_count": len(self.items),
            "items": [i.to_dict() for i in self.items],
            "required_count": len(self.by_priority(RoadmapPriority.REQUIRED)),
            "recommended_count": len(
                self.by_priority(RoadmapPriority.RECOMMENDED)),
            "optional_count": len(self.by_priority(RoadmapPriority.OPTIONAL)),
            "blocked_count": len(self.by_priority(RoadmapPriority.BLOCKED)),
            "executes_tasks": False, "creates_branches": False,
            "calls_external_tools": False,
            "note": "planning only; it runs no task, creates no branch, and "
                    "calls no external tool",
        }


def build_roadmap_reset(*, validated: bool, blocked: bool,
                        limitations: Dict[str, Any],
                        validation: Dict[str, Any]) -> NextCycleRoadmapReset:
    """Build the next-cycle roadmap from the baseline status + limitations."""
    roadmap = NextCycleRoadmapReset()
    limitations = limitations or {}
    validation = validation or {}

    if blocked:
        # Blocked baselines: collect evidence / revise / archive (no soak).
        roadmap.add(RoadmapItemType.COLLECT_MISSING_EVIDENCE,
                    RoadmapPriority.REQUIRED,
                    status=RoadmapStatus.OPERATOR_PENDING,
                    detail="collect the missing/failed evidence before reuse")
        roadmap.add(RoadmapItemType.IMPROVE_SAFETY_EVIDENCE,
                    RoadmapPriority.REQUIRED,
                    detail="resolve the safety/regression blocker")
        roadmap.add(RoadmapItemType.AUDIT_IMPLEMENTATION,
                    RoadmapPriority.RECOMMENDED)
        roadmap.add(RoadmapItemType.ARCHIVE_BLOCKED_BASELINE,
                    RoadmapPriority.OPTIONAL,
                    detail="archive this baseline if it cannot be unblocked")
        # Soak/replication are blocked until the baseline is unblocked.
        roadmap.add(RoadmapItemType.RUN_MINI_SOAK, RoadmapPriority.BLOCKED,
                    detail="blocked until the baseline validates")
        roadmap.add(RoadmapItemType.RUN_REPLICATION, RoadmapPriority.BLOCKED,
                    detail="blocked until the baseline validates")
        return roadmap

    if validated:
        roadmap.add(RoadmapItemType.RUN_MINI_SOAK, RoadmapPriority.RECOMMENDED,
                    detail="confirm stability on a short bounded soak")
        roadmap.add(RoadmapItemType.RUN_REPLICATION, RoadmapPriority.RECOMMENDED,
                    detail="register and compare across independent runs")
        roadmap.add(RoadmapItemType.RUN_FALSIFICATION,
                    RoadmapPriority.RECOMMENDED,
                    detail="replay the falsification probes against the baseline")
        roadmap.add(RoadmapItemType.RUN_30_DAY_SOAK, RoadmapPriority.OPTIONAL,
                    detail="run only if 30-day evidence is warranted")
        roadmap.add(RoadmapItemType.RUN_ARCHITECTURE_EVOLUTION,
                    RoadmapPriority.RECOMMENDED,
                    detail="feed this baseline into the next variant selection")
        roadmap.add(RoadmapItemType.COMPILE_NEXT_EXPERIMENT,
                    RoadmapPriority.OPTIONAL)
    else:
        roadmap.add(RoadmapItemType.RUN_SHORT_VALIDATION,
                    RoadmapPriority.REQUIRED,
                    detail="complete the missing validation before validating")

    # Limitation-driven improvement items.
    cats = {l.get("category") for l in limitations.get("limitations", [])}
    if "fixture_overfit_risk" in cats:
        roadmap.add(RoadmapItemType.IMPROVE_FIXTURE_CONTROLS,
                    RoadmapPriority.RECOMMENDED)
    if "human_label_contamination_risk" in cats:
        roadmap.add(RoadmapItemType.REDUCE_HUMAN_LABEL_CONTAMINATION,
                    RoadmapPriority.RECOMMENDED)
    if "missing_live_data" in cats:
        roadmap.add(RoadmapItemType.IMPROVE_LIVE_FIELD_EVIDENCE,
                    RoadmapPriority.OPTIONAL)
    if validation.get("validation_missing_count", 0):
        roadmap.add(RoadmapItemType.COLLECT_MISSING_EVIDENCE,
                    RoadmapPriority.RECOMMENDED,
                    detail="collect the missing validation evidence")
    return roadmap
