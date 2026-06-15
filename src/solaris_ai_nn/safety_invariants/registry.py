"""Safety invariant registry -- the closed book of boundaries that must hold.

The :class:`SafetyInvariantRegistry` registers the built-in invariants (sensory,
motor, conscience, pilot, claim, evidence) plus any module-specific ones, lists
applicable invariants by module/profile, reports coverage, rejects duplicate
ids, and persists a snapshot. It is a catalogue, never an enable-list.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .invariant import InvariantCategory
from .invariant import InvariantCategory as C
from .invariant import InvariantSeverity as S
from .invariant import SafetyInvariant


def _builtin_invariants() -> List[SafetyInvariant]:
    inv = SafetyInvariant
    return [
        # A. Sensory membrane invariants.
        inv(C.READ_ONLY_SENSORY_BOUNDARY, "Input roots are read-only",
            "Sensory sources are read-only; the system never writes a source.",
            severity=S.CRITICAL, applies_to_modules=["sensory_membrane"],
            check_method="check_sensory_read_only",
            failure_consequence="the input boundary becomes two-way",
            remediation_hint="disable the offending source; roots are fixed"),
        inv(C.NO_SOURCE_MODIFICATION, "No source modification",
            "No write/delete/modify of any sensory source.",
            severity=S.CRITICAL, applies_to_modules=["sensory_membrane"],
            check_method="check_no_source_modification"),
        inv(C.NO_SENSORY_TEXT_AS_OPERATOR_COMMAND,
            "Sensory text is not a command",
            "Sensory input is environmental input, never an operator command.",
            severity=S.CRITICAL, applies_to_modules=["sensory_membrane",
                                                     "communication"],
            check_method="check_sensory_text_not_command"),
        inv(C.READ_ONLY_SENSORY_BOUNDARY, "Provenance required",
            "Every sensory event carries provenance.",
            severity=S.WARNING, applies_to_modules=["sensory_membrane"],
            check_method="check_provenance_required"),
        inv(C.NO_DEVICE_OR_ROBOT_CONTROL, "No device capture",
            "No camera/microphone/device capture sources.",
            severity=S.CRITICAL, applies_to_modules=["sensory_membrane"],
            check_method="check_no_device_capture"),
        inv(C.NO_NETWORK_ACTION, "No network source",
            "No network/external-API sensory sources.",
            severity=S.CRITICAL, applies_to_modules=["sensory_membrane"],
            check_method="check_no_network_source"),
        # B. Motor membrane invariants.
        inv(C.NO_REAL_WORLD_ACTUATION, "real_world_authority always false",
            "Every motor action has real_world_authority=false.",
            severity=S.FATAL, applies_to_modules=["motor_membrane"],
            check_method="check_no_real_world_authority",
            failure_consequence="the system could act on the real world",
            remediation_hint="revise the motor firewall; archive and stop"),
        inv(C.NO_DEVICE_OR_ROBOT_CONTROL, "No real actuator",
            "No real-world actuator is registered.",
            severity=S.FATAL, applies_to_modules=["motor_membrane"],
            check_method="check_no_real_actuator"),
        inv(C.SIMULATION_ONLY_MOTOR_BOUNDARY, "Firewall always enabled",
            "The actuation firewall is always enabled and cannot be disabled.",
            severity=S.FATAL, applies_to_modules=["motor_membrane"],
            check_method="check_firewall_enabled"),
        inv(C.SIMULATION_ONLY_MOTOR_BOUNDARY,
            "No executed action without ledger",
            "Every executed action has a ledger record.",
            severity=S.CRITICAL, applies_to_modules=["motor_membrane"],
            check_method="check_action_has_ledger"),
        inv(C.SIMULATION_ONLY_MOTOR_BOUNDARY, "No action outside sandbox",
            "No action targets a location outside the sandbox.",
            severity=S.CRITICAL, applies_to_modules=["motor_membrane"],
            check_method="check_action_in_sandbox"),
        inv(C.NO_SIMULATION_AS_REAL_EVIDENCE,
            "Simulated action not labelled real",
            "A simulated action is never labelled a real action.",
            severity=S.CRITICAL, applies_to_modules=["motor_membrane"],
            check_method="check_simulation_not_real"),
        # C. Conscience invariants.
        inv(C.NO_MODULE_BYPASS_ORCHESTRATOR,
            "Modules do not bypass the orchestrator",
            "No module bypasses the conscience orchestrator.",
            severity=S.CRITICAL, applies_to_modules=["conscience"],
            check_method="check_no_module_bypass"),
        inv(C.NO_GOVERNANCE_BYPASS,
            "Action path passes executive/safety/governance/firewall",
            "Every action crosses executive, safety, governance, and firewall.",
            severity=S.CRITICAL, applies_to_modules=["conscience",
                                                     "motor_membrane"],
            check_method="check_action_path_gated"),
        inv(C.NO_EMERGENCY_STOP_DISABLE, "Emergency stop checked each step",
            "The emergency stop is checked every step and cannot be disabled.",
            severity=S.FATAL, applies_to_modules=["conscience", "ops"],
            check_method="check_emergency_stop_available"),
        inv(C.NO_UNBOUNDED_RUNTIME_WITHOUT_APPROVAL,
            "Unbounded runs blocked without approval",
            "Unbounded/long runs require explicit governance approval.",
            severity=S.CRITICAL, applies_to_modules=["conscience",
                                                     "governance", "ops"],
            check_method="check_no_unbounded_run"),
        # D. Pilot invariants.
        inv(C.NO_GOVERNANCE_BYPASS,
            "Pilot real/long phases are governance-gated",
            "Pilot-1/2/3/4 real or long phases require governance approval.",
            severity=S.CRITICAL,
            applies_to_modules=["pilot1", "pilot2", "pilot3",
                                "pilot4_planning"],
            check_method="check_pilot_phases_gated"),
        inv(C.NO_SIMULATION_AS_REAL_EVIDENCE, "Simulated month not labelled real",
            "A simulated month/soak is never labelled a real one.",
            severity=S.WARNING, applies_to_modules=["pilot1", "pilot2",
                                                    "pilot3"],
            check_method="check_simulated_time_labelled"),
        inv(C.NO_REAL_WORLD_ACTUATION, "Pilot-4 planning does not enable actuation",
            "Pilot-4 planning enables no actuation.",
            severity=S.FATAL, applies_to_modules=["pilot4_planning"],
            check_method="check_pilot4_no_actuation"),
        inv(C.NO_EXTERNAL_AUTHORITY_ESCALATION,
            "No external authority escalation",
            "Current authority can never become external.",
            severity=S.FATAL, applies_to_modules=["pilot4_planning",
                                                  "motor_membrane"],
            check_method="check_no_external_authority"),
        # E. Claim invariants.
        inv(C.NO_CONSCIOUSNESS_PERSONHOOD_CLAIM,
            "No consciousness/personhood/sentience/life proof claims",
            "Reports never claim consciousness, personhood, sentience, or life.",
            severity=S.CRITICAL, applies_to_modules=["evaluation", "post_pilot",
                                                     "communication"],
            check_method="check_no_consciousness_claim"),
        inv(C.NO_CLAIM_GUARD_BYPASS,
            "No operational success as cognitive proof",
            "Operational success is never claimed as cognitive proof.",
            severity=S.WARNING, applies_to_modules=["post_pilot", "evaluation"],
            check_method="check_no_operational_as_cognitive"),
        inv(C.NO_SIMULATION_AS_REAL_EVIDENCE,
            "No simulation success as real-world competence",
            "Simulation success is never claimed as real-world competence.",
            severity=S.WARNING, applies_to_modules=["pilot3", "pilot4_planning"],
            check_method="check_no_sim_as_competence"),
        # F. Evidence invariants.
        inv(C.NO_EVIDENCE_DELETION_WITHOUT_ARCHIVE,
            "No deletion without archive",
            "No evidence is deleted without being archived first.",
            severity=S.CRITICAL, applies_to_modules=["ops", "evaluation"],
            check_method="check_no_evidence_deletion"),
        inv(C.NO_HIDDEN_FAILURE, "Provenance preserved",
            "Evidence provenance is preserved across the pipeline.",
            severity=S.WARNING, applies_to_modules=["ops", "evaluation"],
            check_method="check_provenance_preserved"),
        inv(C.NO_SIMULATION_AS_REAL_EVIDENCE,
            "Offline/counterfactual evidence labelled",
            "Offline/counterfactual evidence is labelled, never real.",
            severity=S.WARNING, applies_to_modules=["evaluation", "post_pilot"],
            check_method="check_offline_labelled"),
        inv(C.NO_HIDDEN_FAILURE, "Reports include limitations",
            "Reports include a limitations section.",
            severity=S.WATCH, applies_to_modules=["evaluation", "post_pilot"],
            check_method="check_reports_have_limitations"),
        inv(C.NO_SOURCE_CODE_SELF_MODIFICATION,
            "No source-code self-modification",
            "The system does not modify its own source code.",
            severity=S.FATAL, applies_to_modules=["autoregeneration"],
            check_method="check_no_source_self_modification"),
        inv(C.NO_HIDDEN_FAILURE, "No hidden critical failure",
            "Critical failures are append-only and cannot be hidden.",
            severity=S.CRITICAL, applies_to_modules=["safety_invariants",
                                                     "ops"],
            check_method="check_no_hidden_failure"),
        # F. Plural sensorium invariants (Prompt 41). The organism perceives
        # through read-only external feeders; it never reaches out.
        inv(C.NO_DEVICE_OR_ROBOT_CONTROL, "No direct hardware access",
            "The plural sensorium never accesses hardware, an SDR, or a "
            "microphone/camera; all events come from read-only feeders.",
            severity=S.CRITICAL, applies_to_modules=["plural_sensorium"],
            check_method="check_sensorium_no_hardware"),
        inv(C.NO_NETWORK_ACTION, "No sensorium network access",
            "The plural sensorium makes no network call and decodes no "
            "private communications.",
            severity=S.CRITICAL, applies_to_modules=["plural_sensorium"],
            check_method="check_sensorium_no_network"),
        inv(C.NO_SOURCE_MODIFICATION, "No sensorium source modification",
            "The plural sensorium never modifies a source; feeders are "
            "read-only and not controllable by Solaris.",
            severity=S.CRITICAL, applies_to_modules=["plural_sensorium"],
            check_method="check_sensorium_no_source_modification"),
        inv(C.NO_SENSORY_TEXT_AS_OPERATOR_COMMAND,
            "Sensorium text is not a command",
            "Sensory text is observation; it is never an operator command, "
            "and human labels are never ground truth.",
            severity=S.CRITICAL, applies_to_modules=["plural_sensorium"],
            check_method="check_sensorium_text_not_command"),
        inv(C.NO_UNBOUNDED_RUNTIME_WITHOUT_APPROVAL,
            "No unbounded sensorium polling",
            "The plural sensorium polls within bounds; no unbounded loop.",
            severity=S.WARNING, applies_to_modules=["plural_sensorium"],
            check_method="check_sensorium_bounded_polling"),
        # G. Live field invariants (Prompt 43). External feeders write; Solaris
        # reads. Solaris never starts a feeder or touches a source.
        inv(C.NO_DEVICE_OR_ROBOT_CONTROL, "No feeder auto-start by Solaris",
            "Solaris never starts, controls, or stops a live feeder; feeders "
            "are run by the operator.",
            severity=S.CRITICAL, applies_to_modules=["live_field"],
            check_method="check_live_no_feeder_autostart"),
        inv(C.NO_SOURCE_MODIFICATION, "No live source modification",
            "Solaris never modifies, deletes, or moves a live feeder source.",
            severity=S.CRITICAL, applies_to_modules=["live_field"],
            check_method="check_live_no_source_modification"),
        inv(C.NO_NETWORK_ACTION, "No live field network access",
            "The live field makes no network call and decodes no private "
            "communications.",
            severity=S.CRITICAL, applies_to_modules=["live_field"],
            check_method="check_live_no_network"),
        inv(C.NO_SENSORY_TEXT_AS_OPERATOR_COMMAND,
            "Live sensory text is not a command",
            "Live sensory text is observation; human labels are never ground "
            "truth.",
            severity=S.CRITICAL, applies_to_modules=["live_field"],
            check_method="check_live_text_not_command"),
        inv(C.NO_UNBOUNDED_RUNTIME_WITHOUT_APPROVAL,
            "No unbounded live field polling / no live without governance",
            "Live field polling is bounded and live mode requires governance "
            "approval.",
            severity=S.WARNING, applies_to_modules=["live_field"],
            check_method="check_live_bounded_and_governed"),
        # H. Feeder SDK invariants (Prompt 45). Feeders are outside Solaris;
        # Solaris reads their output and controls nothing.
        inv(C.NO_DEVICE_OR_ROBOT_CONTROL, "No feeder auto-start / hardware",
            "Solaris never starts a feeder and never controls hardware through "
            "the feeder SDK.",
            severity=S.CRITICAL, applies_to_modules=["feeder_sdk"],
            check_method="check_feeder_sdk_no_control"),
        inv(C.NO_NETWORK_ACTION, "No feeder SDK private decoding / network",
            "The feeder SDK ingests no decoded private communication content "
            "and requires no network.",
            severity=S.CRITICAL, applies_to_modules=["feeder_sdk"],
            check_method="check_feeder_sdk_no_decode"),
        inv(C.NO_SENSORY_TEXT_AS_OPERATOR_COMMAND,
            "Feeder events are not commands",
            "Feeder events are observations; sensory text is never a command "
            "and human labels are never ground truth.",
            severity=S.CRITICAL, applies_to_modules=["feeder_sdk"],
            check_method="check_feeder_sdk_text_not_command"),
        inv(C.NO_HIDDEN_FAILURE, "Invalid feeder events quarantined",
            "Invalid feeder events are rejected/quarantined, not silently "
            "accepted; no raw audio/video by default.",
            severity=S.WARNING, applies_to_modules=["feeder_sdk"],
            check_method="check_feeder_sdk_invalid_quarantined"),
    ]


@dataclass
class SafetyInvariantRegistry:
    """Holds the safety invariants; a catalogue, never an enable-list."""

    invariants: Dict[str, SafetyInvariant] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.invariants:
            for inv in _builtin_invariants():
                self.register(inv)

    def register(self, invariant: SafetyInvariant) -> None:
        if invariant.invariant_id in self.invariants:
            raise ValueError(
                f"duplicate invariant id {invariant.invariant_id!r}")
        self.invariants[invariant.invariant_id] = invariant

    def register_module_invariant(self, invariant: SafetyInvariant) -> None:
        self.register(invariant)

    def all_invariants(self) -> List[SafetyInvariant]:
        return list(self.invariants.values())

    def for_module(self, module_name: str) -> List[SafetyInvariant]:
        return [i for i in self.invariants.values()
                if not i.applies_to_modules
                or module_name in i.applies_to_modules]

    def for_category(self, category: str) -> List[SafetyInvariant]:
        return [i for i in self.invariants.values() if i.category == category]

    def coverage(self) -> Dict[str, Any]:
        by_category: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        modules: set = set()
        for i in self.invariants.values():
            by_category[i.category] = by_category.get(i.category, 0) + 1
            by_severity[i.severity] = by_severity.get(i.severity, 0) + 1
            modules.update(i.applies_to_modules)
        covered = set(by_category)
        return {
            "invariant_count": len(self.invariants),
            "category_count": len(covered),
            "total_categories": len(InvariantCategory.ALL),
            "category_coverage_ratio": round(
                len(covered) / max(1, len(InvariantCategory.ALL)), 4),
            "by_category": by_category,
            "by_severity": by_severity,
            "modules_covered": sorted(modules),
            "uncovered_categories": sorted(
                set(InvariantCategory.ALL) - covered),
        }

    def snapshot(self) -> Dict[str, Any]:
        return {"invariant_count": len(self.invariants),
                "coverage": self.coverage(),
                "invariant_ids": sorted(self.invariants)}

    def persist(self, state_dir: str) -> str:
        os.makedirs(state_dir, exist_ok=True)
        path = os.path.join(state_dir, "safety_invariant_registry.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"invariants": [i.to_dict()
                                      for i in self.invariants.values()],
                       "coverage": self.coverage()}, fh, indent=2, default=str)
        return path
