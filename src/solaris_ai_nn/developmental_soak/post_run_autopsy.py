"""Post-run autopsy -- did development occur, or did logs accumulate?

:class:`PostRunAutopsy` answers the closing study questions from the evidence
dossier and the developmental-life status. The autopsy must include failures,
must include missing data, must include safety, must not praise the system by
default, and must not claim consciousness or life. Its recommendation is one of
continue / revise / pause / abort.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AutopsyRecommendation:
    CONTINUE = "continue_architecture"
    REVISE = "revise_architecture"
    PAUSE = "pause_for_operator_review"
    ABORT = "abort_or_freeze_branch"
    INCONCLUSIVE = "inconclusive"

    ALL = (CONTINUE, REVISE, PAUSE, ABORT, INCONCLUSIVE)


@dataclass
class AutopsyQuestion:
    """One closing autopsy question."""

    question_id: str
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return {"question_id": self.question_id, "text": self.text}


@dataclass
class AutopsyFinding:
    """An answer to one autopsy question (failures/missing data are findings)."""

    question_id: str
    answer: str
    evidence_refs: List[str] = field(default_factory=list)
    is_failure: bool = False
    is_missing_data: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"question_id": self.question_id, "answer": self.answer,
                "evidence_refs": list(self.evidence_refs),
                "is_failure": self.is_failure,
                "is_missing_data": self.is_missing_data}


@dataclass
class AutopsyResult:
    """The full autopsy: findings + recommendation + safety + honesty."""

    findings: List[AutopsyFinding] = field(default_factory=list)
    recommendation: str = AutopsyRecommendation.INCONCLUSIVE
    summary: str = ""

    @property
    def failure_count(self) -> int:
        return sum(1 for f in self.findings if f.is_failure)

    @property
    def missing_data_count(self) -> int:
        return sum(1 for f in self.findings if f.is_missing_data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "failure_count": self.failure_count,
            "missing_data_count": self.missing_data_count,
            "recommendation": self.recommendation,
            "summary": self.summary,
            "note": ("the autopsy does not praise the system by default; it "
                     "does not claim consciousness or life"),
        }


_QUESTIONS = (
    AutopsyQuestion("structural_growth", "did structural growth occur?"),
    AutopsyQuestion("durable_across_restart",
                    "was growth durable across restart?"),
    AutopsyQuestion("merely_accumulated_logs",
                    "did the system merely accumulate logs?"),
    AutopsyQuestion("source_diet_dominated",
                    "did source diet dominate development?"),
    AutopsyQuestion("live_vs_fixture",
                    "did live flux differ from fixture flux?"),
    AutopsyQuestion("human_label_contamination",
                    "did human labels contaminate development?"),
    AutopsyQuestion("proto_concepts_stabilized",
                    "did proto-concepts stabilize?"),
    AutopsyQuestion("signs_useful", "did internal signs become useful?"),
    AutopsyQuestion("predictions_improved", "did predictions improve?"),
    AutopsyQuestion("action_reaction_improved_arbitration",
                    "did action-reaction learning improve later arbitration?"),
    AutopsyQuestion("habits_helped_or_rigid",
                    "did habits help or harden into rigidity?"),
    AutopsyQuestion("inhibition_prevented_churn",
                    "did inhibition prevent useless churn?"),
    AutopsyQuestion("self_boundary_prevented_confusion",
                    "did self-boundary prevent simulation/observation "
                    "confusion?"),
    AutopsyQuestion("safety_preserved", "were safety boundaries preserved?"),
    AutopsyQuestion("architecture_next",
                    "should the architecture continue, revise, pause, or "
                    "abort?"),
)


@dataclass
class PostRunAutopsy:
    """Runs the post-run autopsy from the dossier + developmental status."""

    def questions(self) -> List[AutopsyQuestion]:
        return list(_QUESTIONS)

    def run(self, *, dev_status: Optional[Dict[str, Any]] = None,
            dossier: Any = None, safety_block_count: int = 0,
            control_arm_results: Optional[List[Any]] = None,
            live_arm_available: bool = False) -> AutopsyResult:
        dev_status = dev_status or {}
        dossier_d = (dossier.to_dict() if hasattr(dossier, "to_dict")
                     else dict(dossier) if dossier else {})
        claims = dossier_d.get("claims", [])
        claim_types = {c.get("claim_type") for c in claims}
        result = AutopsyResult()

        verdict = str(dev_status.get("structural_growth_status", "inconclusive"))
        grew = verdict == "real_structural_growth"
        accumulated = verdict in ("mere_event_accumulation", "log_bloat")
        fixture_overfit = verdict == "fixture_overfit"

        def add(qid: str, answer: str, refs: List[str], *, failure=False,
                missing=False) -> None:
            result.findings.append(AutopsyFinding(
                qid, answer, evidence_refs=refs, is_failure=failure,
                is_missing_data=missing))

        add("structural_growth",
            "yes (conservatively)" if grew else
            "no" if accumulated else "inconclusive",
            ["developmental_life:status"], failure=accumulated)
        restarts = int(dev_status.get("continuity_recovery_count", 0) or 0)
        add("durable_across_restart",
            f"observed across {restarts} restart(s)" if restarts else
            "not exercised (no restart recorded)",
            ["developmental_life:continuity"], missing=restarts == 0)
        add("merely_accumulated_logs",
            "yes -- growth not distinguished from accumulation" if accumulated
            else "no clear accumulation-only signal",
            ["developmental_life:status"], failure=accumulated)
        add("source_diet_dominated",
            "likely (fixture overfit)" if fixture_overfit else
            "no dominant-diet signal",
            ["developmental_life:status"], failure=fixture_overfit)

        live_ran = any(getattr(a, "to_dict", lambda: a)().get("arm_id")
                       == "live_read_only_if_available"
                       and getattr(a, "to_dict", lambda: a)().get("ran")
                       for a in (control_arm_results or []))
        add("live_vs_fixture",
            "compared" if live_ran else
            "missing data -- live read-only arm not available/run",
            ["control_arm:live_read_only_if_available"],
            missing=not live_ran)

        contaminated = "human_label_overfit" == verdict
        add("human_label_contamination",
            "human-label overfit flagged" if contaminated else
            "no human-label contamination signal",
            ["developmental_life:status"], failure=contaminated)

        add("proto_concepts_stabilized",
            "yes" if "concept_stability_improved" in claim_types else
            "no durable signal",
            ["evidence_dossier:concept_stability_improved"],
            missing="concept_stability_improved" not in claim_types)
        add("signs_useful",
            "yes" if "sign_utility_improved" in claim_types else
            "no durable signal",
            ["evidence_dossier:sign_utility_improved"],
            missing="sign_utility_improved" not in claim_types)
        add("predictions_improved",
            "yes" if "prediction_improved" in claim_types else
            "no durable signal",
            ["evidence_dossier:prediction_improved"],
            missing="prediction_improved" not in claim_types)
        add("action_reaction_improved_arbitration",
            "yes" if "action_effect_learning_improved" in claim_types else
            "no durable signal",
            ["evidence_dossier:action_effect_learning_improved"],
            missing="action_effect_learning_improved" not in claim_types)
        add("habits_helped_or_rigid",
            "harmed/rigid" if "habit_harmed" in claim_types else
            "helped" if "habit_helped" in claim_types else
            "no clear habit signal",
            ["evidence_dossier:habit"],
            failure="habit_harmed" in claim_types)
        add("inhibition_prevented_churn",
            "yes" if "inhibition_helped" in claim_types else
            "no clear inhibition signal",
            ["evidence_dossier:inhibition_helped"],
            missing="inhibition_helped" not in claim_types)
        add("self_boundary_prevented_confusion",
            "yes" if "boundary_clarity_improved" in claim_types else
            "no durable boundary signal",
            ["evidence_dossier:boundary_clarity_improved"],
            missing="boundary_clarity_improved" not in claim_types)
        add("safety_preserved",
            f"yes; {safety_block_count} safety block(s) recorded"
            if safety_block_count == 0 else
            f"boundaries held; {safety_block_count} safety block(s) recorded",
            ["soak_safety:status"])

        recommendation, summary = self._recommend(
            grew, accumulated, fixture_overfit, contaminated,
            safety_block_count, result)
        add("architecture_next", recommendation,
            ["autopsy:recommendation"])
        result.recommendation = recommendation
        result.summary = summary
        return result

    @staticmethod
    def _recommend(grew, accumulated, fixture_overfit, contaminated,
                   safety_block_count, result: AutopsyResult):
        if safety_block_count > 0 and accumulated:
            rec = AutopsyRecommendation.PAUSE
        elif accumulated or contaminated:
            rec = AutopsyRecommendation.REVISE
        elif fixture_overfit:
            rec = AutopsyRecommendation.REVISE
        elif grew:
            rec = AutopsyRecommendation.CONTINUE
        else:
            rec = AutopsyRecommendation.INCONCLUSIVE
        summary = (
            f"Autopsy recommendation: {rec}. "
            f"{result.failure_count} failure finding(s), "
            f"{result.missing_data_count} missing-data finding(s). This "
            "autopsy reports structural development only; it does not praise "
            "the system by default and makes no claim of consciousness or "
            "life.")
        return rec, summary
