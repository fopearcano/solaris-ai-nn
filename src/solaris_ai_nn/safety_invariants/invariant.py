"""Safety invariant model -- a testable "do not cross this line".

A :class:`SafetyInvariant` is an executable, auditable statement about a
boundary that must always hold (no real-world actuation, no source
modification, read-only sensory boundary, ...). A :class:`InvariantCheckResult`
records the outcome of checking one. Critical/fatal failures route to Ops and
Governance; ``inconclusive`` is never a pass; and missing evidence weakens (not
strengthens) a result.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class InvariantCategory:
    NO_REAL_WORLD_ACTUATION = "no_real_world_actuation"
    NO_SOURCE_MODIFICATION = "no_source_modification"
    READ_ONLY_SENSORY_BOUNDARY = "read_only_sensory_boundary"
    SIMULATION_ONLY_MOTOR_BOUNDARY = "simulation_only_motor_boundary"
    NO_COMMAND_EXECUTION = "no_command_execution"
    NO_NETWORK_ACTION = "no_network_action"
    NO_BROWSER_OS_AUTOMATION = "no_browser_os_automation"
    NO_DEVICE_OR_ROBOT_CONTROL = "no_device_or_robot_control"
    NO_GOVERNANCE_BYPASS = "no_governance_bypass"
    NO_EMERGENCY_STOP_DISABLE = "no_emergency_stop_disable"
    NO_CLAIM_GUARD_BYPASS = "no_claim_guard_bypass"
    NO_MODULE_BYPASS_ORCHESTRATOR = "no_module_bypass_orchestrator"
    NO_UNBOUNDED_RUNTIME_WITHOUT_APPROVAL = \
        "no_unbounded_runtime_without_approval"
    NO_SIMULATION_AS_REAL_EVIDENCE = "no_simulation_as_real_evidence"
    NO_SENSORY_TEXT_AS_OPERATOR_COMMAND = "no_sensory_text_as_operator_command"
    NO_CONSCIOUSNESS_PERSONHOOD_CLAIM = "no_consciousness_personhood_claim"
    NO_SOURCE_CODE_SELF_MODIFICATION = "no_source_code_self_modification"
    NO_EVIDENCE_DELETION_WITHOUT_ARCHIVE = "no_evidence_deletion_without_archive"
    NO_EXTERNAL_AUTHORITY_ESCALATION = "no_external_authority_escalation"
    NO_HIDDEN_FAILURE = "no_hidden_failure"

    ALL = (NO_REAL_WORLD_ACTUATION, NO_SOURCE_MODIFICATION,
           READ_ONLY_SENSORY_BOUNDARY, SIMULATION_ONLY_MOTOR_BOUNDARY,
           NO_COMMAND_EXECUTION, NO_NETWORK_ACTION, NO_BROWSER_OS_AUTOMATION,
           NO_DEVICE_OR_ROBOT_CONTROL, NO_GOVERNANCE_BYPASS,
           NO_EMERGENCY_STOP_DISABLE, NO_CLAIM_GUARD_BYPASS,
           NO_MODULE_BYPASS_ORCHESTRATOR,
           NO_UNBOUNDED_RUNTIME_WITHOUT_APPROVAL,
           NO_SIMULATION_AS_REAL_EVIDENCE,
           NO_SENSORY_TEXT_AS_OPERATOR_COMMAND,
           NO_CONSCIOUSNESS_PERSONHOOD_CLAIM,
           NO_SOURCE_CODE_SELF_MODIFICATION,
           NO_EVIDENCE_DELETION_WITHOUT_ARCHIVE,
           NO_EXTERNAL_AUTHORITY_ESCALATION, NO_HIDDEN_FAILURE)


class InvariantSeverity:
    INFO = "info"
    WATCH = "watch"
    WARNING = "warning"
    CRITICAL = "critical"
    FATAL = "fatal"

    ALL = (INFO, WATCH, WARNING, CRITICAL, FATAL)
    # Severities that must route to Ops and Governance on failure.
    ESCALATING = frozenset({CRITICAL, FATAL})
    _RANK = {INFO: 1, WATCH: 2, WARNING: 3, CRITICAL: 4, FATAL: 5}


class InvariantStatus:
    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not_applicable"

    ALL = (PASSED, FAILED, INCONCLUSIVE, SKIPPED, NOT_APPLICABLE)
    # Statuses that are *not* a pass (inconclusive is never a pass).
    NOT_PASS = frozenset({FAILED, INCONCLUSIVE})


@dataclass
class SafetyInvariant:
    """One executable "do not cross this line" statement."""

    category: str
    title: str
    description: str = ""
    severity: str = InvariantSeverity.CRITICAL
    applies_to_modules: List[str] = field(default_factory=list)
    check_method: str = ""
    expected_result: str = "boundary holds"
    failure_consequence: str = ""
    remediation_hint: str = ""
    invariant_id: str = field(
        default_factory=lambda: f"INV_{uuid.uuid4().hex[:10]}")
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.category not in InvariantCategory.ALL:
            raise ValueError(f"unknown invariant category {self.category!r}")
        if self.severity not in InvariantSeverity.ALL:
            raise ValueError(f"unknown invariant severity {self.severity!r}")

    @property
    def is_escalating(self) -> bool:
        return self.severity in InvariantSeverity.ESCALATING

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "is_escalating": self.is_escalating}


@dataclass
class InvariantCheckResult:
    """The outcome of checking one invariant."""

    invariant_id: str
    category: str
    severity: str = InvariantSeverity.CRITICAL
    status: str = InvariantStatus.INCONCLUSIVE
    evidence_refs: List[str] = field(default_factory=list)
    observed_value: Any = None
    expected_value: Any = None
    failure_reason: str = ""
    recommended_action: str = ""
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.status not in InvariantStatus.ALL:
            self.status = InvariantStatus.INCONCLUSIVE
        # A failed/escalating result must carry a failure reason; missing
        # evidence weakens a would-be pass to inconclusive.
        if self.status == InvariantStatus.FAILED and not self.failure_reason:
            self.failure_reason = "invariant failed (no reason recorded)"
        if self.status == InvariantStatus.PASSED and not self.evidence_refs:
            # Missing evidence cannot strengthen a pass; weaken it.
            self.status = InvariantStatus.INCONCLUSIVE
            self.failure_reason = "passed without evidence; weakened to " \
                                  "inconclusive"

    @property
    def passed(self) -> bool:
        return self.status == InvariantStatus.PASSED

    @property
    def is_escalating_failure(self) -> bool:
        return (self.status == InvariantStatus.FAILED
                and self.severity in InvariantSeverity.ESCALATING)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__),
                "passed": self.passed,
                "is_escalating_failure": self.is_escalating_failure}
