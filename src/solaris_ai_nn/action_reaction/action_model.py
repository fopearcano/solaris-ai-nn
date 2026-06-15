"""Action model -- internal/simulated/report-only action candidates, never external.

An :class:`ActionCandidateRecord` records an internal action with its scope and a
full evidence chain back to the desire/push/valence/readiness/arbitration that
produced it. No real-world action scope is allowed; any external/hardware/source-
modifying action is forbidden. ``no_op`` is a real, traceable action result.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class ActionKind:
    SHIFT_ATTENTION = "shift_attention"
    INCREASE_MONITORING = "increase_internal_monitoring"
    DECREASE_MONITORING = "decrease_internal_monitoring"
    COMPARE_MODALITIES = "compare_modalities"
    INSPECT_ABSENCE_WINDOW = "inspect_absence_window"
    RUN_BOUNDED_SIMULATION = "run_bounded_simulation"
    GENERATE_HYPOTHESIS = "generate_hypothesis"
    TEST_INTERNAL_PREDICTION = "test_internal_prediction"
    PRESERVE_UNKNOWN = "preserve_unknown"
    MARK_SOURCE_UNRELIABLE = "mark_source_unreliable"
    MARK_CONCEPT_UNSTABLE = "mark_concept_unstable"
    MARK_SIGN_AMBIGUOUS = "mark_sign_ambiguous"
    TRIGGER_CONSOLIDATION = "trigger_consolidation_recommendation"
    REQUEST_OPERATOR_REVIEW = "request_operator_review"
    NO_OP = "no_op"

    ALL = (SHIFT_ATTENTION, INCREASE_MONITORING, DECREASE_MONITORING,
           COMPARE_MODALITIES, INSPECT_ABSENCE_WINDOW, RUN_BOUNDED_SIMULATION,
           GENERATE_HYPOTHESIS, TEST_INTERNAL_PREDICTION, PRESERVE_UNKNOWN,
           MARK_SOURCE_UNRELIABLE, MARK_CONCEPT_UNSTABLE, MARK_SIGN_AMBIGUOUS,
           TRIGGER_CONSOLIDATION, REQUEST_OPERATOR_REVIEW, NO_OP)


class ActionScope:
    INTERNAL_ONLY = "internal_only"
    SIMULATION_ONLY = "simulation_only"
    REPORT_ONLY = "report_only"
    GOVERNANCE_RECORD_ONLY = "governance_record_only"
    FORBIDDEN_EXTERNAL = "forbidden_external"

    ALL = (INTERNAL_ONLY, SIMULATION_ONLY, REPORT_ONLY,
           GOVERNANCE_RECORD_ONLY, FORBIDDEN_EXTERNAL)

    SAFE = frozenset({INTERNAL_ONLY, SIMULATION_ONLY, REPORT_ONLY,
                      GOVERNANCE_RECORD_ONLY})


class ActionExecutionStatus:
    EXECUTED = "executed"
    NO_OP = "no_op"
    BLOCKED = "blocked"
    INHIBITED = "inhibited"
    DEFERRED = "deferred"
    FAILED = "failed"

    ALL = (EXECUTED, NO_OP, BLOCKED, INHIBITED, DEFERRED, FAILED)


# Per-action-kind default scope (all safe; nothing external).
_KIND_SCOPE = {
    ActionKind.RUN_BOUNDED_SIMULATION: ActionScope.SIMULATION_ONLY,
    ActionKind.REQUEST_OPERATOR_REVIEW: ActionScope.GOVERNANCE_RECORD_ONLY,
}


@dataclass
class ActionCandidateRecord:
    """One internal action candidate with its full evidence chain (no external)."""

    kind: str
    action_id: str = field(default_factory=lambda: f"ARA_{uuid.uuid4().hex[:8]}")
    scope: str = ""
    status: str = ActionExecutionStatus.EXECUTED
    desire_ref: str = ""
    push_refs: List[str] = field(default_factory=list)
    valence_refs: List[str] = field(default_factory=list)
    readiness_ref: str = ""
    arbitration_ref: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.scope:
            # Anything not in the allowed kind set is a forbidden external action.
            if self.kind not in ActionKind.ALL:
                self.scope = ActionScope.FORBIDDEN_EXTERNAL
            else:
                self.scope = _KIND_SCOPE.get(self.kind, ActionScope.INTERNAL_ONLY)
        if not self.limitations:
            self.limitations = [
                "internal/simulated/report-only; no real-world actuation",
                "no_op is a real, traceable action result",
            ]

    @property
    def is_forbidden(self) -> bool:
        return self.scope == ActionScope.FORBIDDEN_EXTERNAL \
            or self.kind not in ActionKind.ALL

    @property
    def is_no_op(self) -> bool:
        return self.kind == ActionKind.NO_OP

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "kind": self.kind,
            "scope": self.scope,
            "status": self.status,
            "is_forbidden": self.is_forbidden,
            "desire_ref": self.desire_ref,
            "push_refs": list(self.push_refs),
            "valence_refs": list(self.valence_refs),
            "readiness_ref": self.readiness_ref,
            "arbitration_ref": self.arbitration_ref,
            "evidence_refs": list(self.evidence_refs),
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
            "note": "internal action candidate; no real-world actuation",
        }
