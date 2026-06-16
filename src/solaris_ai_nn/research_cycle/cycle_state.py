"""Research cycle state -- where the project is in the experimental cycle.

:class:`ResearchCycleState` is a *descriptive* record of the current cycle stage
and its status. It cannot approve itself, cannot advance through critical gates
without evidence, and keeps missing evidence visible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ResearchCycleStage:
    BASELINE_SELECTED = "baseline_selected"
    ROADMAP_DEFINED = "roadmap_defined"
    ARCHITECTURE_EVIDENCE_LOADED = "architecture_evidence_loaded"
    VARIANT_PROPOSED = "variant_proposed"
    EXPERIMENT_PACK_COMPILED = "experiment_pack_compiled"
    WAITING_FOR_EXTERNAL_IMPLEMENTATION = "waiting_for_external_implementation"
    IMPLEMENTATION_SUBMITTED = "implementation_submitted"
    IMPLEMENTATION_AUDITED = "implementation_audited"
    WAITING_FOR_HUMAN_MERGE = "waiting_for_human_merge"
    POST_MERGE_EVIDENCE_SUBMITTED = "post_merge_evidence_submitted"
    POST_MERGE_ASSIMILATED = "post_merge_assimilated"
    CANDIDATE_BASELINE_CREATED = "candidate_baseline_created"
    RESEARCH_BASELINE_VALIDATED = "research_baseline_validated"
    SOAK_RECOMMENDED = "soak_recommended"
    REPLICATION_RECOMMENDED = "replication_recommended"
    FALSIFICATION_RECOMMENDED = "falsification_recommended"
    ARCHITECTURE_EVOLUTION_RECOMMENDED = "architecture_evolution_recommended"
    CYCLE_COMPLETE = "cycle_complete"
    BLOCKED = "blocked"
    ARCHIVED = "archived"

    # Canonical forward order (recommendation branches share a rank).
    ORDER = (BASELINE_SELECTED, ROADMAP_DEFINED, ARCHITECTURE_EVIDENCE_LOADED,
             VARIANT_PROPOSED, EXPERIMENT_PACK_COMPILED,
             WAITING_FOR_EXTERNAL_IMPLEMENTATION, IMPLEMENTATION_SUBMITTED,
             IMPLEMENTATION_AUDITED, WAITING_FOR_HUMAN_MERGE,
             POST_MERGE_EVIDENCE_SUBMITTED, POST_MERGE_ASSIMILATED,
             CANDIDATE_BASELINE_CREATED, RESEARCH_BASELINE_VALIDATED,
             SOAK_RECOMMENDED, REPLICATION_RECOMMENDED,
             FALSIFICATION_RECOMMENDED, ARCHITECTURE_EVOLUTION_RECOMMENDED,
             CYCLE_COMPLETE)

    ALL = ORDER + (BLOCKED, ARCHIVED)


class ResearchCycleStageStatus:
    NOT_STARTED = "not_started"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_OPERATOR = "waiting_for_operator"
    WAITING_FOR_EXTERNAL_ARTIFACT = "waiting_for_external_artifact"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    BLOCKED_BY_MISSING_EVIDENCE = "blocked_by_missing_evidence"
    BLOCKED_BY_TESTS = "blocked_by_tests"
    BLOCKED_BY_FALSIFICATION = "blocked_by_falsification"
    BLOCKED_BY_REGRESSION = "blocked_by_regression"
    COMPLETED = "completed"
    INCONCLUSIVE = "inconclusive"
    UNKNOWN = "unknown"

    ALL = (NOT_STARTED, READY, IN_PROGRESS, WAITING_FOR_OPERATOR,
           WAITING_FOR_EXTERNAL_ARTIFACT, BLOCKED_BY_SAFETY,
           BLOCKED_BY_MISSING_EVIDENCE, BLOCKED_BY_TESTS,
           BLOCKED_BY_FALSIFICATION, BLOCKED_BY_REGRESSION, COMPLETED,
           INCONCLUSIVE, UNKNOWN)

    BLOCKED_KINDS = (BLOCKED_BY_SAFETY, BLOCKED_BY_MISSING_EVIDENCE,
                     BLOCKED_BY_TESTS, BLOCKED_BY_FALSIFICATION,
                     BLOCKED_BY_REGRESSION)


@dataclass
class ResearchCycleState:
    """The current cycle stage + status (descriptive; cannot self-approve)."""

    stage: str = ResearchCycleStage.BASELINE_SELECTED
    status: str = ResearchCycleStageStatus.NOT_STARTED
    missing_evidence: List[str] = field(default_factory=list)
    detail: str = ""

    @property
    def blocked(self) -> bool:
        return (self.stage == ResearchCycleStage.BLOCKED
                or self.status in ResearchCycleStageStatus.BLOCKED_KINDS)

    def to_dict(self) -> Dict[str, Any]:
        return {"stage": self.stage, "status": self.status,
                "missing_evidence": list(self.missing_evidence),
                "detail": self.detail, "blocked": self.blocked,
                "self_approved": False}


# Which bundle key, when present, signals each stage has been *reached*.
_STAGE_EVIDENCE = (
    (ResearchCycleStage.BASELINE_SELECTED, "research_baseline"),
    (ResearchCycleStage.ROADMAP_DEFINED, "roadmap"),
    (ResearchCycleStage.ARCHITECTURE_EVIDENCE_LOADED, "architecture_evolution"),
    (ResearchCycleStage.EXPERIMENT_PACK_COMPILED, "experiment_compiler"),
    (ResearchCycleStage.IMPLEMENTATION_AUDITED, "implementation_intake"),
    (ResearchCycleStage.POST_MERGE_ASSIMILATED, "post_merge"),
)


def determine_state(bundle: Dict[str, Any]) -> ResearchCycleState:
    """Derive the descriptive cycle state from the available evidence bundle.

    The furthest stage with present evidence wins; the status reflects whether
    the project is waiting for an operator, waiting for an external artifact,
    blocked, or able to proceed. Missing evidence stays visible.
    """
    bundle = bundle or {}
    reached = ResearchCycleStage.BASELINE_SELECTED
    for stage, key in _STAGE_EVIDENCE:
        if bundle.get(key):
            reached = stage

    pm = bundle.get("post_merge", {}) or {}
    intake = bundle.get("implementation_intake", {}) or {}
    rb = bundle.get("research_baseline", {}) or {}

    state = ResearchCycleState(stage=reached,
                               status=ResearchCycleStageStatus.IN_PROGRESS)

    # Refine based on the most advanced evidence.
    if bundle.get("research_baseline"):
        rb_status = rb.get("baseline_status")
        if rb_status in ("validated", "validated_with_warnings"):
            state.stage = ResearchCycleStage.RESEARCH_BASELINE_VALIDATED
            state.status = ResearchCycleStageStatus.COMPLETED
            state.detail = f"research baseline {rb_status}"
        elif rb_status == "blocked":
            state.stage = ResearchCycleStage.BLOCKED
            state.status = ResearchCycleStageStatus.BLOCKED_BY_SAFETY
            state.detail = "research baseline blocked"
    elif bundle.get("post_merge"):
        cand = pm.get("candidate_baseline_status")
        state.stage = ResearchCycleStage.CANDIDATE_BASELINE_CREATED
        if cand in ("validated", "validated_with_warnings"):
            state.status = ResearchCycleStageStatus.READY
        elif cand and cand.startswith("blocked"):
            state.stage = ResearchCycleStage.BLOCKED
            state.status = ResearchCycleStageStatus.BLOCKED_BY_SAFETY
        else:
            state.status = ResearchCycleStageStatus.WAITING_FOR_OPERATOR
    elif bundle.get("implementation_intake"):
        merge_status = intake.get("merge_recommendation_status", "")
        state.stage = ResearchCycleStage.IMPLEMENTATION_AUDITED
        if merge_status.startswith("block_merge_due_to_safety"):
            state.stage = ResearchCycleStage.BLOCKED
            state.status = ResearchCycleStageStatus.BLOCKED_BY_SAFETY
        elif merge_status.startswith("block_merge_due_to_tests"):
            state.stage = ResearchCycleStage.BLOCKED
            state.status = ResearchCycleStageStatus.BLOCKED_BY_TESTS
        elif merge_status.startswith("block"):
            state.stage = ResearchCycleStage.BLOCKED
            state.status = ResearchCycleStageStatus.BLOCKED_BY_MISSING_EVIDENCE
        else:
            state.stage = ResearchCycleStage.WAITING_FOR_HUMAN_MERGE
            state.status = ResearchCycleStageStatus.WAITING_FOR_OPERATOR
    elif bundle.get("experiment_compiler"):
        state.stage = ResearchCycleStage.WAITING_FOR_EXTERNAL_IMPLEMENTATION
        state.status = ResearchCycleStageStatus.WAITING_FOR_EXTERNAL_ARTIFACT
    elif bundle.get("architecture_evolution"):
        state.stage = ResearchCycleStage.ARCHITECTURE_EVIDENCE_LOADED
        state.status = ResearchCycleStageStatus.READY
    elif bundle.get("roadmap"):
        state.stage = ResearchCycleStage.ROADMAP_DEFINED
        state.status = ResearchCycleStageStatus.READY
    elif bundle.get("research_baseline_selected") or bundle.get("baseline_id"):
        state.stage = ResearchCycleStage.BASELINE_SELECTED
        state.status = ResearchCycleStageStatus.READY

    # Record any declared missing evidence.
    for key in ("research_baseline", "roadmap", "architecture_evolution",
                "experiment_compiler", "implementation_intake", "post_merge"):
        if not bundle.get(key):
            state.missing_evidence.append(key)
    return state
