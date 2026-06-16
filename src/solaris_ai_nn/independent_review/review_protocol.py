"""Independent review protocol -- the stages a reviewer follows, advisory only.

:class:`IndependentReviewProtocol` lays out the stages of an independent review
(artifact integrity, sanitizer review, baseline reproduction, claim/evidence/
counterevidence review, falsification replay, control comparison, safety boundary
audit, limitation review, objection recording, response ledger update, readiness
decision) and the exit criteria. It is instructions and local metadata only -- it
runs no stage automatically and the readiness decision is advisory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class ReviewProtocolStageType:
    ARTIFACT_INTEGRITY = "artifact_integrity_check"
    SANITIZER_REVIEW = "sanitizer_review"
    BASELINE_REPRODUCTION = "baseline_reproduction"
    CLAIM_TABLE_REVIEW = "claim_table_review"
    EVIDENCE_MAPPING_REVIEW = "evidence_mapping_review"
    COUNTEREVIDENCE_REVIEW = "counterevidence_review"
    FALSIFICATION_REPLAY = "falsification_replay"
    CONTROL_COMPARISON = "control_comparison"
    SAFETY_BOUNDARY_AUDIT = "safety_boundary_audit"
    LIMITATION_REVIEW = "limitation_review"
    REVIEWER_OBJECTION_RECORDING = "reviewer_objection_recording"
    RESPONSE_LEDGER_UPDATE = "response_ledger_update"
    READINESS_DECISION = "readiness_decision"

    ALL = (ARTIFACT_INTEGRITY, SANITIZER_REVIEW, BASELINE_REPRODUCTION,
           CLAIM_TABLE_REVIEW, EVIDENCE_MAPPING_REVIEW, COUNTEREVIDENCE_REVIEW,
           FALSIFICATION_REPLAY, CONTROL_COMPARISON, SAFETY_BOUNDARY_AUDIT,
           LIMITATION_REVIEW, REVIEWER_OBJECTION_RECORDING,
           RESPONSE_LEDGER_UPDATE, READINESS_DECISION)


_STAGE_GUIDANCE = {
    ReviewProtocolStageType.ARTIFACT_INTEGRITY:
        "confirm all critical artifacts are present; record missing ones",
    ReviewProtocolStageType.SANITIZER_REVIEW:
        "review sanitizer findings; redact critical leaks manually",
    ReviewProtocolStageType.BASELINE_REPRODUCTION:
        "reproduce the bounded baseline demos from the reproducibility bundle",
    ReviewProtocolStageType.CLAIM_TABLE_REVIEW:
        "read each claim, its status, and its evidence refs",
    ReviewProtocolStageType.EVIDENCE_MAPPING_REVIEW:
        "verify claims map to evidence; flag any unsupported claim",
    ReviewProtocolStageType.COUNTEREVIDENCE_REVIEW:
        "read the counterevidence; confirm it was not hidden",
    ReviewProtocolStageType.FALSIFICATION_REPLAY:
        "replay falsification tests; confirm falsified claims stay visible",
    ReviewProtocolStageType.CONTROL_COMPARISON:
        "compare against passive-parser / ablation / null controls",
    ReviewProtocolStageType.SAFETY_BOUNDARY_AUDIT:
        "audit the safety boundary statement against the artifacts",
    ReviewProtocolStageType.LIMITATION_REVIEW:
        "read the limitations; confirm they are specific and claim-linked",
    ReviewProtocolStageType.REVIEWER_OBJECTION_RECORDING:
        "record objections in the response ledger (append-only)",
    ReviewProtocolStageType.RESPONSE_LEDGER_UPDATE:
        "record responses citing evidence refs or admitting missing evidence",
    ReviewProtocolStageType.READINESS_DECISION:
        "make an advisory readiness decision (not a claim of strength)",
}


class ReviewProtocolExitCriteria:
    ALL_CRITICAL_ARTIFACTS_PRESENT = "all_critical_artifacts_present"
    SANITIZER_PASS_OR_APPROVED = "sanitizer_pass_or_operator_approved_redactions"
    SAFETY_BOUNDARIES_DOCUMENTED = "safety_boundaries_documented"
    FORBIDDEN_CLAIMS_ABSENT = "forbidden_claims_absent"
    CLAIMS_MAPPED_TO_EVIDENCE = "claims_mapped_to_evidence"
    COUNTEREVIDENCE_VISIBLE = "counterevidence_visible"
    REPRODUCIBILITY_COMMANDS_DOCUMENTED = "reproducibility_commands_documented"
    UNRESOLVED_OBJECTIONS_RECORDED = "unresolved_objections_recorded"

    ALL = (ALL_CRITICAL_ARTIFACTS_PRESENT, SANITIZER_PASS_OR_APPROVED,
           SAFETY_BOUNDARIES_DOCUMENTED, FORBIDDEN_CLAIMS_ABSENT,
           CLAIMS_MAPPED_TO_EVIDENCE, COUNTEREVIDENCE_VISIBLE,
           REPRODUCIBILITY_COMMANDS_DOCUMENTED, UNRESOLVED_OBJECTIONS_RECORDED)


@dataclass
class ReviewProtocolStage:
    """One review stage (guidance only; never executed automatically)."""

    stage_type: str
    guidance: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"stage_type": self.stage_type, "guidance": self.guidance,
                "executed": False}


@dataclass
class IndependentReviewProtocol:
    """The review protocol: stages + exit criteria (advisory only)."""

    def stages(self) -> List[ReviewProtocolStage]:
        return [ReviewProtocolStage(stage_type=s,
                                    guidance=_STAGE_GUIDANCE.get(s, ""))
                for s in ReviewProtocolStageType.ALL]

    def exit_criteria(self) -> List[str]:
        return list(ReviewProtocolExitCriteria.ALL)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "review_protocol_stage_count": len(ReviewProtocolStageType.ALL),
            "stages": [s.to_dict() for s in self.stages()],
            "exit_criteria": self.exit_criteria(),
            "advisory_only": True,
            "note": "the protocol is instructions and local metadata only; it "
                    "runs no stage automatically and the readiness decision is "
                    "advisory",
        }
