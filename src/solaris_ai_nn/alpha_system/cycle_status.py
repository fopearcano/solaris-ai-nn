"""Alpha cycle status -- where an Alpha run is, and what to do next (descriptive).

:class:`AlphaCycleStatus` is a descriptive record of the Alpha run stage plus an
advisory next action. It is descriptive only: it never executes the next action,
and blockers are always explicit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AlphaCycleStage:
    NOT_INITIALIZED = "not_initialized"
    INITIALIZED = "initialized"
    DOCTOR_PASSED = "doctor_passed"
    DOCTOR_BLOCKED = "doctor_blocked"
    DEMO_READY = "demo_ready"
    DEMO_COMPLETED = "demo_completed"
    DEMO_COMPLETED_WITH_WARNINGS = "demo_completed_with_warnings"
    CLAIMS_GENERATED = "claims_generated"
    REVIEW_PACK_GENERATED = "review_pack_generated"
    CYCLE_STATUS_GENERATED = "cycle_status_generated"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"

    ALL = (NOT_INITIALIZED, INITIALIZED, DOCTOR_PASSED, DOCTOR_BLOCKED,
           DEMO_READY, DEMO_COMPLETED, DEMO_COMPLETED_WITH_WARNINGS,
           CLAIMS_GENERATED, REVIEW_PACK_GENERATED, CYCLE_STATUS_GENERATED,
           BLOCKED, UNKNOWN)


class AlphaNextAction:
    RUN_DOCTOR = "run_doctor"
    FIX_BLOCKERS = "fix_blockers"
    RUN_END_TO_END_DEMO = "run_end_to_end_demo"
    INSPECT_ALPHA_REPORT = "inspect_alpha_report"
    INSPECT_MISSING_MODULES = "inspect_missing_modules"
    RUN_CLAIMS_REPORT = "run_claims_report"
    RUN_REVIEW_PACK = "run_review_pack"
    PROCEED_TO_ARCHITECTURE_EVOLUTION = "proceed_to_architecture_evolution"
    PROCEED_TO_PROMPT_66 = "proceed_to_prompt_66"
    PAUSE = "pause"

    ALL = (RUN_DOCTOR, FIX_BLOCKERS, RUN_END_TO_END_DEMO, INSPECT_ALPHA_REPORT,
           INSPECT_MISSING_MODULES, RUN_CLAIMS_REPORT, RUN_REVIEW_PACK,
           PROCEED_TO_ARCHITECTURE_EVOLUTION, PROCEED_TO_PROMPT_66, PAUSE)


@dataclass
class AlphaCycleStatus:
    """The descriptive Alpha run stage + advisory next action."""

    stage: str = AlphaCycleStage.NOT_INITIALIZED
    next_action: str = AlphaNextAction.RUN_DOCTOR
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    detail: str = ""

    def __post_init__(self) -> None:
        if self.stage not in AlphaCycleStage.ALL:
            self.stage = AlphaCycleStage.UNKNOWN
        if self.next_action not in AlphaNextAction.ALL:
            self.next_action = AlphaNextAction.PAUSE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage, "next_action": self.next_action,
            "blocker_count": len(self.blockers),
            "blockers": list(self.blockers),
            "warning_count": len(self.warnings),
            "warnings": list(self.warnings),
            "detail": self.detail,
            "executes_next_action": False,
            "note": "alpha cycle status is descriptive only; it never executes "
                    "the next action and blockers are explicit",
        }


def determine_cycle_status(*, initialized: bool, doctor_blocked: bool,
                           demo_completed: bool, warnings: int,
                           blockers: Optional[List[str]] = None,
                           claims_generated: bool = False,
                           review_generated: bool = False,
                           ) -> AlphaCycleStatus:
    """Derive the descriptive cycle status from the run outcome."""
    blockers = list(blockers or [])
    if blockers or doctor_blocked:
        return AlphaCycleStatus(
            stage=(AlphaCycleStage.DOCTOR_BLOCKED if doctor_blocked
                   else AlphaCycleStage.BLOCKED),
            next_action=AlphaNextAction.FIX_BLOCKERS, blockers=blockers,
            detail="resolve the blockers before running the demo")
    if not initialized:
        return AlphaCycleStatus(
            stage=AlphaCycleStage.NOT_INITIALIZED,
            next_action=AlphaNextAction.RUN_DOCTOR,
            detail="initialize alpha state and run doctor")
    if not demo_completed:
        return AlphaCycleStatus(
            stage=AlphaCycleStage.DEMO_READY,
            next_action=AlphaNextAction.RUN_END_TO_END_DEMO,
            detail="state initialized and doctor passed; run the demo")
    stage = (AlphaCycleStage.DEMO_COMPLETED_WITH_WARNINGS if warnings
             else AlphaCycleStage.DEMO_COMPLETED)
    if review_generated:
        stage = AlphaCycleStage.REVIEW_PACK_GENERATED
    elif claims_generated:
        stage = AlphaCycleStage.CLAIMS_GENERATED
    return AlphaCycleStatus(
        stage=stage, next_action=AlphaNextAction.INSPECT_ALPHA_REPORT,
        warnings=["see skipped modules in the alpha report"] if warnings else [],
        detail=("demo completed" + (" with warnings" if warnings else "")
                + "; inspect the alpha report and the next-cycle options"))
