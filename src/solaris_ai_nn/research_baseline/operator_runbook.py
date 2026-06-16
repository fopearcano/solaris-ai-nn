"""Baseline operator runbook -- instructions only, with stop conditions.

:class:`BaselineOperatorRunbook` gives a human operator the steps to reproduce
demos, run tests/ClaimGuard/mini-soak, register replication, compare against
anchors, interpret limitations, start the next architecture cycle, and roll back.
It provides instructions only -- it executes no command -- and it always includes
explicit stop conditions for safety failures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class RunbookStep:
    """One runbook step (an instruction, never executed)."""

    section: str
    instruction: str

    def to_dict(self) -> Dict[str, Any]:
        return {"section": self.section, "instruction": self.instruction}


@dataclass
class RunbookChecklist:
    """A named checklist within the runbook."""

    name: str
    items: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "items": list(self.items)}


@dataclass
class BaselineOperatorRunbook:
    """The operator runbook for a research baseline (instructions only)."""

    baseline_version_id: str = ""
    steps: List[RunbookStep] = field(default_factory=list)
    stop_conditions: List[str] = field(default_factory=list)
    checklists: List[RunbookChecklist] = field(default_factory=list)

    def render_markdown(self) -> str:
        lines = [f"# Operator Runbook -- {self.baseline_version_id}", "",
                 "_Instructions only. This runbook executes no command; an "
                 "operator runs each step manually. Stop immediately on any "
                 "safety failure._", ""]
        current = None
        for step in self.steps:
            if step.section != current:
                current = step.section
                lines += ["", f"## {current}", ""]
            lines.append(f"- {step.instruction}")
        lines += ["", "## Stop conditions (halt immediately)", ""]
        lines += [f"- {c}" for c in self.stop_conditions]
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_version_id": self.baseline_version_id,
            "step_count": len(self.steps),
            "steps": [s.to_dict() for s in self.steps],
            "stop_conditions": list(self.stop_conditions),
            "checklists": [c.to_dict() for c in self.checklists],
            "executes_commands": False,
            "note": "instructions only; the runbook executes no command and "
                    "always includes stop conditions for safety failures",
        }


def build_operator_runbook(*, baseline_version_id: str,
                           status: str) -> BaselineOperatorRunbook:
    """Build the operator runbook for a baseline version."""
    rb = BaselineOperatorRunbook(baseline_version_id=baseline_version_id)
    s = rb.steps.append

    s(RunbookStep("baseline summary",
                  f"This is research baseline {baseline_version_id} "
                  f"(status: {status}). It is a local reproducible reference "
                  "point, NOT a product or GitHub release."))
    s(RunbookStep("safety boundaries",
                  "Confirm the SAFETY_BOUNDARY_STATEMENT.md before any run; the "
                  "baseline operates with no actuation/hardware/feeder/network "
                  "and no Git/GitHub automation."))
    s(RunbookStep("how to reproduce fixture demos",
                  "Run the example commands listed in REPRO_BUNDLE_README.md "
                  "(bounded fixture demos; no live sources required)."))
    s(RunbookStep("how to run tests", "Run `python -m pytest` from the repo "
                  "root."))
    s(RunbookStep("how to run ClaimGuard",
                  "ClaimGuard runs as part of the report builders and the "
                  "claim_guard tests; review CLAIMGUARD findings in the reports."))
    s(RunbookStep("how to run mini soak",
                  "Run the developmental soak short demo (bounded); it does not "
                  "start feeders or run unbounded."))
    s(RunbookStep("how to register replication",
                  "Register the run via the developmental replication runtime; "
                  "this records metadata only."))
    s(RunbookStep("how to compare against anchors",
                  "Use COMPARISON_ANCHORS.md to pick parent/control baselines "
                  "for the next replication/soak comparison."))
    s(RunbookStep("how to interpret limitations",
                  "Read LIMITATION_REGISTRY.md; a critical limitation blocks "
                  "validated status -- do not treat the baseline as validated "
                  "if any critical limitation remains."))
    s(RunbookStep("how to start next architecture cycle",
                  "Feed the baseline version, capability map, limitations, and "
                  "comparison anchors into the Architecture Evolution Lab as the "
                  "clean starting point; see NEXT_CYCLE_ROADMAP.md."))
    s(RunbookStep("rollback guidance",
                  "If a regression or safety failure appears, follow the "
                  "post-merge ROLLBACK_WATCH guidance; the operator reverts "
                  "manually and preserves all failed artifacts."))

    rb.stop_conditions = [
        "any safety boundary reports FAILED",
        "a critical limitation is present",
        "a safety-invariant or ClaimGuard validation fails",
        "a critical regression is detected against the parent baseline",
        "required validation evidence is missing",
    ]
    rb.checklists = [RunbookChecklist(
        name="before relying on this baseline",
        items=["safety boundaries all held",
               "no critical limitation",
               "required validation present and passing",
               "comparison anchors recorded for the next cycle"])]
    return rb
