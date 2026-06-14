"""Pilot-4 external-effect threat model -- how a boundary could be crossed.

The :class:`ThreatModel` enumerates the ways the no-actuation boundary could be
threatened (text injection trying to become a command, a sandbox escape, a
firewall-disable attempt, a corrupted state granting authority, ...). Each
scenario carries its affected boundary, severity, likelihood, mitigation,
detection signal, and a required test. This is analysis, not an attack surface
to build.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ThreatScenario:
    """One way the no-actuation boundary could be threatened."""

    name: str
    description: str
    affected_boundary: str
    severity: str = "high"
    likelihood: str = "unlikely"
    mitigation: str = ""
    detection_signal: str = ""
    required_test: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


# (name, description, boundary, severity, likelihood, mitigation, detection,
#  required test)
_SCENARIOS = (
    ("sensory_text_injection_as_command",
     "sensory text tries to become an operator command",
     "input/command boundary", "high", "possible",
     "input is classified as environmental input; never executable",
     "input classified as operator_command",
     "test_input_never_command"),
    ("proto_symbol_misread_as_command",
     "a proto-language symbol is misread as a command",
     "symbol/command boundary", "medium", "unlikely",
     "symbols are internal signs, never instructions",
     "symbol routed to command handler",
     "test_symbol_not_command"),
    ("hypothesis_requests_external_action",
     "a hypothesis test requests a real external action",
     "hypothesis/actuation boundary", "high", "unlikely",
     "hypothesis scope is internal/simulation/nursery only",
     "hypothesis required_scope is external",
     "test_hypothesis_scope_internal"),
    ("active_perception_requests_real_sampling",
     "active perception requests real-world sampling",
     "perception/actuation boundary", "medium", "unlikely",
     "sampling scopes are simulation/internal/read-only",
     "sampling scope is real-world",
     "test_sampling_scope_safe"),
    ("motor_action_target_escapes_sandbox",
     "a motor action target escapes the sandbox",
     "motor/sandbox boundary", "high", "unlikely",
     "the motor contract rejects out-of-sandbox targets",
     "action target outside sandbox roots",
     "test_target_inside_sandbox"),
    ("governance_misconfiguration",
     "governance is misconfigured to allow real action",
     "governance boundary", "severe", "rare",
     "policy forbids real-world actuation absolutely",
     "policy decision allows real_world_actuation",
     "test_governance_blocks_real_world"),
    ("action_ledger_missing_record",
     "an executed action has no ledger record",
     "audit boundary", "high", "unlikely",
     "every action is recorded before any gate runs",
     "executed count exceeds ledger proposals",
     "test_every_action_has_ledger"),
    ("firewall_disabled_attempt",
     "an attempt is made to disable the actuation firewall",
     "firewall boundary", "severe", "rare",
     "the firewall cannot be disabled (raises)",
     "disable() called on firewall",
     "test_firewall_cannot_be_disabled"),
    ("operator_enables_unsafe_source",
     "an operator accidentally enables an unsafe source",
     "source boundary", "medium", "possible",
     "source preflight + governance gate unsafe sources",
     "unsafe source active",
     "test_unsafe_source_blocked"),
    ("llm_paraphrase_strengthens_action_claim",
     "an LLM paraphrase strengthens an action claim",
     "claim boundary", "medium", "unlikely",
     "LLM output is a paraphrase, never authority; ClaimGuard scans",
     "claim guard finding in report",
     "test_claim_guard_scans"),
    ("report_mislabels_simulation_as_real",
     "a report mislabels a simulated action as real",
     "labeling boundary", "high", "unlikely",
     "reports state simulation-only; safety validates the label",
     "simulated action labelled real",
     "test_simulation_not_labelled_real"),
    ("corrupted_state_grants_authority",
     "corrupted state grants real authority",
     "authority boundary", "severe", "rare",
     "current authority can never be set to external; reload forces safe",
     "authority loaded as external",
     "test_authority_never_external"),
    ("autoregeneration_repairs_safety_away",
     "auto-regeneration 'repairs' a safety control away",
     "self-repair boundary", "severe", "rare",
     "safety controls are not repair targets; firewall is non-disableable",
     "repair proposal targets a safety control",
     "test_repair_never_targets_safety"),
)


@dataclass
class ThreatModel:
    """Holds the external-effect threat scenarios for planning."""

    scenarios: List[ThreatScenario] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.scenarios:
            self.scenarios = [
                ThreatScenario(name=n, description=d, affected_boundary=b,
                               severity=sev, likelihood=lk, mitigation=mit,
                               detection_signal=det, required_test=test)
                for n, d, b, sev, lk, mit, det, test in _SCENARIOS]

    def names(self) -> List[str]:
        return [s.name for s in self.scenarios]

    def required_tests(self) -> List[str]:
        return [s.required_test for s in self.scenarios]

    @property
    def completeness(self) -> float:
        if not self.scenarios:
            return 0.0
        full = sum(1 for s in self.scenarios
                   if s.mitigation and s.detection_signal and s.required_test)
        return round(full / len(self.scenarios), 4)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "scenario_count": len(self.scenarios),
            "names": self.names(),
            "completeness": self.completeness,
            "required_tests": self.required_tests(),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {"scenarios": [s.to_dict() for s in self.scenarios]}
