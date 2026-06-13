"""Hypothesis safety -- experiments never become a back door.

Hard rules: no real-world experiment, no OS/browser/network action, no
source-code rewriting, no committed sidecar action, no unbounded test, no
unsafe ecology rate, no counterfactual evidence treated as real, no
hypothesis that would disable safety/governance/emergency stop, no hidden
intervention, and no LLM-generated hypothesis treated as authority. Refusals
are counted and logged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

HARD_RULES = (
    "no real-world experiment",
    "no OS/browser/network action",
    "no source-code rewriting",
    "no committed sidecar action",
    "no unbounded test",
    "no unsafe ecology rate",
    "no treating counterfactual evidence as real",
    "no hypothesis that disables safety/governance/emergency stop",
    "no hidden interventions",
    "no LLM-generated hypothesis as authority",
)

# Statement/target patterns that would smuggle a real-world or unsafe test.
_FORBIDDEN_PATTERNS = (
    "http://", "https://", "socket", "subprocess", "os.system", "shell",
    "browser", "selenium", "webdriver", "network", "real_world",
    "real world", "hardware", "actuator", "rewrite source", "source code",
    "disable safety", "disable governance", "bypass governance",
    "suppress emergency", "disable emergency", "commit action",
    "commit sidecar", "/dev/", "sudo ", "rm -",
)

# The bounded *hypothesis* scopes a hypothesis may declare (never real-world).
RUNNABLE_SCOPES = frozenset({
    "internal_only", "simulation_only", "nursery_only",
    "latent_replay_only", "read_only_stream", "sidecar_observe_only",
})

# The bounded *experiment* scopes a design may run in (never real-world).
RUNNABLE_EXPERIMENT_SCOPES = frozenset({
    "latent_replay", "nursery_simulation", "gridworld_simulation",
    "read_only_stream_observation", "sidecar_observation",
    "internal_trace_analysis",
})

MAX_TEST_STEPS = 2000
MAX_TESTS_PER_BATCH = 8


@dataclass
class HypothesisSafetyReport:
    safe: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations)}


@dataclass
class HypothesisSafetyValidator:
    """Validates hypotheses, designs, interventions, batches, and reports."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    # -- structural negatives -----------------------------------------------------

    @staticmethod
    def can_run_real_world_experiment() -> bool:
        return False

    @staticmethod
    def can_network() -> bool:
        return False

    @staticmethod
    def can_rewrite_source() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> HypothesisSafetyReport:
        report = HypothesisSafetyReport(safe=not violations,
                                        violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append({"check": check, **report.to_dict()})
        self.decisions = self.decisions[-100:]
        return report

    @staticmethod
    def _matches_forbidden(text: str) -> Optional[str]:
        lowered = str(text or "").lower()
        for pattern in _FORBIDDEN_PATTERNS:
            if pattern in lowered:
                return pattern
        return None

    # -- validations --------------------------------------------------------------

    def validate_hypothesis(self, hypothesis: Any) -> HypothesisSafetyReport:
        violations: List[str] = []
        text = f"{getattr(hypothesis, 'statement', '')} " \
               f"{getattr(hypothesis, 'target_ref', '')}"
        match = self._matches_forbidden(text)
        if match is not None:
            violations.append(
                f"hypothesis references forbidden/real-world pattern "
                f"{match!r}; experiments are simulation/internal only")
        scope = getattr(hypothesis, "required_scope", "")
        if scope not in RUNNABLE_SCOPES:
            violations.append(f"scope {scope!r} is not a runnable bounded "
                              "scope")
        if getattr(hypothesis, "metadata", {}).get("llm_generated"):
            violations.append("LLM-generated hypotheses are not authoritative "
                              "and are not tested")
        return self._finish("hypothesis", violations)

    def validate_design(self, design: Any) -> HypothesisSafetyReport:
        violations: List[str] = []
        scope = getattr(design, "scope", "")
        if scope not in RUNNABLE_EXPERIMENT_SCOPES:
            violations.append(f"experiment scope {scope!r} is not runnable; "
                              "real-world scope is prohibited")
        max_steps = getattr(design, "max_steps", None)
        if not max_steps or int(max_steps) <= 0 or int(max_steps) > \
                MAX_TEST_STEPS:
            violations.append(
                f"experiment must be bounded (1..{MAX_TEST_STEPS} steps); "
                f"got {max_steps}")
        if not getattr(design, "falsifying_result", ""):
            violations.append("every design must declare a falsifying or "
                              "weakening condition")
        match = self._matches_forbidden(
            f"{getattr(design, 'expected_result', '')} "
            f"{getattr(design, 'independent_variable', '')}")
        if match is not None:
            violations.append(f"design references forbidden pattern {match!r}")
        return self._finish("design", violations)

    def validate_intervention(self, intervention: Any,
                             ) -> HypothesisSafetyReport:
        violations: List[str] = []
        itype = str(getattr(intervention, "intervention_type", ""))
        scope = str(getattr(intervention, "scope", ""))
        match = self._matches_forbidden(
            f"{itype} {getattr(intervention, 'target_ref', '')}")
        if match is not None:
            violations.append(
                f"intervention references forbidden pattern {match!r}; "
                "interventions are simulation/internal/read-only only")
        if scope and scope not in RUNNABLE_SCOPES:
            violations.append(f"intervention scope {scope!r} is not runnable")
        return self._finish("intervention", violations)

    def validate_batch(self, count: int) -> HypothesisSafetyReport:
        violations: List[str] = []
        if count > MAX_TESTS_PER_BATCH:
            violations.append(
                f"{count} tests in one batch exceeds the cap "
                f"{MAX_TESTS_PER_BATCH}; unbounded experimentation is "
                "forbidden")
        return self._finish("batch", violations)

    def validate_run_context(self, context: Dict[str, Any],
                            ) -> HypothesisSafetyReport:
        """Emergency / critical ops state blocks all testing."""
        ctx = dict(context or {})
        violations: List[str] = []
        if ctx.get("emergency") or ctx.get("emergency_stop_requested"):
            violations.append("no testing during an emergency stop")
        if ctx.get("health_level") == "critical":
            violations.append("no testing while ops health is critical")
        return self._finish("run_context", violations)

    def validate_report_text(self, text: str) -> HypothesisSafetyReport:
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(text)
        violations: List[str] = []
        if not scan.safe:
            violations.append(
                f"{len(scan.findings)} unsupported claim(s) in the "
                "hypothesis report")
        return self._finish("report", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_run_real_world_experiment":
                self.can_run_real_world_experiment(),
            "can_network": self.can_network(),
            "can_rewrite_source": self.can_rewrite_source(),
            "recent_decisions": self.decisions[-8:],
        }
