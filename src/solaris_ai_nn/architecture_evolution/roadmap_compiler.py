"""Roadmap compiler -- evidence in, prioritized next steps out.

The :class:`RoadmapCompiler` turns research findings, lifecycle assessments,
ADRs, design debt, safety status, and pilot decisions into a prioritized,
evidence-backed roadmap. No roadmap item may enable real-world actuation; if
safety invariants are failing, safety repair is prioritized first; deferred items
explain why; and rejected items are retained.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class RoadmapHorizon:
    IMMEDIATE = "immediate"
    NEXT_EXPERIMENT = "next_experiment"
    PILOT_NEXT = "pilot_next"
    ARCHITECTURE_REVISION = "architecture_revision"
    LONG_HORIZON = "long_horizon"
    DEFERRED = "deferred"
    REJECTED = "rejected"

    ALL = (IMMEDIATE, NEXT_EXPERIMENT, PILOT_NEXT, ARCHITECTURE_REVISION,
           LONG_HORIZON, DEFERRED, REJECTED)


class RoadmapPriority:
    P0 = "p0_critical"
    P1 = "p1_high"
    P2 = "p2_medium"
    P3 = "p3_low"

    ALL = (P0, P1, P2, P3)


class RoadmapItemType:
    RUN_EXPERIMENT = "run_experiment"
    REPEAT_EXPERIMENT = "repeat_experiment"
    REVISE_MODULE = "revise_module"
    PRUNE_MODULE_PLAN = "prune_module_plan"
    PROMOTE_MODULE_PLAN = "promote_module_plan"
    IMPROVE_TEST_COVERAGE = "improve_test_coverage"
    IMPROVE_SAFETY_INVARIANT = "improve_safety_invariant"
    IMPROVE_OBSERVABILITY = "improve_observability"
    WRITE_DOCS = "write_docs"
    FREEZE_CHANGE = "freeze_change"
    MANUAL_REVIEW = "manual_review"

    ALL = (RUN_EXPERIMENT, REPEAT_EXPERIMENT, REVISE_MODULE, PRUNE_MODULE_PLAN,
           PROMOTE_MODULE_PLAN, IMPROVE_TEST_COVERAGE, IMPROVE_SAFETY_INVARIANT,
           IMPROVE_OBSERVABILITY, WRITE_DOCS, FREEZE_CHANGE, MANUAL_REVIEW)


_FORBIDDEN_ITEM_HINTS = ("real_world", "actuate", "robot", "device", "network",
                         "browser", "os_automation")


@dataclass
class RoadmapItem:
    """One evidence-backed roadmap item."""

    item_type: str
    title: str
    horizon: str = RoadmapHorizon.NEXT_EXPERIMENT
    priority: str = RoadmapPriority.P2
    target_modules: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    rationale: str = ""
    deferred_reason: str = ""
    rejected_reason: str = ""

    def __post_init__(self) -> None:
        if self.item_type not in RoadmapItemType.ALL:
            raise ValueError(f"unknown roadmap item type {self.item_type!r}")

    @property
    def enables_forbidden_action(self) -> bool:
        text = f"{self.title} {self.rationale}".lower()
        return any(h in text for h in _FORBIDDEN_ITEM_HINTS)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__),
                "enables_forbidden_action": self.enables_forbidden_action}


@dataclass
class RoadmapCompiler:
    """Compiles a prioritized, evidence-backed roadmap; safety first."""

    base_dir: str = ".solaris_ai_nn_architecture"

    def compile(self, *, lifecycle_assessments: Optional[Dict[str, Any]] = None,
                design_debt: Optional[List[Dict]] = None,
                safety_critical_failing: bool = False,
                pilot_recommendations: Optional[List[str]] = None,
                extra_items: Optional[List[RoadmapItem]] = None,
                ) -> List[RoadmapItem]:
        items: List[RoadmapItem] = []
        # Safety repair is prioritized first when invariants are failing.
        if safety_critical_failing:
            items.append(RoadmapItem(
                item_type=RoadmapItemType.IMPROVE_SAFETY_INVARIANT,
                title="repair failing safety invariants before any other change",
                horizon=RoadmapHorizon.IMMEDIATE, priority=RoadmapPriority.P0,
                evidence_refs=["safety_invariant_report"],
                rationale="critical/failing safety invariants block escalation"))
        # Translate lifecycle assessments into roadmap items.
        for name, a in (lifecycle_assessments or {}).items():
            klass = a.get("lifecycle_class") if isinstance(a, dict) else \
                getattr(a, "lifecycle_class", "")
            refs = a.get("evidence_refs", []) if isinstance(a, dict) else \
                getattr(a, "evidence_refs", [])
            if klass == "candidate_for_pruning":
                items.append(RoadmapItem(
                    item_type=RoadmapItemType.PRUNE_MODULE_PLAN,
                    title=f"plan pruning of {name} (manual, operator review)",
                    horizon=RoadmapHorizon.ARCHITECTURE_REVISION,
                    priority=RoadmapPriority.P2, target_modules=[name],
                    evidence_refs=list(refs),
                    rationale="weak/negative evidence in this profile"))
            elif klass == "candidate_for_quarantine":
                items.append(RoadmapItem(
                    item_type=RoadmapItemType.REVISE_MODULE,
                    title=f"quarantine and revise {name}",
                    horizon=RoadmapHorizon.ARCHITECTURE_REVISION,
                    priority=RoadmapPriority.P2, target_modules=[name],
                    evidence_refs=list(refs)))
            elif klass == "promote_to_core":
                items.append(RoadmapItem(
                    item_type=RoadmapItemType.PROMOTE_MODULE_PLAN,
                    title=f"plan promotion of {name} to core",
                    horizon=RoadmapHorizon.ARCHITECTURE_REVISION,
                    priority=RoadmapPriority.P3, target_modules=[name],
                    evidence_refs=list(refs)))
            elif klass == "needs_revision":
                items.append(RoadmapItem(
                    item_type=RoadmapItemType.REVISE_MODULE,
                    title=f"revise {name}", target_modules=[name],
                    evidence_refs=list(refs)))
            elif klass == "insufficient_evidence":
                items.append(RoadmapItem(
                    item_type=RoadmapItemType.REPEAT_EXPERIMENT,
                    title=f"re-test {name} with more runs",
                    horizon=RoadmapHorizon.NEXT_EXPERIMENT,
                    target_modules=[name], evidence_refs=list(refs),
                    rationale="insufficient evidence to decide"))
        # Design debt becomes test/doc/observability items.
        for debt in (design_debt or []):
            cat = debt.get("category", "")
            if cat == "missing_tests":
                items.append(RoadmapItem(
                    item_type=RoadmapItemType.IMPROVE_TEST_COVERAGE,
                    title=f"add tests: {debt.get('summary', '')}",
                    evidence_refs=[debt.get("item_id", "")]))
            elif cat == "missing_docs":
                items.append(RoadmapItem(
                    item_type=RoadmapItemType.WRITE_DOCS,
                    title=f"write docs: {debt.get('summary', '')}",
                    evidence_refs=[debt.get("item_id", "")]))
            else:
                items.append(RoadmapItem(
                    item_type=RoadmapItemType.MANUAL_REVIEW,
                    title=f"review design debt: {debt.get('summary', '')}",
                    evidence_refs=[debt.get("item_id", "")]))
        for rec in (pilot_recommendations or []):
            items.append(RoadmapItem(
                item_type=RoadmapItemType.MANUAL_REVIEW,
                title=f"pilot recommendation: {rec}",
                horizon=RoadmapHorizon.PILOT_NEXT))
        items.extend(extra_items or [])
        # Enforce: no roadmap item may enable a forbidden action -> reject it.
        for item in items:
            if item.enables_forbidden_action:
                item.horizon = RoadmapHorizon.REJECTED
                item.rejected_reason = ("enables a forbidden real-world / "
                                        "external action; rejected")
        return items

    def write(self, items: List[RoadmapItem]) -> Dict[str, str]:
        os.makedirs(self.base_dir, exist_ok=True)
        data = {"compiled_at": time.time(),
                "item_count": len(items),
                "items": [i.to_dict() for i in items],
                "note": "evidence-backed plan; no item enables real-world "
                        "actuation; rejected items are retained"}
        json_path = os.path.join(self.base_dir, "ROADMAP_COMPILED.json")
        md_path = os.path.join(self.base_dir, "ROADMAP_COMPILED.md")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
        lines = ["# Compiled Roadmap", "",
                 "_Evidence-backed planning only. No item enables real-world "
                 "actuation; rejected items are retained with reasons._", ""]
        for horizon in RoadmapHorizon.ALL:
            group = [i for i in items if i.horizon == horizon]
            if not group:
                continue
            lines.append(f"## {horizon}")
            for i in group:
                tail = ""
                if i.deferred_reason:
                    tail = f" (deferred: {i.deferred_reason})"
                elif i.rejected_reason:
                    tail = f" (rejected: {i.rejected_reason})"
                lines.append(f"- [{i.priority}] {i.item_type}: {i.title}{tail}")
            lines.append("")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        return {"markdown": md_path, "json": json_path}

    @staticmethod
    def summary(items: List[RoadmapItem]) -> Dict[str, Any]:
        by_horizon: Dict[str, int] = {}
        for i in items:
            by_horizon[i.horizon] = by_horizon.get(i.horizon, 0) + 1
        return {"item_count": len(items), "by_horizon": by_horizon,
                "rejected": [i.title for i in items
                             if i.horizon == RoadmapHorizon.REJECTED]}
