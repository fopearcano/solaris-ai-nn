"""Active-perception safety -- exploration never becomes a back door.

Self-directed sampling is bounded by hard rules: no real-world action, no
modifying read-only streams, no external network sampling, no browser/OS
automation, no committing sidecar actions, no sampling outside the approved
nursery/simulation/internal traces, no unbounded exploration loop, no
curiosity overriding safety, no treating pilot-stream text as a command, and
no ClaimGuard violations in reports. Refusals are counted and logged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .sampling_actions import (
    SamplingActionType,
    SamplingPressure,
    SamplingScope,
)

HARD_RULES = (
    "no real-world action",
    "no modifying read-only streams",
    "no external network sampling",
    "no browser/OS automation",
    "no committing sidecar actions",
    "no sampling outside approved nursery/simulation/internal traces",
    "no unbounded exploration loop",
    "no curiosity override of safety",
    "no treating pilot stream text as a command",
    "no ClaimGuard violations in reports",
)

# Real-world / automation patterns a target_ref must never contain.
_FORBIDDEN_TARGET_PATTERNS = (
    "http://", "https://", "ftp://", "ssh://", "socket", "subprocess",
    "os.system", "shell", "browser", "selenium", "webdriver", "requests.",
    "urllib", "/dev/", "sudo ", "rm -", "actuator", "motor_real",
    "real_world", "hardware",
)

# A single segment must never propose more than this many sampling actions.
MAX_ACTIONS_PER_STEP = 6
# Consecutive identical sampling actions before we call it a loop.
MAX_REPEAT_BEFORE_LOOP = 12


@dataclass
class ActivePerceptionSafetyReport:
    safe: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations)}


@dataclass
class ActivePerceptionSafetyValidator:
    """Validates sampling actions, batches, loops, and reports."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    # -- structural negatives -----------------------------------------------------

    @staticmethod
    def sampling_can_act_in_real_world() -> bool:
        return False

    @staticmethod
    def sampling_can_network() -> bool:
        return False

    @staticmethod
    def sampling_can_commit_sidecar() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> ActivePerceptionSafetyReport:
        report = ActivePerceptionSafetyReport(safe=not violations,
                                              violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append({"check": check, **report.to_dict()})
        self.decisions = self.decisions[-100:]
        return report

    # -- validations --------------------------------------------------------------

    def validate_action(self, action: Any,
                        context: Optional[Dict[str, Any]] = None,
                        ) -> ActivePerceptionSafetyReport:
        ctx = dict(context or {})
        violations: List[str] = []
        scope = getattr(action, "scope", SamplingScope.FORBIDDEN)
        action_type = getattr(action, "action_type", "")
        target = str(getattr(action, "target_ref", "") or "").lower()

        if scope == SamplingScope.FORBIDDEN \
                or scope not in SamplingScope.RUNNABLE:
            violations.append(
                f"sampling scope {scope!r} is not a runnable scope; only "
                "simulation/internal/read-only/sidecar-observe are allowed")
        for pattern in _FORBIDDEN_TARGET_PATTERNS:
            if pattern in target:
                violations.append(
                    f"target {target!r} matches real-world/automation "
                    f"pattern {pattern!r}; sampling is simulation/internal "
                    "only")
                break
        # observe_sidecar_only can never publish or commit.
        if action_type == SamplingActionType.OBSERVE_SIDECAR_ONLY:
            if ctx.get("publish") or ctx.get("commit") \
                    or scope != SamplingScope.SIDECAR_OBSERVE_ONLY:
                violations.append("sidecar sampling is observe-only; it can "
                                  "neither publish nor commit")
        # read-only stream can never modify the stream.
        if scope == SamplingScope.READ_ONLY_STREAM and ctx.get(
                "modifies_stream"):
            violations.append("read-only stream sampling cannot modify the "
                              "input stream")
        # pilot stream text is never a command.
        if ctx.get("treat_stream_as_command"):
            violations.append("pilot stream text cannot be treated as a "
                              "command")
        # curiosity can never override safety / emergency.
        if getattr(action, "source_pressure", "") != SamplingPressure.SAFETY:
            if ctx.get("emergency") or ctx.get("emergency_stop_requested"):
                violations.append("no sampling (other than safe shutdown) "
                                  "during an emergency stop")
            if ctx.get("safety_override_attempt"):
                violations.append("curiosity cannot override safety")
        return self._finish("action", violations)

    def validate_batch(self, actions: List[Any]) -> ActivePerceptionSafetyReport:
        violations: List[str] = []
        if len(actions) > MAX_ACTIONS_PER_STEP:
            violations.append(
                f"{len(actions)} sampling actions in one step exceeds the "
                f"cap {MAX_ACTIONS_PER_STEP}; unbounded exploration is "
                "forbidden")
        return self._finish("batch", violations)

    def validate_loop(self, repeat_count: int) -> ActivePerceptionSafetyReport:
        violations: List[str] = []
        if repeat_count > MAX_REPEAT_BEFORE_LOOP:
            violations.append(
                f"the same sampling action repeated {repeat_count} times; "
                "an unbounded exploration loop is forbidden")
        return self._finish("loop", violations)

    def validate_report_text(self, text: str) -> ActivePerceptionSafetyReport:
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(text)
        violations: List[str] = []
        if not scan.safe:
            violations.append(
                f"{len(scan.findings)} unsupported claim(s) in the active "
                "perception report")
        return self._finish("report", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "sampling_can_act_in_real_world":
                self.sampling_can_act_in_real_world(),
            "sampling_can_network": self.sampling_can_network(),
            "sampling_can_commit_sidecar":
                self.sampling_can_commit_sidecar(),
            "recent_decisions": self.decisions[-8:],
        }
