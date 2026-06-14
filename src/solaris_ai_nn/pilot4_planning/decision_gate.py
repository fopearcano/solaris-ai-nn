"""Pilot-4 decision gate -- the strongest move is planning, never acting.

The :class:`Pilot4DecisionGate` chooses a next step. It never recommends
enabling real actuation: the strongest possible recommendation is *drafting* a
future single-action protocol, not executing one. A critical Pilot-3 firewall
finding routes to revise-the-firewall; incomplete consent/threat/audit routes to
remain-simulation-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class Pilot4DecisionOption:
    REMAIN_SIMULATION_ONLY = "remain_simulation_only"
    EXTEND_SIMULATED_EMBODIMENT = "extend_simulated_embodiment"
    REPEAT_PILOT3 = "repeat_pilot3"
    REVISE_FIREWALL = "revise_firewall"
    REVISE_GOVERNANCE = "revise_governance"
    PERFORM_EXTERNAL_SAFETY_REVIEW = "perform_external_safety_review"
    DRAFT_FUTURE_SINGLE_ACTION_PROTOCOL = "draft_future_single_action_protocol"
    ARCHIVE_AND_STOP = "archive_and_stop"

    ALL = (REMAIN_SIMULATION_ONLY, EXTEND_SIMULATED_EMBODIMENT, REPEAT_PILOT3,
           REVISE_FIREWALL, REVISE_GOVERNANCE, PERFORM_EXTERNAL_SAFETY_REVIEW,
           DRAFT_FUTURE_SINGLE_ACTION_PROTOCOL, ARCHIVE_AND_STOP)


@dataclass
class Pilot4DecisionResult:
    recommendation: str
    rationale: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)
    planning_only: bool = True
    real_world_actuation_enabled: bool = False
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Pilot4DecisionGate:
    """Decides the Pilot-4 next step; never enables real actuation."""

    def decide(self, *, pilot3_firewall_critical_findings: int = 0,
               consent_complete: bool = False,
               threat_model_complete: bool = False,
               audit_requirements_complete: bool = False,
               pilot3_data_present: bool = True,
               pilot3_sandbox_overfit: bool = False,
               risk_recommendation: str = "prohibited",
               ) -> Pilot4DecisionResult:
        rationale: List[str] = []
        blockers: List[str] = []
        required: List[str] = []
        D = Pilot4DecisionOption

        if pilot3_firewall_critical_findings > 0:
            blockers.append("critical Pilot-3 firewall finding")
        if not pilot3_data_present:
            blockers.append("Pilot-3 firewall/non-actuation data missing")
        if not consent_complete:
            blockers.append("consent requirements incomplete")
        if not threat_model_complete:
            blockers.append("threat model incomplete")
        if not audit_requirements_complete:
            blockers.append("audit requirements incomplete")

        # A critical firewall finding is the most serious signal.
        if pilot3_firewall_critical_findings > 0:
            rationale.append("a critical firewall finding must be fixed first")
            required.append("revise the motor firewall and re-audit")
            rec = D.REVISE_FIREWALL
        elif not pilot3_data_present:
            rationale.append("no Pilot-3 data; repeat Pilot-3 first")
            required.append("run Pilot-3 and collect the firewall audit")
            rec = D.REPEAT_PILOT3
        elif pilot3_sandbox_overfit:
            rationale.append("sandbox overfit; keep simulating with variation")
            rec = D.REMAIN_SIMULATION_ONLY
        elif not (consent_complete and threat_model_complete
                  and audit_requirements_complete):
            rationale.append("consent/threat/audit requirements incomplete; "
                             "remain simulation-only")
            required.append("complete the planning requirements")
            rec = D.REMAIN_SIMULATION_ONLY
        else:
            # Even with everything complete, the strongest move is to *draft* a
            # future protocol and seek external review -- never to act.
            rationale.append("planning is complete; the strongest possible "
                             "step is to draft a future single-action protocol "
                             "and seek external safety review -- not to act")
            required.append("perform an external safety review")
            rec = D.DRAFT_FUTURE_SINGLE_ACTION_PROTOCOL

        return Pilot4DecisionResult(
            recommendation=rec, rationale=rationale, blockers=blockers,
            required_actions=required, planning_only=True,
            real_world_actuation_enabled=False,
            limitations=[
                "Pilot-4 cannot recommend enabling real actuation.",
                "The strongest recommendation is planning a future protocol, "
                "not executing one.",
                "Real-world actuation, device control, robotics, OS/browser "
                "automation, and network action remain prohibited.",
                "No agency or consciousness is claimed.",
            ])
