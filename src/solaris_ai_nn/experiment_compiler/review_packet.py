"""Operator review packet -- the human decision point (no self-approval).

:class:`OperatorReviewPacket` summarizes an evidence + proposed implementation +
risks + blocked claims for a *human operator*, with yes/no review questions and a
recommended next step. It does not approve itself; no decision is automatic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ReviewDecision:
    APPROVE_FOR_EXTERNAL_AGENT = "approve_for_external_agent"
    REVISE_SPEC = "revise_spec"
    REQUEST_MORE_EVIDENCE = "request_more_evidence"
    RUN_ABLATION_FIRST = "run_ablation_first"
    RUN_FALSIFICATION_FIRST = "run_falsification_first"
    BLOCK_FOR_SAFETY = "block_for_safety"
    ARCHIVE = "archive"

    ALL = (APPROVE_FOR_EXTERNAL_AGENT, REVISE_SPEC, REQUEST_MORE_EVIDENCE,
           RUN_ABLATION_FIRST, RUN_FALSIFICATION_FIRST, BLOCK_FOR_SAFETY,
           ARCHIVE)


@dataclass
class ReviewQuestion:
    """A yes/no question the operator must answer (default unanswered)."""

    question: str
    answer: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"question": self.question, "answer": self.answer}


@dataclass
class OperatorReviewPacket:
    """The human-operator decision packet for one compiled spec."""

    spec_id: str
    purpose: str = ""
    evidence_summary: List[str] = field(default_factory=list)
    proposed_implementation: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    blocked_claims: List[str] = field(default_factory=list)
    required_operator_decisions: List[str] = field(default_factory=list)
    review_questions: List[ReviewQuestion] = field(default_factory=list)
    recommended_next_step: str = ""
    # The decision is set by a human; the packet never sets it itself.
    decision: Optional[str] = None

    def render_markdown(self) -> str:
        lines = [f"# Operator Review Packet -- {self.spec_id}", "",
                 f"_Purpose: {self.purpose}_", "",
                 "## Evidence summary", ""]
        lines += [f"- {e}" for e in self.evidence_summary]
        lines += ["", "## Proposed implementation", ""]
        lines += [f"- {p}" for p in self.proposed_implementation]
        lines += ["", "## Risks", ""]
        lines += [f"- {r}" for r in self.risks]
        lines += ["", "## Blocked claims", ""]
        lines += [f"- {b}" for b in self.blocked_claims] or ["- none"]
        lines += ["", "## Review questions (operator answers)", ""]
        lines += [f"- [ ] {q.question}" for q in self.review_questions]
        lines += ["", f"## Recommended next step", "",
                  self.recommended_next_step, "",
                  "_This packet does not approve itself. No decision is "
                  "automatic; a human operator must decide._"]
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spec_id": self.spec_id, "purpose": self.purpose,
            "evidence_summary": list(self.evidence_summary),
            "proposed_implementation": list(self.proposed_implementation),
            "risks": list(self.risks),
            "blocked_claims": list(self.blocked_claims),
            "required_operator_decisions":
                list(self.required_operator_decisions),
            "review_questions": [q.to_dict() for q in self.review_questions],
            "recommended_next_step": self.recommended_next_step,
            "decision": self.decision, "self_approved": False,
            "available_decisions": list(ReviewDecision.ALL),
        }


@dataclass
class ReviewPacketBuilder:
    """Builds an operator review packet from a compiled spec + gate summary."""

    def build(self, spec: Dict[str, Any], *,
              gate_summary: Optional[Dict[str, Any]] = None,
              ) -> OperatorReviewPacket:
        gate_summary = gate_summary or {}
        blocked = bool(spec.get("blocked"))
        critical_fail = not gate_summary.get("all_critical_passed", True)
        recommended = self._recommend(spec, blocked, critical_fail)
        questions = [
            ReviewQuestion("Is the source evidence sufficient and not "
                           "falsified?"),
            ReviewQuestion("Do all critical safety gates pass?"),
            ReviewQuestion("Are the required tests (incl. safety + ClaimGuard) "
                           "specified?"),
            ReviewQuestion("Should this be handed to an external coding agent "
                           "now?"),
            ReviewQuestion("Should a Git branch / PR be created manually after "
                           "review?")]
        return OperatorReviewPacket(
            spec_id=spec.get("spec_id", "spec"),
            purpose=spec.get("purpose", ""),
            evidence_summary=list(spec.get("evidence_refs", []))
            or ["no evidence refs supplied"],
            proposed_implementation=list(spec.get("proposed_changes", [])),
            risks=list(spec.get("limitations", [])),
            blocked_claims=([spec.get("block_reason")] if spec.get("block_reason")
                            else []),
            required_operator_decisions=[
                "approve / revise / request-evidence / run-ablation-first / "
                "run-falsification-first / block-for-safety / archive"],
            review_questions=questions,
            recommended_next_step=recommended)

    @staticmethod
    def _recommend(spec: Dict[str, Any], blocked: bool,
                   critical_fail: bool) -> str:
        if critical_fail:
            return ("Recommended: block_for_safety -- a critical safety gate "
                    "failed.")
        if spec.get("status") == "blocked_by_falsification":
            return ("Recommended: run_falsification_first -- the proposal rests "
                    "on falsified evidence.")
        if spec.get("status") == "blocked_by_missing_evidence":
            return ("Recommended: request_more_evidence / run_ablation_first -- "
                    "evidence is inconclusive.")
        if blocked:
            return "Recommended: block_for_safety / archive."
        return ("Recommended: approve_for_external_agent after confirming the "
                "safety gates and tests (operator decides).")
