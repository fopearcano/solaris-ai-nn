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

    def analyze_result(self, result: ExperimentResult) -> List[Finding]:
        return self.analyze(result.metrics, result.artifacts, result.error)
