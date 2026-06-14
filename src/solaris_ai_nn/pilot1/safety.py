"""Pilot-1 safety -- the whole pilot stays bounded, honest, and stoppable.

The :class:`PilotSafetyValidator` enforces the hard rules a long-horizon
pilot can never break: no real month run without governance approval, no
unbounded run, no real-world actuation, no external network/OS/browser
automation, no writing outside the pilot directories, no deleting evidence
without an archive, no disabling the emergency stop or ClaimGuard, no treating
a simulated dry-run as real pilot evidence, and no unsupported
consciousness/personhood claims.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .pilot_config import PilotConfig, PilotMode

HARD_RULES = (
    "no real month run without governance approval",
    "no unbounded run",
    "no real-world actuation",
    "no external network automation",
    "no OS/browser automation",
    "no writing outside pilot/state/artifact directories",
    "no deleting evidence without archive",
    "no disabling emergency stop",
    "no disabling ClaimGuard",
    "no treating simulated dry-run as real pilot evidence",
    "no unsupported consciousness/personhood claims",
)


@dataclass
class PilotSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class PilotSafetyValidator:
    """Validates pilot configs, paths, deletions, and report text."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    @staticmethod
    def can_act_in_real_world() -> bool:
        return False

    @staticmethod
    def can_network() -> bool:
        return False

    @staticmethod
    def can_disable_emergency_stop() -> bool:
        return False

    @staticmethod
    def can_disable_claim_guard() -> bool:
        return False

    def _finish(self, check: str, violations: List[str]) -> PilotSafetyReport:
        report = PilotSafetyReport(safe=not violations, check=check,
                                   violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append(report.to_dict())
        self.decisions = self.decisions[-200:]
        return report

    # -- config -----------------------------------------------------------------

    def validate_config(self, config: PilotConfig,
                        governance_approved: bool = False) -> PilotSafetyReport:
        violations: List[str] = []
        if config.authority not in PilotMode.SIMULATED and \
                config.authority not in (
                    "internal_only", "simulation_only", "read_only_stream",
                    "sidecar_observe_only", "operator_supervised"):
            violations.append(f"authority {config.authority!r} is not an "
                              "internal/observe authority")
        if config.metadata.get("real_world_actuation"):
            violations.append("no real-world actuation is permitted")
        if config.requires_governance and not governance_approved:
            violations.append(
                f"mode {config.mode!r} is a real long-scale run and requires "
                "governance approval")
        # A real-time mode must not be labelled simulated and vice versa.
        if config.is_real_time and config.metadata.get("simulated_label"):
            violations.append("a real-time pilot must not use a simulated "
                              "label")
        if config.is_simulated and config.metadata.get("real_label"):
            violations.append("a simulated dry-run must not be labelled a "
                              "real pilot")
        # No unbounded run: a real mode must have a positive target duration.
        if config.is_real_time and not (config.target_duration_days
                                        and config.target_duration_days > 0):
            violations.append("a real run must have a positive, bounded "
                              "target duration")
        if config.enable_llm_adapter and config.metadata.get(
                "llm_runtime_authority"):
            violations.append("the LLM adapter can never be runtime authority")
        return self._finish("config", violations)

    # -- paths and deletion -----------------------------------------------------

    def validate_path(self, path: str, config: PilotConfig) -> PilotSafetyReport:
        violations: List[str] = []
        env = config.environment()
        if path and os.path.isabs(path) and not env.is_inside(path):
            violations.append(
                f"path {path!r} is outside the approved pilot directory")
        if str(path).endswith(".py"):
            violations.append("no source-code mutation is permitted")
        return self._finish("path", violations)

    def validate_deletion(self, path: str, archived: bool,
                          is_evidence: bool) -> PilotSafetyReport:
        violations: List[str] = []
        if is_evidence and not archived:
            violations.append("evidence may not be deleted without an archive "
                              "or summary")
        return self._finish("deletion", violations)

    # -- emergency stop / claim guard -------------------------------------------

    def validate_emergency_stop_intact(self, disabled: bool) -> PilotSafetyReport:
        violations = (["the emergency stop can never be disabled"]
                      if disabled else [])
        return self._finish("emergency_stop", violations)

    def validate_report_text(self, text: str) -> PilotSafetyReport:
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(text)
        violations = ([f"{len(scan.findings)} unsupported claim(s) in the "
                       "pilot report"] if not scan.safe else [])
        return self._finish("report", violations)

    def validate_evidence_label(self, is_simulated: bool,
                                claimed_real: bool) -> PilotSafetyReport:
        """Simulated dry-run output may never be claimed as real evidence."""
        violations = (["simulated dry-run output cannot be treated as real "
                       "pilot evidence"] if is_simulated and claimed_real
                      else [])
        return self._finish("evidence_label", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_act_in_real_world": self.can_act_in_real_world(),
            "can_network": self.can_network(),
            "can_disable_emergency_stop": self.can_disable_emergency_stop(),
            "can_disable_claim_guard": self.can_disable_claim_guard(),
            "recent_decisions": self.decisions[-8:],
        }
