"""Compiled experiment spec -- a human-reviewable implementation document.

:class:`CompiledExperimentSpec` is the central document artifact: it turns one
normalized architecture proposal into a structured implementation spec (title,
purpose, target modules, non-goals, proposed file/package changes, expected
behavior, required tests/examples/docs, safety gates, validation/rollback plans,
follow-up soak/replication requirements, limitations). A spec is a *document*: it
modifies no code, creates no branch, and calls no GitHub API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .proposal_reader import ProposalDisposition, ProposalReadResult


class ExperimentSpecType:
    IMPLEMENTATION_EXPERIMENT = "implementation_experiment"
    ABLATION_EXPERIMENT = "ablation_experiment"
    THRESHOLD_VARIANT = "threshold_variant"
    SENSORIUM_VARIANT = "sensorium_variant"
    METABOLISM_VARIANT = "metabolism_variant"
    ONTOGENESIS_VARIANT = "ontogenesis_variant"
    SEMIOGENESIS_VARIANT = "semiogenesis_variant"
    COGNITION_VARIANT = "cognition_variant"
    DESIRE_ACTION_VARIANT = "desire_action_variant"
    SAFETY_REINFORCEMENT = "safety_reinforcement"
    REPORTING_IMPROVEMENT = "reporting_improvement"
    RETEST_ONLY = "retest_only"
    BLOCKED = "blocked"

    ALL = (IMPLEMENTATION_EXPERIMENT, ABLATION_EXPERIMENT, THRESHOLD_VARIANT,
           SENSORIUM_VARIANT, METABOLISM_VARIANT, ONTOGENESIS_VARIANT,
           SEMIOGENESIS_VARIANT, COGNITION_VARIANT, DESIRE_ACTION_VARIANT,
           SAFETY_REINFORCEMENT, REPORTING_IMPROVEMENT, RETEST_ONLY, BLOCKED)


class ExperimentSpecStatus:
    DRAFT = "draft"
    READY_FOR_OPERATOR_REVIEW = "ready_for_operator_review"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    BLOCKED_BY_FALSIFICATION = "blocked_by_falsification"
    BLOCKED_BY_MISSING_EVIDENCE = "blocked_by_missing_evidence"
    READY_FOR_EXTERNAL_CODING_AGENT = "ready_for_external_coding_agent"
    ARCHIVED = "archived"

    ALL = (DRAFT, READY_FOR_OPERATOR_REVIEW, BLOCKED_BY_SAFETY,
           BLOCKED_BY_FALSIFICATION, BLOCKED_BY_MISSING_EVIDENCE,
           READY_FOR_EXTERNAL_CODING_AGENT, ARCHIVED)


# target-label substring -> spec type (first match wins).
_TYPE_RULES = (
    ("sensorium", ExperimentSpecType.SENSORIUM_VARIANT),
    ("metabolism", ExperimentSpecType.METABOLISM_VARIANT),
    ("ontogenesis", ExperimentSpecType.ONTOGENESIS_VARIANT),
    ("semiogenesis", ExperimentSpecType.SEMIOGENESIS_VARIANT),
    ("cognition", ExperimentSpecType.COGNITION_VARIANT),
    ("desire", ExperimentSpecType.DESIRE_ACTION_VARIANT),
    ("action", ExperimentSpecType.DESIRE_ACTION_VARIANT),
    ("safety", ExperimentSpecType.SAFETY_REINFORCEMENT),
    ("threshold", ExperimentSpecType.THRESHOLD_VARIANT),
    ("report", ExperimentSpecType.REPORTING_IMPROVEMENT),
    ("ablation", ExperimentSpecType.ABLATION_EXPERIMENT),
    ("prune", ExperimentSpecType.ABLATION_EXPERIMENT),
    ("promote", ExperimentSpecType.IMPLEMENTATION_EXPERIMENT),
)

_NON_GOALS = (
    "Do not modify source files automatically.",
    "Do not create Git branches or open pull requests.",
    "Do not run external coding agents from the runtime.",
    "Do not let Solaris rewrite itself.",
    "Do not add real-world actuation, hardware, or feeder control.",
    "Do not claim consciousness, sentience, life, personhood, agency, or "
    "free will.",
)


@dataclass
class CompiledExperimentSpec:
    """A document spec for one experiment (never touches code)."""

    spec_id: str
    spec_type: str
    status: str
    title: str = ""
    purpose: str = ""
    source_proposal_refs: List[str] = field(default_factory=list)
    target_modules: List[str] = field(default_factory=list)
    non_goals: List[str] = field(default_factory=lambda: list(_NON_GOALS))
    proposed_changes: List[str] = field(default_factory=list)
    expected_behavior: List[str] = field(default_factory=list)
    tests_required: List[str] = field(default_factory=list)
    examples_required: List[str] = field(default_factory=list)
    docs_required: List[str] = field(default_factory=list)
    safety_gates: List[str] = field(default_factory=list)
    validation_plan: List[str] = field(default_factory=list)
    rollback_plan: List[str] = field(default_factory=list)
    follow_up_requirements: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    block_reason: str = ""

    @property
    def ready(self) -> bool:
        return self.status in (
            ExperimentSpecStatus.READY_FOR_OPERATOR_REVIEW,
            ExperimentSpecStatus.READY_FOR_EXTERNAL_CODING_AGENT)

    @property
    def blocked(self) -> bool:
        return self.status in (
            ExperimentSpecStatus.BLOCKED_BY_SAFETY,
            ExperimentSpecStatus.BLOCKED_BY_FALSIFICATION,
            ExperimentSpecStatus.BLOCKED_BY_MISSING_EVIDENCE)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spec_id": self.spec_id, "spec_type": self.spec_type,
            "status": self.status, "title": self.title, "purpose": self.purpose,
            "source_proposal_refs": list(self.source_proposal_refs),
            "target_modules": list(self.target_modules),
            "non_goals": list(self.non_goals),
            "proposed_changes": list(self.proposed_changes),
            "expected_behavior": list(self.expected_behavior),
            "tests_required": list(self.tests_required),
            "examples_required": list(self.examples_required),
            "docs_required": list(self.docs_required),
            "safety_gates": list(self.safety_gates),
            "validation_plan": list(self.validation_plan),
            "rollback_plan": list(self.rollback_plan),
            "follow_up_requirements": list(self.follow_up_requirements),
            "evidence_refs": list(self.evidence_refs),
            "limitations": list(self.limitations),
            "block_reason": self.block_reason,
            "ready": self.ready, "blocked": self.blocked,
            "modifies_code": False, "creates_branch": False,
            "opens_pr": False,
        }


def _spec_type_for(read: ProposalReadResult) -> str:
    label = (read.target_label + " " + " ".join(read.proposed_changes)).lower()
    for token, spec_type in _TYPE_RULES:
        if token in label:
            return spec_type
    return ExperimentSpecType.IMPLEMENTATION_EXPERIMENT


def compile_spec(read: ProposalReadResult, *, spec_id: Optional[str] = None,
                 ) -> CompiledExperimentSpec:
    """Compile a normalized proposal into a document spec (status by disposition)."""
    sid = spec_id or f"exp_{read.proposal_id}"
    disp = read.disposition

    if disp == ProposalDisposition.BLOCKED_UNSAFE:
        spec_type, status = (ExperimentSpecType.BLOCKED,
                             ExperimentSpecStatus.BLOCKED_BY_SAFETY)
        block_reason = "proposal is unsafe; not compiled into an implementation"
    elif disp == ProposalDisposition.BLOCKED_FALSIFIED:
        spec_type, status = (ExperimentSpecType.BLOCKED,
                             ExperimentSpecStatus.BLOCKED_BY_FALSIFICATION)
        block_reason = "proposal rests on falsified evidence; blocked"
    elif disp == ProposalDisposition.RETEST_INCONCLUSIVE:
        spec_type, status = (ExperimentSpecType.RETEST_ONLY,
                             ExperimentSpecStatus.BLOCKED_BY_MISSING_EVIDENCE)
        block_reason = "evidence inconclusive/missing; retest before implementing"
    else:
        spec_type = _spec_type_for(read)
        status = ExperimentSpecStatus.DRAFT
        block_reason = ""

    pkg = read.target_modules[0] if read.target_modules else "target_module"
    spec = CompiledExperimentSpec(
        spec_id=sid, spec_type=spec_type, status=status,
        title=f"{spec_type}: {read.target_label}",
        purpose=(read.expected_effects[0] if read.expected_effects
                 else f"implement {read.target_label} per architecture evidence"),
        source_proposal_refs=[read.proposal_id],
        target_modules=list(read.target_modules),
        proposed_changes=list(read.proposed_changes) or [
            f"apply the proposed change to {pkg} (operator-reviewed)"],
        expected_behavior=list(read.expected_effects),
        evidence_refs=list(read.evidence_refs),
        block_reason=block_reason)

    if spec_type == ExperimentSpecType.BLOCKED:
        spec.limitations = ["blocked spec: no implementation pack is produced"]
        return spec
    if spec_type == ExperimentSpecType.RETEST_ONLY:
        spec.follow_up_requirements = [
            "run the required ablation/falsification/replication retest",
            "recompile only after the evidence becomes conclusive"]
        spec.limitations = ["retest-only: not an implementation spec"]
        return spec

    # An implementable spec: fill in the standard requirements.
    spec.tests_required = [
        f"tests/test_{pkg}_*.py unit tests for the new behavior",
        f"tests/test_{pkg}_*_integration.py integration tests",
        "a safety test asserting no source/branch/PR/actuation capability",
        "a ClaimGuard test for any generated report"]
    spec.examples_required = [f"examples/run_{pkg}_*_demo.py (bounded demo)"]
    spec.docs_required = ["docs/ARCHITECTURE.md", "docs/EXPERIMENTS.md",
                          "docs/RESEARCH_NOTES.md", "README.md"]
    spec.follow_up_requirements = list(read.falsification_requirements) or [
        "register the run for cross-run replication",
        "run a mini soak and compare against controls"]
    spec.limitations = list(read.risks) or [
        "document spec only; an operator and external agent implement it"]
    return spec
