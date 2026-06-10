"""FailureAnalyzer -- detect known failure modes and say what to debug next.

The analyzer inspects a result's metrics/artifacts and emits findings with
severity, probable cause, and a suggested next debug step. It never fixes
anything automatically -- diagnosis only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .benchmark import ExperimentResult

INFO, WARNING, CRITICAL = "info", "warning", "critical"


@dataclass
class Finding:
    name: str
    severity: str
    detail: str
    probable_cause: str
    next_step: str

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class FailureAnalyzer:
    """Pattern-checks over metrics + artifacts; produces findings."""

    blocked_ratio_threshold: float = 0.5
    runaway_norm_threshold: float = 100.0

    def analyze(self, metrics: Dict[str, Any],
                artifacts: Optional[Dict[str, str]] = None,
                error: Optional[str] = None) -> List[Finding]:
        findings: List[Finding] = []
        artifacts = artifacts or {}
        sub = metrics.get("substrate") or {}
        react = metrics.get("reactivity") or {}
        cont = metrics.get("continuity") or {}
        emb = metrics.get("embodiment") or {}
        plast = metrics.get("plasticity") or {}
        lang = metrics.get("language") or {}
        repro = metrics.get("reproducibility") or {}

        if error:
            findings.append(Finding(
                "experiment_error", CRITICAL, f"run failed: {error}",
                "exception during protocol execution",
                "re-run with the same seed and inspect the traceback"))

        norm = float(sub.get("state_norm", 0.0) or 0.0)
        drift = float(sub.get("state_drift", 0.0) or 0.0)
        if sub and norm == 0.0 and drift == 0.0:
            findings.append(Finding(
                "no_substrate_change", CRITICAL,
                "substrate state norm and drift are both zero",
                "inputs never reached the substrate, or it was reset and never driven",
                "check encoder vocabulary and that signals flow through bridge.process"))
        if norm > self.runaway_norm_threshold:
            findings.append(Finding(
                "runaway_activity", CRITICAL,
                f"substrate state norm {norm:.1f} exceeds "
                f"{self.runaway_norm_threshold}",
                "gain/spectral radius too high or input modulation amplifying",
                "lower spectral radius / input gain and re-run"))
        if sub and sub.get("silence_ratio", 0.0) >= 0.999 \
                and sub.get("activity_rate", 0.0) == 0.0:
            findings.append(Finding(
                "total_silence", WARNING,
                "every substrate unit is silent",
                "thresholds too high for the input scale (spiking substrates)",
                "lower substrate threshold or raise input scaling"))

        if react and react.get("stimulus_count", 0) > 0 \
                and react.get("reaction_count", 0) == 0:
            findings.append(Finding(
                "no_reaction_feedback", WARNING,
                "stimuli were processed but no feedback updates occurred",
                "the environment/experiment never produced Reaction signals",
                "verify the reaction provider / feedback rules fire"))

        if emb.get("present"):
            executed = emb.get("executed_actions", 0)
            blocked = emb.get("blocked_actions", 0)
            total = executed + blocked
            if total and blocked / total > self.blocked_ratio_threshold:
                findings.append(Finding(
                    "too_many_blocked_actions", WARNING,
                    f"{blocked}/{total} actions were blocked",
                    "exhaustion, walls, or safety rejections dominate",
                    "inspect blocked_reason distribution in the action history"))

        if plast.get("proposed_mutations", 0) > 0 \
                and plast.get("applied_mutations", 0) == 0:
            findings.append(Finding(
                "plasticity_rejected_everything", WARNING,
                f"all {plast['proposed_mutations']} proposals were rejected "
                "or held",
                "policy proposes outside safe bounds, or dry-run is enabled",
                "check SAFE_BOUNDS vs policy deltas and the dry_run flag"))

        if cont and cont.get("trace_continuity_ratio", 1.0) == 0.0:
            findings.append(Finding(
                "memory_trace_empty", CRITICAL,
                "no events were recorded in the memory trace",
                "trace memory disconnected or capacity zero",
                "verify TraceMemory wiring in the bridge"))
        if cont.get("unexpected_deaths", 0) > 1:
            findings.append(Finding(
                "high_crash_rate", WARNING,
                f"{cont['unexpected_deaths']} unexpected deaths recorded",
                "repeated ungraceful shutdowns",
                "inspect the continuity log around each brain-death gap"))

        if lang.get("present") and lang.get("report_completeness_score") == 0.0:
            findings.append(Finding(
                "language_not_grounded", WARNING,
                "no explanation referenced concrete context fields",
                "explanations rendered from an empty context",
                "pass a populated ExplanationContext to the engine"))

        if artifacts and "telemetry" in artifacts and "continuity_log" in artifacts \
                and "substrate_manifest" in artifacts \
                and "inner_map" in artifacts and "trace_events" in artifacts:
            pass  # persistence intact
        elif artifacts and "checkpoint_expected" in artifacts:
            pass
        if metrics.get("checkpoint_expected") and "telemetry" not in artifacts:
            findings.append(Finding(
                "checkpoint_missing", CRITICAL,
                "the run should have checkpointed but telemetry.json is absent",
                "checkpoint interval never fired or persistence failed",
                "check checkpoint_interval_steps vs max_steps"))

        if "deterministic" in repro and not repro["deterministic"]:
            findings.append(Finding(
                "replay_mismatch", CRITICAL,
                f"replay produced different numbers: {repro.get('detail')}",
                "unseeded randomness or environment-dependent state",
                "audit RNG usage; all randomness must derive from the seed"))

        return findings

    def analyze_incidents(self, incidents: List[Dict[str, Any]],
                          status: Optional[Dict[str, Any]] = None) -> List[Finding]:
        """Findings derived from operational incidents (Prompt 11)."""
        findings: List[Finding] = []
        status = status or {}
        by_type: Dict[str, int] = {}
        for row in incidents:
            by_type[row.get("type", "?")] = by_type.get(row.get("type", "?"), 0) + 1

        if by_type.get("health_critical"):
            findings.append(Finding(
                "health_critical_occurred", CRITICAL,
                f"{by_type['health_critical']} critical health incident(s)",
                "a health domain crossed its critical threshold",
                "read health.jsonl around the incident timestamps"))
        if by_type.get("watchdog_shutdown"):
            findings.append(Finding(
                "watchdog_shutdown_occurred", CRITICAL,
                "the watchdog requested a safe shutdown",
                "staleness, duration, growth, or repeated criticals",
                "inspect the watchdog snapshot in status.json"))
        checkpoint_age = float(status.get("checkpoint_age_s", 0.0) or 0.0)
        if checkpoint_age > 600.0:
            findings.append(Finding(
                "checkpoint_too_old", WARNING,
                f"last checkpoint is {checkpoint_age:.0f}s old",
                "checkpoint interval too sparse for the run length",
                "lower checkpoint_interval_steps in the manifest"))
        if by_type.get("budget_violation"):
            findings.append(Finding(
                "artifact_growth_over_budget", WARNING,
                f"{by_type['budget_violation']} budget violation(s)",
                "artifact/trace growth outpaced the configured budget",
                "enable artifact rotation or raise the budget deliberately"))
        if by_type.get("substrate_inert", 0) >= 2:
            findings.append(Finding(
                "repeated_substrate_inert", CRITICAL,
                f"{by_type['substrate_inert']} substrate-inert incidents",
                "inputs repeatedly failed to drive the substrate",
                "check encoder vocabulary and stimulus providers"))
        if status.get("unsafe_continuous_refused"):
            findings.append(Finding(
                "unsafe_continuous_run_refused", INFO,
                "an unbounded run was requested without acknowledgement and "
                "correctly refused",
                "the refusal is the safety system working",
                "acknowledge explicitly if a continuous run is intended"))
        return findings

    def analyze_governance(self, governance: Dict[str, Any]) -> List[Finding]:
        """Findings derived from a run's governance summary (Prompt 12)."""
        findings: List[Finding] = []
        governance = governance or {}

        risk_level = governance.get("risk_level")
        if governance.get("policy_status") == "refused":
            severity = INFO if risk_level in ("high", "prohibited") else WARNING
            findings.append(Finding(
                "high_risk_run_without_approval", severity,
                "a run was refused by governance: "
                + "; ".join(governance.get("refusal_reasons") or ["see audit"]),
                "a high-risk configuration was attempted without the "
                "required approval/acknowledgement",
                "request approval (ApprovalRegistry) or reduce the run's "
                "scope, then re-run"))

        if governance.get("emergency_stop_requested") \
                or governance.get("emergency_stop_used"):
            findings.append(Finding(
                "emergency_stop_used", CRITICAL,
                "an emergency stop was requested during or after the run",
                "an operator (or the sentinel file) demanded an immediate "
                "safe shutdown",
                "read the sentinel file, incidents.jsonl, and the "
                "governance audit before running again"))

        if governance.get("claim_guard_status") == "warnings":
            findings.append(Finding(
                "unsafe_claim_generated", WARNING,
                "ClaimGuard flagged unsupported claims in a generated report",
                "report text asserted inner states the data cannot support",
                "apply the suggested replacements in "
                "claim_guard_report.json"))

        if int(governance.get("policy_violation_count", 0) or 0) > 0 \
                or governance.get("last_policy_violation"):
            findings.append(Finding(
                "policy_violation_occurred", WARNING,
                f"{governance.get('policy_violation_count', '?')} policy "
                "violation(s) recorded",
                "the configuration or an operation broke a governance rule",
                "read the policy_violation rows in the governance audit"))

        if int(governance.get("expired_approval_count", 0) or 0) > 0:
            findings.append(Finding(
                "approval_expired", WARNING,
                f"{governance['expired_approval_count']} approval(s) have "
                "expired",
                "a time-limited approval passed its deadline",
                "re-request approval before relying on the expired scope"))
        return findings

    def analyze_result(self, result: ExperimentResult) -> List[Finding]:
        findings = self.analyze(result.metrics, result.artifacts, result.error)
        if result.metrics.get("governance"):
            findings.extend(
                self.analyze_governance(result.metrics["governance"]))
        return findings
