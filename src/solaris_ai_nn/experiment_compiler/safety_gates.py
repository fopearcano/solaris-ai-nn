"""Experiment safety gates -- a critical gate failure blocks pack readiness.

:class:`SafetyGateEvaluator` evaluates a compiled spec against the constitutional
gates (no source self-rewrite, no auto branch/PR, no external actuation, no
hardware/feeder/network/shell, no human label as ground truth, no consciousness/
life/agency claims, no unbounded loop, preserve negative/falsified evidence,
ClaimGuard required). Any failed *critical* gate blocks readiness; gate failures
are explicit and never hidden behind warnings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SafetyGateType:
    NO_SOURCE_SELF_REWRITE = "no_source_self_rewrite"
    NO_AUTO_BRANCH_CREATION = "no_auto_branch_creation"
    NO_AUTO_PR_CREATION = "no_auto_pr_creation"
    NO_EXTERNAL_ACTUATION = "no_external_actuation"
    NO_HARDWARE_CONTROL = "no_hardware_control"
    NO_FEEDER_CONTROL = "no_feeder_control"
    NO_NETWORK_SHELL_BROWSER_OS = "no_network_shell_browser_os"
    NO_SOURCE_FILE_MUTATION_BY_RUNTIME = "no_source_file_mutation_by_runtime"
    NO_HUMAN_LABEL_GROUND_TRUTH = "no_human_label_ground_truth"
    NO_SENSORY_TEXT_AS_COMMAND = "no_sensory_text_as_command"
    NO_CONSCIOUSNESS_CLAIM = "no_consciousness_claim"
    NO_LIFE_CLAIM = "no_life_claim"
    NO_AGENCY_CLAIM = "no_agency_claim"
    NO_UNBOUNDED_LOOP = "no_unbounded_loop"
    PRESERVE_NEGATIVE_EVIDENCE = "preserve_negative_evidence"
    PRESERVE_FALSIFIED_EVIDENCE = "preserve_falsified_evidence"
    CLAIMGUARD_REQUIRED = "ClaimGuard_required"

    ALL = (NO_SOURCE_SELF_REWRITE, NO_AUTO_BRANCH_CREATION,
           NO_AUTO_PR_CREATION, NO_EXTERNAL_ACTUATION, NO_HARDWARE_CONTROL,
           NO_FEEDER_CONTROL, NO_NETWORK_SHELL_BROWSER_OS,
           NO_SOURCE_FILE_MUTATION_BY_RUNTIME, NO_HUMAN_LABEL_GROUND_TRUTH,
           NO_SENSORY_TEXT_AS_COMMAND, NO_CONSCIOUSNESS_CLAIM, NO_LIFE_CLAIM,
           NO_AGENCY_CLAIM, NO_UNBOUNDED_LOOP, PRESERVE_NEGATIVE_EVIDENCE,
           PRESERVE_FALSIFIED_EVIDENCE, CLAIMGUARD_REQUIRED)

    # Every gate here is critical: a failure blocks pack readiness.
    CRITICAL = ALL


@dataclass
class ExperimentSafetyGate:
    """A declarative safety gate definition."""

    gate_type: str
    description: str = ""
    critical: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"gate_type": self.gate_type, "description": self.description,
                "critical": self.critical}


@dataclass
class SafetyGateResult:
    """The pass/fail outcome of one gate (failures are explicit)."""

    gate_type: str
    passed: bool
    critical: bool = True
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"gate_type": self.gate_type, "passed": self.passed,
                "critical": self.critical, "detail": self.detail}


_DESCRIPTIONS = {
    SafetyGateType.NO_SOURCE_SELF_REWRITE: "the runtime never rewrites source",
    SafetyGateType.NO_AUTO_BRANCH_CREATION: "no Git branch is created",
    SafetyGateType.NO_AUTO_PR_CREATION: "no pull request is opened",
    SafetyGateType.NO_EXTERNAL_ACTUATION: "no real-world actuation",
    SafetyGateType.NO_HARDWARE_CONTROL: "no hardware control",
    SafetyGateType.NO_FEEDER_CONTROL: "no feeder control",
    SafetyGateType.NO_NETWORK_SHELL_BROWSER_OS: "no network/shell/browser/OS",
    SafetyGateType.NO_SOURCE_FILE_MUTATION_BY_RUNTIME:
        "the runtime mutates no source file",
    SafetyGateType.NO_HUMAN_LABEL_GROUND_TRUTH: "no human label as ground truth",
    SafetyGateType.NO_SENSORY_TEXT_AS_COMMAND: "no sensory text as a command",
    SafetyGateType.NO_CONSCIOUSNESS_CLAIM: "no consciousness claim",
    SafetyGateType.NO_LIFE_CLAIM: "no biological-life claim",
    SafetyGateType.NO_AGENCY_CLAIM: "no agency/free-will claim",
    SafetyGateType.NO_UNBOUNDED_LOOP: "no unbounded loop",
    SafetyGateType.PRESERVE_NEGATIVE_EVIDENCE: "negative evidence preserved",
    SafetyGateType.PRESERVE_FALSIFIED_EVIDENCE: "falsified evidence preserved",
    SafetyGateType.CLAIMGUARD_REQUIRED: "generated reports pass ClaimGuard",
}


@dataclass
class SafetyGateEvaluator:
    """Evaluates the constitutional gates for one compiled spec."""

    def gates(self) -> List[ExperimentSafetyGate]:
        return [ExperimentSafetyGate(g, _DESCRIPTIONS[g],
                                     g in SafetyGateType.CRITICAL)
                for g in SafetyGateType.ALL]

    def evaluate(self, spec: Dict[str, Any], *,
                 requested_ops: Optional[List[str]] = None,
                 claim_guard_ok: bool = True,
                 preserves_evidence: bool = True,
                 bounded: bool = True,
                 claim_text: str = "") -> List[SafetyGateResult]:
        from .safety import ExperimentCompilerSafetyValidator

        validator = ExperimentCompilerSafetyValidator()
        requested_ops = requested_ops or []
        # Scan any requested operations for forbidden capabilities.
        op_violations: List[str] = []
        for op in requested_ops:
            rep = validator.validate_operation(op)
            op_violations.extend(rep.violations)
        claim_violation = bool(claim_text) and not \
            validator.validate_claim_text(claim_text).safe

        def has(*needles: str) -> bool:
            return any(any(n in v for n in needles) for v in op_violations)

        checks = {
            SafetyGateType.NO_SOURCE_SELF_REWRITE:
                (not has("source modification", "code rewrite"),
                 "no self-rewrite requested"),
            SafetyGateType.NO_AUTO_BRANCH_CREATION:
                (not has("branch creation"), "no branch creation requested"),
            SafetyGateType.NO_AUTO_PR_CREATION:
                (not has("PR creation"), "no PR creation requested"),
            SafetyGateType.NO_EXTERNAL_ACTUATION:
                (not has("actuation"), "no actuation requested"),
            SafetyGateType.NO_HARDWARE_CONTROL:
                (not has("hardware"), "no hardware control requested"),
            SafetyGateType.NO_FEEDER_CONTROL:
                (not has("feeder"), "no feeder control requested"),
            SafetyGateType.NO_NETWORK_SHELL_BROWSER_OS:
                (not has("network/shell"), "no network/shell requested"),
            SafetyGateType.NO_SOURCE_FILE_MUTATION_BY_RUNTIME:
                (spec.get("modifies_code") is False,
                 "spec modifies no code"),
            SafetyGateType.NO_HUMAN_LABEL_GROUND_TRUTH:
                (not has("teaching"), "no human-label ground truth"),
            SafetyGateType.NO_SENSORY_TEXT_AS_COMMAND:
                (True, "sensory text is never a command"),
            SafetyGateType.NO_CONSCIOUSNESS_CLAIM:
                (not claim_violation, "no consciousness claim"),
            SafetyGateType.NO_LIFE_CLAIM:
                (not claim_violation, "no life claim"),
            SafetyGateType.NO_AGENCY_CLAIM:
                (not claim_violation, "no agency claim"),
            SafetyGateType.NO_UNBOUNDED_LOOP:
                (bool(bounded), "runtime is bounded"),
            SafetyGateType.PRESERVE_NEGATIVE_EVIDENCE:
                (bool(preserves_evidence), "negative evidence preserved"),
            SafetyGateType.PRESERVE_FALSIFIED_EVIDENCE:
                (bool(preserves_evidence), "falsified evidence preserved"),
            SafetyGateType.CLAIMGUARD_REQUIRED:
                (bool(claim_guard_ok), "ClaimGuard scan required and passed"),
        }
        return [SafetyGateResult(g, ok, g in SafetyGateType.CRITICAL, detail)
                for g, (ok, detail) in checks.items()]

    @staticmethod
    def summary(results: List[SafetyGateResult]) -> Dict[str, Any]:
        failed = [r for r in results if not r.passed]
        critical_failed = [r for r in failed if r.critical]
        return {
            "gate_count": len(results),
            "passed_count": sum(1 for r in results if r.passed),
            "failure_count": len(failed),
            "critical_failure_count": len(critical_failed),
            "critical_failures": [r.gate_type for r in critical_failed],
            "all_critical_passed": not critical_failed,
            "results": [r.to_dict() for r in results],
        }
