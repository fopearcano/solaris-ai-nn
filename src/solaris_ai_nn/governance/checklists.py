"""Checklists -- the operator's pre-flight and post-flight discipline.

A :class:`Checklist` is a fixed list of named items evaluated against a plain
context dict (item id -> truthy/falsy). Results are serializable and human
readable; nothing here executes anything.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ChecklistItem:
    """One thing to verify before/after a run."""

    item_id: str
    description: str
    required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ChecklistResult:
    """The outcome of evaluating one checklist against a context."""

    name: str
    passed: bool
    items: List[Dict[str, Any]] = field(default_factory=list)
    failed_required: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "timestamp": self.timestamp,
            "failed_required": list(self.failed_required),
            "items": list(self.items),
        }

    def to_markdown(self) -> str:
        lines = [f"# Checklist: {self.name}", "",
                 f"Result: **{'PASSED' if self.passed else 'FAILED'}**", ""]
        for item in self.items:
            mark = "x" if item["passed"] else " "
            suffix = "" if item["required"] else " (advisory)"
            lines.append(f"- [{mark}] {item['description']}{suffix}")
        lines.append("")
        return "\n".join(lines)


@dataclass
class Checklist:
    """A named list of items; evaluation is a pure dict lookup."""

    name: str
    items: List[ChecklistItem] = field(default_factory=list)

    def evaluate(self, context: Dict[str, Any]) -> ChecklistResult:
        """Each item passes iff ``context[item_id]`` is truthy."""
        rows: List[Dict[str, Any]] = []
        failed_required: List[str] = []
        for item in self.items:
            ok = bool(context.get(item.item_id))
            rows.append({"item_id": item.item_id,
                         "description": item.description,
                         "required": item.required, "passed": ok})
            if item.required and not ok:
                failed_required.append(item.item_id)
        return ChecklistResult(name=self.name, passed=not failed_required,
                               items=rows, failed_required=failed_required)

    def item_ids(self) -> List[str]:
        return [i.item_id for i in self.items]


# -- the required checklists ------------------------------------------------------


def pre_run_checklist() -> Checklist:
    return Checklist("pre_run", [
        ChecklistItem("state_dir_configured", "state directory configured"),
        ChecklistItem("artifact_dir_configured",
                      "artifact directory configured"),
        ChecklistItem("bounds_set", "max steps and/or max duration set"),
        ChecklistItem("watchdog_enabled", "watchdog enabled"),
        ChecklistItem("checkpointing_enabled", "checkpointing enabled"),
        ChecklistItem("emergency_stop_path_known",
                      "emergency stop sentinel path known"),
        ChecklistItem("permissions_evaluated",
                      "permissions evaluated against the policy"),
        ChecklistItem("risk_acknowledged",
                      "risk assessment reviewed and acknowledged"),
        ChecklistItem("previous_incidents_reviewed",
                      "previous incidents reviewed"),
    ])


def long_soak_checklist() -> Checklist:
    return Checklist("long_soak", [
        ChecklistItem("short_bounded_test_passed",
                      "a short bounded test passed"),
        ChecklistItem("restart_test_passed", "the restart test passed"),
        ChecklistItem("replay_test_passed", "the replay test passed"),
        ChecklistItem("healthcheck_demo_passed",
                      "the healthcheck demo passed"),
        ChecklistItem("artifact_rotation_dry_run_passed",
                      "an artifact-rotation dry run passed"),
        ChecklistItem("storage_budget_checked", "storage budget checked"),
        ChecklistItem("operator_availability_confirmed",
                      "operator availability confirmed for the soak window"),
    ])


def plasticity_checklist() -> Checklist:
    return Checklist("plasticity", [
        ChecklistItem("dry_run_completed", "a dry run was completed first"),
        ChecklistItem("rollback_tested", "rollback was tested"),
        ChecklistItem("audit_enabled", "plasticity audit logging enabled"),
        ChecklistItem("safety_validator_active",
                      "the safety validator is active"),
        ChecklistItem("mutation_bounds_reviewed",
                      "mutation bounds (SAFE_BOUNDS) reviewed"),
    ])


def sidecar_checklist() -> Checklist:
    return Checklist("sidecar", [
        ChecklistItem("observe_only_tested", "observe-only mode tested"),
        ChecklistItem("suggestions_clearly_marked",
                      "suggestions are clearly marked as suggestions"),
        ChecklistItem("no_action_authority",
                      "the sidecar has no Action authority"),
        ChecklistItem("detach_tested", "detach was tested"),
        ChecklistItem("compatibility_report_reviewed",
                      "the compatibility report was reviewed"),
    ])


def post_run_checklist() -> Checklist:
    return Checklist("post_run", [
        ChecklistItem("final_checkpoint_exists", "a final checkpoint exists"),
        ChecklistItem("health_report_exists", "a health report exists"),
        ChecklistItem("incidents_reviewed", "incidents were reviewed"),
        ChecklistItem("benchmark_report_generated",
                      "a benchmark report was generated", required=False),
        ChecklistItem("inner_map_saved", "the Inner MAP was saved"),
        ChecklistItem("language_report_saved_if_enabled",
                      "the language report was saved (if language was "
                      "enabled)", required=False),
        ChecklistItem("run_registry_updated", "the run registry was updated"),
    ])


ALL_CHECKLISTS = {
    "pre_run": pre_run_checklist,
    "long_soak": long_soak_checklist,
    "plasticity": plasticity_checklist,
    "sidecar": sidecar_checklist,
    "post_run": post_run_checklist,
}
