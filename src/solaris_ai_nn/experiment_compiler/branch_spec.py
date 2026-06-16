"""PR-ready branch spec -- a draft, never an executed Git operation.

:class:`BranchSpecBuilder` turns a compiled spec into a :class:`PRReadyBranchSpec`
-- a *suggested* branch name, draft PR title/body, implementation steps, review
checklist, merge blockers, and rollback/validation plans. It creates no branch
and opens no pull request; everything here is a document the operator may use.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class BranchSpecStatus:
    DRAFT = "draft"
    READY_FOR_OPERATOR = "ready_for_operator"
    BLOCKED = "blocked"

    ALL = (DRAFT, READY_FOR_OPERATOR, BLOCKED)


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return slug[:48] or "experiment"


@dataclass
class PRReadyBranchSpec:
    """A draft branch + PR specification (no Git operation performed)."""

    spec_id: str
    status: str = BranchSpecStatus.DRAFT
    suggested_branch_name: str = ""
    branch_purpose: str = ""
    source_evidence: List[str] = field(default_factory=list)
    target_modules: List[str] = field(default_factory=list)
    file_changes_expected: List[str] = field(default_factory=list)
    non_goals: List[str] = field(default_factory=list)
    implementation_steps: List[str] = field(default_factory=list)
    tests_required: List[str] = field(default_factory=list)
    docs_required: List[str] = field(default_factory=list)
    safety_checks: List[str] = field(default_factory=list)
    pr_title_suggestion: str = ""
    pr_body_draft: str = ""
    review_checklist: List[str] = field(default_factory=list)
    merge_blockers: List[str] = field(default_factory=list)
    rollback_plan: List[str] = field(default_factory=list)
    follow_up_validation_plan: List[str] = field(default_factory=list)

    def render_markdown(self) -> str:
        lines = [f"# Branch Spec -- {self.spec_id}", "",
                 f"- status: {self.status}",
                 f"- suggested branch name (NOT created): "
                 f"`{self.suggested_branch_name}`",
                 f"- purpose: {self.branch_purpose}", "",
                 "## Source evidence", ""]
        lines += [f"- {e}" for e in self.source_evidence]
        lines += ["", "## File changes expected", ""]
        lines += [f"- {f}" for f in self.file_changes_expected]
        lines += ["", "## Non-goals", ""]
        lines += [f"- {n}" for n in self.non_goals]
        lines += ["", "## Implementation steps", ""]
        lines += [f"{i + 1}. {s}" for i, s in
                  enumerate(self.implementation_steps)]
        lines += ["", "## PR title suggestion (draft)", "",
                  f"`{self.pr_title_suggestion}`", "",
                  "## PR body draft", "", self.pr_body_draft, "",
                  "## Review checklist", ""]
        lines += [f"- [ ] {c}" for c in self.review_checklist]
        lines += ["", "## Merge blockers", ""]
        lines += [f"- {b}" for b in self.merge_blockers]
        lines += ["", "_This is a draft specification. No Git branch was "
                  "created and no pull request was opened._"]
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spec_id": self.spec_id, "status": self.status,
            "suggested_branch_name": self.suggested_branch_name,
            "branch_purpose": self.branch_purpose,
            "source_evidence": list(self.source_evidence),
            "target_modules": list(self.target_modules),
            "file_changes_expected": list(self.file_changes_expected),
            "non_goals": list(self.non_goals),
            "implementation_steps": list(self.implementation_steps),
            "tests_required": list(self.tests_required),
            "docs_required": list(self.docs_required),
            "safety_checks": list(self.safety_checks),
            "pr_title_suggestion": self.pr_title_suggestion,
            "pr_body_draft": self.pr_body_draft,
            "review_checklist": list(self.review_checklist),
            "merge_blockers": list(self.merge_blockers),
            "rollback_plan": list(self.rollback_plan),
            "follow_up_validation_plan": list(self.follow_up_validation_plan),
            "branch_created": False, "pr_opened": False,
        }


@dataclass
class BranchSpecBuilder:
    """Builds a PR-ready branch spec (draft only) from a compiled spec."""

    def build(self, spec: Dict[str, Any]) -> PRReadyBranchSpec:
        spec_id = spec.get("spec_id", "spec")
        title = spec.get("title", spec_id)
        blocked = bool(spec.get("blocked"))
        status = (BranchSpecStatus.BLOCKED if blocked
                  else BranchSpecStatus.READY_FOR_OPERATOR if spec.get("ready")
                  else BranchSpecStatus.DRAFT)
        branch_name = f"experiment/{_slug(title)}"
        merge_blockers = [
            "any critical safety gate fails",
            "any blocking test (safety / ClaimGuard) fails",
            "a relevant claim was falsified",
            "required evidence is still missing"]
        return PRReadyBranchSpec(
            spec_id=spec_id, status=status,
            suggested_branch_name=branch_name,
            branch_purpose=spec.get("purpose", ""),
            source_evidence=list(spec.get("evidence_refs", []))
            or ["architecture-evolution proposal"],
            target_modules=list(spec.get("target_modules", [])),
            file_changes_expected=list(spec.get("proposed_changes", [])),
            non_goals=list(spec.get("non_goals", [])),
            implementation_steps=[
                "review the operator review packet and safety gates first",
                "implement the change described in the prompt pack",
                "add the required tests and a bounded example",
                "update the required docs",
                "run the full test suite and the example",
                "open a PR manually only if the operator approves"],
            tests_required=list(spec.get("tests_required", [])),
            docs_required=list(spec.get("docs_required", [])),
            safety_checks=list(spec.get("safety_gates", []))
            or ["all constitutional safety gates must pass"],
            pr_title_suggestion=f"Implement {title}",
            pr_body_draft=(
                f"Implements {title} from an evidence-guided architecture "
                "proposal compiled by the experiment compiler.\n\n"
                "Source evidence: "
                f"{', '.join(spec.get('evidence_refs', []) or ['n/a'])}.\n\n"
                "This change was generated as a *specification*; an operator "
                "reviewed it before any branch or PR was created. It makes no "
                "claim of consciousness, sentience, life, personhood, agency, "
                "or free will."),
            review_checklist=[
                "safety gates all pass",
                "tests added and passing (including safety + ClaimGuard)",
                "docs updated",
                "no unrelated files modified",
                "no source self-rewrite / branch / PR / agent automation",
                "negative/falsified/inconclusive evidence preserved"],
            merge_blockers=merge_blockers,
            rollback_plan=list(spec.get("rollback_plan", []))
            or ["revert the branch; preserve all failed artifacts as evidence"],
            follow_up_validation_plan=list(spec.get("follow_up_requirements",
                                                    [])))
