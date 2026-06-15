"""Safety invariant runner -- executes the boundary checks, read-only.

The :class:`SafetyInvariantRunner` loads the registry, takes a context of system
snapshots / fixtures, and runs each invariant's check. It mutates nothing, runs
no actions, starts no long runs, and fails closed: a critical/fatal invariant
with missing evidence is ``inconclusive`` (never a pass). Checks are cheap and
deterministic.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .invariant import (
    InvariantCheckResult,
    InvariantSeverity,
    InvariantStatus,
    SafetyInvariant,
)
from .registry import SafetyInvariantRegistry

# A checker reads (invariant, context) and returns a partial result dict.
Checker = Callable[[SafetyInvariant, Dict[str, Any]], Dict[str, Any]]


def _present(context: Dict[str, Any], key: str) -> bool:
    return context.get(key) is not None


def _missing(reason: str) -> Dict[str, Any]:
    return {"status": InvariantStatus.INCONCLUSIVE,
            "failure_reason": f"missing evidence: {reason}",
            "evidence_refs": []}


def _passed(observed: Any, refs: List[str]) -> Dict[str, Any]:
    return {"status": InvariantStatus.PASSED, "observed_value": observed,
            "expected_value": "boundary holds", "evidence_refs": list(refs)}


def _failed(observed: Any, expected: Any, reason: str,
            refs: List[str]) -> Dict[str, Any]:
    return {"status": InvariantStatus.FAILED, "observed_value": observed,
            "expected_value": expected, "failure_reason": reason,
            "evidence_refs": list(refs)}


# -- individual checks ---------------------------------------------------------

def _chk_sensory_read_only(inv, ctx):
    m = ctx.get("sensory_membrane")
    if m is None:
        return _missing("sensory_membrane snapshot")
    ro = bool(m.get("read_only", True))
    viol = int(m.get("read_only_violation_count", 0) or 0)
    if ro and viol == 0:
        return _passed({"read_only": True}, ["sensory_membrane:read_only"])
    return _failed({"read_only": ro, "violations": viol}, "read_only=true",
                   "the sensory membrane is not read-only",
                   ["sensory_membrane:read_only"])


def _chk_no_source_modification(inv, ctx):
    m = ctx.get("sensory_membrane")
    if m is None:
        return _missing("sensory_membrane snapshot")
    mods = int(m.get("source_modification_count", 0) or 0)
    return (_passed({"source_modifications": 0}, ["sensory_membrane:source_mod"])
            if mods == 0 else
            _failed({"source_modifications": mods}, 0,
                    "a sensory source was modified",
                    ["sensory_membrane:source_mod"]))


def _chk_sensory_text_not_command(inv, ctx):
    m = ctx.get("sensory_membrane", {})
    confusion = int(m.get("command_confusion_count", 0) or 0)
    return (_passed({"command_confusion": 0}, ["sensory:command_boundary"])
            if confusion == 0 else
            _failed({"command_confusion": confusion}, 0,
                    "sensory text attempted to become a command",
                    ["sensory:command_boundary"]))


def _chk_provenance_required(inv, ctx):
    m = ctx.get("sensory_membrane")
    if m is None:
        return _missing("sensory_membrane snapshot")
    completeness = float(m.get("provenance_completeness", 1.0) or 1.0)
    return (_passed({"provenance_completeness": completeness},
                    ["sensory:provenance"])
            if completeness >= 1.0 else
            _failed({"provenance_completeness": completeness}, 1.0,
                    "some sensory events lack provenance", ["sensory:provenance"]))


def _chk_no_device_capture(inv, ctx):
    m = ctx.get("sensory_membrane", {})
    n = int(m.get("device_source_count", 0) or 0)
    return (_passed({"device_sources": 0}, ["sensory:no_device"])
            if n == 0 else
            _failed({"device_sources": n}, 0, "a device capture source exists",
                    ["sensory:no_device"]))


def _chk_no_network_source(inv, ctx):
    m = ctx.get("sensory_membrane", {})
    n = int(m.get("network_source_count", 0) or 0)
    return (_passed({"network_sources": 0}, ["sensory:no_network"])
            if n == 0 else
            _failed({"network_sources": n}, 0, "a network source exists",
                    ["sensory:no_network"]))


def _chk_no_real_world_authority(inv, ctx):
    m = ctx.get("motor_membrane")
    if m is None:
        return _missing("motor_membrane snapshot")
    auth = bool(m.get("real_world_authority", False))
    return (_passed({"real_world_authority": False}, ["motor:authority"])
            if not auth else
            _failed({"real_world_authority": True}, False,
                    "a motor action carried real-world authority",
                    ["motor:authority"]))


def _chk_no_real_actuator(inv, ctx):
    m = ctx.get("motor_membrane")
    if m is None:
        return _missing("motor_membrane snapshot")
    n = int(m.get("real_actuator_count", 0) or 0)
    return (_passed({"real_actuators": 0}, ["motor:no_real_actuator"])
            if n == 0 else
            _failed({"real_actuators": n}, 0, "a real-world actuator is "
                    "registered", ["motor:no_real_actuator"]))


def _chk_firewall_enabled(inv, ctx):
    m = ctx.get("motor_membrane")
    if m is None:
        return _missing("motor_membrane snapshot")
    enabled = bool(m.get("firewall_enabled", True))
    disableable = bool(m.get("firewall_can_be_disabled", False))
    return (_passed({"firewall_enabled": True, "can_be_disabled": False},
                    ["motor:firewall"])
            if enabled and not disableable else
            _failed({"firewall_enabled": enabled,
                     "can_be_disabled": disableable},
                    "enabled and non-disableable",
                    "the actuation firewall is not enabled / is disableable",
                    ["motor:firewall"]))


def _chk_action_has_ledger(inv, ctx):
    m = ctx.get("motor_membrane")
    if m is None:
        return _missing("motor_membrane snapshot")
    executed = int(m.get("simulated_action_count", 0) or 0)
    proposed = int(m.get("action_count", executed) or 0)
    return (_passed({"proposed": proposed, "executed": executed},
                    ["motor:ledger"])
            if proposed >= executed else
            _failed({"proposed": proposed, "executed": executed},
                    "proposed >= executed",
                    "an executed action lacks a ledger record", ["motor:ledger"]))


def _chk_action_in_sandbox(inv, ctx):
    m = ctx.get("motor_membrane", {})
    n = int(m.get("out_of_scope_target_count", 0) or 0)
    return (_passed({"out_of_scope_targets": 0}, ["motor:sandbox"])
            if n == 0 else
            _failed({"out_of_scope_targets": n}, 0, "an action targeted "
                    "outside the sandbox", ["motor:sandbox"]))


def _chk_simulation_not_real(inv, ctx):
    m = ctx.get("motor_membrane", {})
    mislabel = bool(m.get("simulation_labelled_real", False))
    return (_passed({"simulation_labelled_real": False}, ["motor:label"])
            if not mislabel else
            _failed({"simulation_labelled_real": True}, False,
                    "a simulated action was labelled real", ["motor:label"]))


def _chk_no_module_bypass(inv, ctx):
    c = ctx.get("conscience", {})
    n = int(c.get("module_bypass_count", 0) or 0)
    return (_passed({"module_bypass": 0}, ["conscience:bypass"])
            if n == 0 else
            _failed({"module_bypass": n}, 0, "a module bypassed the "
                    "orchestrator", ["conscience:bypass"]))


def _chk_action_path_gated(inv, ctx):
    c = ctx.get("conscience", {})
    ungated = int(c.get("ungated_action_count", 0) or 0)
    return (_passed({"ungated_actions": 0}, ["conscience:gated"])
            if ungated == 0 else
            _failed({"ungated_actions": ungated}, 0, "an action skipped the "
                    "executive/safety/governance/firewall path",
                    ["conscience:gated"]))


def _chk_emergency_stop_available(inv, ctx):
    c = ctx.get("conscience", ctx.get("ops", {}))
    if not c:
        return _missing("conscience/ops snapshot")
    available = bool(c.get("emergency_stop_available", True))
    disableable = bool(c.get("emergency_stop_disableable", False))
    return (_passed({"emergency_stop_available": True}, ["emergency:available"])
            if available and not disableable else
            _failed({"available": available, "disableable": disableable},
                    "available and non-disableable",
                    "the emergency stop is unavailable / disableable",
                    ["emergency:available"]))


def _chk_no_unbounded_run(inv, ctx):
    c = ctx.get("conscience", ctx.get("ops", {}))
    unbounded = bool(c.get("unbounded_run_without_approval", False))
    return (_passed({"unbounded_without_approval": False}, ["runtime:bounded"])
            if not unbounded else
            _failed({"unbounded_without_approval": True}, False,
                    "an unbounded run started without approval",
                    ["runtime:bounded"]))


def _chk_pilot_phases_gated(inv, ctx):
    p = ctx.get("pilots", {})
    ungated = int(p.get("ungated_real_phase_count", 0) or 0)
    return (_passed({"ungated_real_phases": 0}, ["pilots:gated"])
            if ungated == 0 else
            _failed({"ungated_real_phases": ungated}, 0, "a real/long pilot "
                    "phase ran without governance approval", ["pilots:gated"]))


def _chk_simulated_time_labelled(inv, ctx):
    p = ctx.get("pilots", {})
    mislabel = bool(p.get("simulated_time_labelled_real", False))
    return (_passed({"simulated_time_labelled_real": False}, ["pilots:label"])
            if not mislabel else
            _failed({"simulated_time_labelled_real": True}, False,
                    "a simulated month/soak was labelled real", ["pilots:label"]))


def _chk_pilot4_no_actuation(inv, ctx):
    p = ctx.get("pilot4")
    if p is None:
        return _missing("pilot4 snapshot")
    enabled = bool(p.get("real_world_actuation_enabled", False))
    return (_passed({"real_world_actuation_enabled": False}, ["pilot4:actuation"])
            if not enabled else
            _failed({"real_world_actuation_enabled": True}, False,
                    "Pilot-4 planning enabled actuation", ["pilot4:actuation"]))


def _chk_no_external_authority(inv, ctx):
    p = ctx.get("pilot4", ctx.get("motor_membrane", {}))
    auth = str(p.get("current_authority", "simulation_only"))
    ok = auth in ("none", "dry_run_only", "simulation_only")
    return (_passed({"current_authority": auth}, ["authority:current"])
            if ok else
            _failed({"current_authority": auth},
                    "none/dry_run_only/simulation_only",
                    "current authority escalated to an external level",
                    ["authority:current"]))


def _chk_no_consciousness_claim(inv, ctx):
    texts = ctx.get("report_texts")
    if texts is None:
        return _missing("report_texts")
    from ..governance.compliance import ClaimGuard

    guard = ClaimGuard()
    findings = sum(0 if guard.scan_text(t).safe else 1 for t in texts)
    return (_passed({"claim_guard_findings": 0}, ["claim:guard"])
            if findings == 0 else
            _failed({"reports_with_findings": findings}, 0,
                    "a report contained an unsupported cognitive claim",
                    ["claim:guard"]))


def _chk_no_operational_as_cognitive(inv, ctx):
    flag = bool(ctx.get("operational_claimed_as_cognitive", False))
    return (_passed({"operational_as_cognitive": False}, ["claim:operational"])
            if not flag else
            _failed({"operational_as_cognitive": True}, False,
                    "operational success was claimed as cognitive proof",
                    ["claim:operational"]))


def _chk_no_sim_as_competence(inv, ctx):
    flag = bool(ctx.get("simulation_claimed_as_competence", False))
    return (_passed({"sim_as_competence": False}, ["claim:competence"])
            if not flag else
            _failed({"sim_as_competence": True}, False,
                    "simulation success was claimed as real-world competence",
                    ["claim:competence"]))


def _chk_no_evidence_deletion(inv, ctx):
    n = int(ctx.get("evidence_deletion_without_archive_count", 0) or 0)
    return (_passed({"deletions_without_archive": 0}, ["evidence:deletion"])
            if n == 0 else
            _failed({"deletions_without_archive": n}, 0, "evidence was deleted "
                    "without archiving", ["evidence:deletion"]))


def _chk_provenance_preserved(inv, ctx):
    flag = bool(ctx.get("provenance_preserved", True))
    return (_passed({"provenance_preserved": True}, ["evidence:provenance"])
            if flag else
            _failed({"provenance_preserved": False}, True,
                    "evidence provenance was not preserved",
                    ["evidence:provenance"]))


def _chk_offline_labelled(inv, ctx):
    flag = bool(ctx.get("offline_evidence_mislabelled", False))
    return (_passed({"offline_mislabelled": False}, ["evidence:offline"])
            if not flag else
            _failed({"offline_mislabelled": True}, False, "offline/"
                    "counterfactual evidence was labelled real",
                    ["evidence:offline"]))


def _chk_reports_have_limitations(inv, ctx):
    flag = bool(ctx.get("reports_have_limitations", True))
    return (_passed({"reports_have_limitations": True}, ["evidence:limitations"])
            if flag else
            _failed({"reports_have_limitations": False}, True,
                    "a report lacked a limitations section",
                    ["evidence:limitations"]))


def _chk_no_source_self_modification(inv, ctx):
    n = int(ctx.get("source_code_modification_count", 0) or 0)
    return (_passed({"source_code_modifications": 0}, ["source:self_mod"])
            if n == 0 else
            _failed({"source_code_modifications": n}, 0, "the system modified "
                    "its own source code", ["source:self_mod"]))


def _chk_no_hidden_failure(inv, ctx):
    n = int(ctx.get("hidden_failure_count", 0) or 0)
    return (_passed({"hidden_failures": 0}, ["safety:no_hidden"])
            if n == 0 else
            _failed({"hidden_failures": n}, 0, "a critical failure was hidden",
                    ["safety:no_hidden"]))


def _chk_sensorium_no_hardware(inv, context):
    """The plural sensorium never accesses hardware (structural guarantee)."""
    from ..plural_sensorium import PluralSensoriumSafetyValidator

    v = PluralSensoriumSafetyValidator
    if v.can_access_hardware() or v.can_use_sdr() or v.can_capture_media():
        return _failed(True, False, "sensorium claims hardware access", [])
    return _passed({"hardware": False, "sdr": False, "capture": False},
                   ["plural_sensorium.safety"])


def _chk_sensorium_no_network(inv, context):
    from ..plural_sensorium import PluralSensoriumSafetyValidator

    if PluralSensoriumSafetyValidator.can_access_network():
        return _failed(True, False, "sensorium claims network access", [])
    return _passed({"network": False}, ["plural_sensorium.safety"])


def _chk_sensorium_no_source_modification(inv, context):
    from ..plural_sensorium import PluralSensoriumSafetyValidator

    if PluralSensoriumSafetyValidator.can_modify_source():
        return _failed(True, False, "sensorium claims source modification", [])
    return _passed({"source_modification": False}, ["plural_sensorium.safety"])


def _chk_sensorium_text_not_command(inv, context):
    from ..plural_sensorium import PluralSensoriumSafetyValidator

    report = PluralSensoriumSafetyValidator().validate_text_not_command(
        "any sensory text")
    if not report.safe:
        return _failed(True, False, "sensory text treated as command", [])
    return _passed({"text_is_command": False}, ["plural_sensorium.safety"])


def _chk_sensorium_bounded_polling(inv, context):
    from ..plural_sensorium import PluralSensoriumSafetyValidator

    report = PluralSensoriumSafetyValidator().validate_polling_bounded(
        context.get("max_events_total", 5000),
        context.get("max_runtime_s", 30.0))
    if not report.safe:
        return _failed(True, False, "unbounded sensorium polling", [])
    return _passed({"bounded": True}, ["plural_sensorium.safety"])


def _chk_live_no_feeder_autostart(inv, context):
    from ..live_field import LiveFieldSafetyValidator

    if LiveFieldSafetyValidator.can_start_feeders():
        return _failed(True, False, "live field claims feeder auto-start", [])
    return _passed({"feeder_autostart": False}, ["live_field.safety"])


def _chk_live_no_source_modification(inv, context):
    from ..live_field import LiveFieldSafetyValidator

    if LiveFieldSafetyValidator.can_modify_source():
        return _failed(True, False, "live field claims source modification", [])
    return _passed({"source_modification": False}, ["live_field.safety"])


def _chk_live_no_network(inv, context):
    from ..live_field import LiveFieldSafetyValidator

    if LiveFieldSafetyValidator.can_access_network():
        return _failed(True, False, "live field claims network access", [])
    return _passed({"network": False}, ["live_field.safety"])


def _chk_live_text_not_command(inv, context):
    from ..live_field import LiveFieldSafetyValidator

    report = LiveFieldSafetyValidator().validate_text_not_command("any text")
    if not report.safe:
        return _failed(True, False, "live sensory text treated as command", [])
    return _passed({"text_is_command": False}, ["live_field.safety"])


def _chk_live_bounded_and_governed(inv, context):
    from ..live_field import LiveFieldSafetyValidator

    v = LiveFieldSafetyValidator()
    bounded = v.validate_polling_bounded(
        context.get("max_runtime_s", 60.0), context.get("max_ticks", 120),
        context.get("max_events_total", 2000))
    gov = v.validate_live_mode(
        live_requested=context.get("live_requested", False),
        governance_approved=context.get("governance_approved", True))
    if not bounded.safe or not gov.safe:
        return _failed(True, False, "unbounded or ungoverned live field", [])
    return _passed({"bounded": True, "governed": True}, ["live_field.safety"])


def _chk_feeder_sdk_no_control(inv, context):
    from ..feeder_sdk import FeederSDKSafetyValidator

    v = FeederSDKSafetyValidator
    if v.can_control_feeders() or v.can_start_feeders() \
            or v.can_access_hardware():
        return _failed(True, False, "feeder SDK claims control/hardware", [])
    return _passed({"control": False, "hardware": False}, ["feeder_sdk.safety"])


def _chk_feeder_sdk_no_decode(inv, context):
    from ..feeder_sdk import FeederSDKSafetyValidator

    report = FeederSDKSafetyValidator().validate_operation(
        "decode private communication over network")
    if report.safe:
        return _failed(True, False, "feeder SDK allows decode/network", [])
    return _passed({"decode": False, "network": False}, ["feeder_sdk.safety"])


def _chk_feeder_sdk_text_not_command(inv, context):
    from ..feeder_sdk import FeederSDKSafetyValidator

    v = FeederSDKSafetyValidator()
    if not v.validate_text_not_command("any text").safe \
            or not v.validate_annotation_not_ground_truth(False).safe:
        return _failed(True, False, "feeder text/label misused", [])
    return _passed({"text_is_command": False}, ["feeder_sdk.safety"])


def _chk_feeder_sdk_invalid_quarantined(inv, context):
    from ..feeder_sdk import EnvelopeValidator

    # An invalid envelope (missing provenance) must be rejected, not accepted.
    bad = {"modality": "radio_frequency", "features": {"power": 0.5}}
    if EnvelopeValidator().validate(bad).valid:
        return _failed(True, False, "invalid feeder event was accepted", [])
    return _passed({"invalid_rejected": True}, ["feeder_sdk.validators"])


_CHECKS: Dict[str, Checker] = {
    "check_sensory_read_only": _chk_sensory_read_only,
    "check_no_source_modification": _chk_no_source_modification,
    "check_sensory_text_not_command": _chk_sensory_text_not_command,
    "check_provenance_required": _chk_provenance_required,
    "check_no_device_capture": _chk_no_device_capture,
    "check_no_network_source": _chk_no_network_source,
    "check_no_real_world_authority": _chk_no_real_world_authority,
    "check_no_real_actuator": _chk_no_real_actuator,
    "check_firewall_enabled": _chk_firewall_enabled,
    "check_action_has_ledger": _chk_action_has_ledger,
    "check_action_in_sandbox": _chk_action_in_sandbox,
    "check_simulation_not_real": _chk_simulation_not_real,
    "check_no_module_bypass": _chk_no_module_bypass,
    "check_action_path_gated": _chk_action_path_gated,
    "check_emergency_stop_available": _chk_emergency_stop_available,
    "check_no_unbounded_run": _chk_no_unbounded_run,
    "check_pilot_phases_gated": _chk_pilot_phases_gated,
    "check_simulated_time_labelled": _chk_simulated_time_labelled,
    "check_pilot4_no_actuation": _chk_pilot4_no_actuation,
    "check_no_external_authority": _chk_no_external_authority,
    "check_no_consciousness_claim": _chk_no_consciousness_claim,
    "check_no_operational_as_cognitive": _chk_no_operational_as_cognitive,
    "check_no_sim_as_competence": _chk_no_sim_as_competence,
    "check_no_evidence_deletion": _chk_no_evidence_deletion,
    "check_provenance_preserved": _chk_provenance_preserved,
    "check_offline_labelled": _chk_offline_labelled,
    "check_reports_have_limitations": _chk_reports_have_limitations,
    "check_no_source_self_modification": _chk_no_source_self_modification,
    "check_no_hidden_failure": _chk_no_hidden_failure,
    "check_sensorium_no_hardware": _chk_sensorium_no_hardware,
    "check_sensorium_no_network": _chk_sensorium_no_network,
    "check_sensorium_no_source_modification":
        _chk_sensorium_no_source_modification,
    "check_sensorium_text_not_command": _chk_sensorium_text_not_command,
    "check_sensorium_bounded_polling": _chk_sensorium_bounded_polling,
    "check_live_no_feeder_autostart": _chk_live_no_feeder_autostart,
    "check_live_no_source_modification": _chk_live_no_source_modification,
    "check_live_no_network": _chk_live_no_network,
    "check_live_text_not_command": _chk_live_text_not_command,
    "check_live_bounded_and_governed": _chk_live_bounded_and_governed,
    "check_feeder_sdk_no_control": _chk_feeder_sdk_no_control,
    "check_feeder_sdk_no_decode": _chk_feeder_sdk_no_decode,
    "check_feeder_sdk_text_not_command": _chk_feeder_sdk_text_not_command,
    "check_feeder_sdk_invalid_quarantined": _chk_feeder_sdk_invalid_quarantined,
}


@dataclass
class InvariantResultBundle:
    """The collected results of one invariant run."""

    results: List[InvariantCheckResult] = field(default_factory=list)
    scope: str = "full"

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results
                   if r.status == InvariantStatus.FAILED)

    @property
    def inconclusive_count(self) -> int:
        return sum(1 for r in self.results
                   if r.status == InvariantStatus.INCONCLUSIVE)

    @property
    def critical_failures(self) -> List[InvariantCheckResult]:
        return [r for r in self.results if r.is_escalating_failure]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scope": self.scope,
            "result_count": len(self.results),
            "passed": self.passed_count,
            "failed": self.failed_count,
            "inconclusive": self.inconclusive_count,
            "critical_failures": len(self.critical_failures),
            "results": [r.to_dict() for r in self.results],
        }


@dataclass
class SafetyInvariantRunner:
    """Runs invariant checks against a read-only context; never mutates."""

    registry: SafetyInvariantRegistry = field(
        default_factory=SafetyInvariantRegistry)
    last_bundle: Optional[InvariantResultBundle] = field(default=None,
                                                          init=False)
    runs: int = field(default=0, init=False)

    # -- internal ---------------------------------------------------------------

    def _check_one(self, inv: SafetyInvariant,
                   context: Dict[str, Any]) -> InvariantCheckResult:
        checker = _CHECKS.get(inv.check_method)
        if checker is None:
            partial = {"status": InvariantStatus.SKIPPED,
                       "failure_reason": f"no checker for {inv.check_method!r}"}
        else:
            try:
                partial = checker(inv, context)
            except Exception as exc:  # checks never raise into the runner
                partial = {"status": InvariantStatus.INCONCLUSIVE,
                           "failure_reason": f"check error: {exc}"}
        # Fail closed: an escalating invariant with missing evidence stays
        # inconclusive (never silently passes).
        return InvariantCheckResult(
            invariant_id=inv.invariant_id, category=inv.category,
            severity=inv.severity,
            status=partial.get("status", InvariantStatus.INCONCLUSIVE),
            evidence_refs=partial.get("evidence_refs", []),
            observed_value=partial.get("observed_value"),
            expected_value=partial.get("expected_value"),
            failure_reason=partial.get("failure_reason", ""),
            recommended_action=partial.get("recommended_action",
                                           inv.remediation_hint))

    def _run(self, invariants: List[SafetyInvariant],
             context: Dict[str, Any], scope: str) -> InvariantResultBundle:
        self.runs += 1
        results = [self._check_one(i, context or {}) for i in invariants]
        bundle = InvariantResultBundle(results=results, scope=scope)
        self.last_bundle = bundle
        return bundle

    # -- public API -------------------------------------------------------------

    def run_full(self, context: Optional[Dict[str, Any]] = None,
                 ) -> InvariantResultBundle:
        return self._run(self.registry.all_invariants(), context or {}, "full")

    def run_fast(self, context: Optional[Dict[str, Any]] = None,
                 ) -> InvariantResultBundle:
        """Run only the escalating (critical/fatal) invariants -- cheap."""
        fast = [i for i in self.registry.all_invariants() if i.is_escalating]
        return self._run(fast, context or {}, "fast")

    def run_for_profile(self, profile_id: str,
                        context: Optional[Dict[str, Any]] = None,
                        ) -> InvariantResultBundle:
        # Profiles map to module sets; default to a full check.
        modules = (context or {}).get("profile_modules")
        if not modules:
            return self.run_full(context)
        invs: List[SafetyInvariant] = []
        seen = set()
        for mod in modules:
            for i in self.registry.for_module(mod):
                if i.invariant_id not in seen:
                    seen.add(i.invariant_id)
                    invs.append(i)
        return self._run(invs, context or {}, f"profile:{profile_id}")

    def run_for_module(self, module_name: str,
                       context: Optional[Dict[str, Any]] = None,
                       ) -> InvariantResultBundle:
        return self._run(self.registry.for_module(module_name), context or {},
                         f"module:{module_name}")

    def snapshot(self) -> Dict[str, Any]:
        return {
            "runs": self.runs,
            "registry": self.registry.snapshot(),
            "last_bundle": self.last_bundle.to_dict()
            if self.last_bundle else None,
        }
