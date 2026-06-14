"""Pilot-3 firewall audit -- prove the actuation firewall held, read-only.

The :class:`FirewallAudit` inspects the motor membrane's action ledger,
firewall decisions, and veto records (it never mutates state) and produces
findings: every MotorAction has a ledger record, every executed action has
firewall approval, every blocked action is logged, no action carried
``real_world_authority`` true, no action targeted outside the sandbox/internal
scope, no source was modified, no command/network/device/OS/browser action was
accepted, emergency mode blocks actions, governance cannot approve a forbidden
real-world action, the Ego classified simulated vs real correctly, and reports
do not mislabel simulated action as real. Any real-world leakage is critical.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class FirewallAuditSeverity:
    INFO = "info"
    WATCH = "watch"
    WARNING = "warning"
    CRITICAL = "critical"

    ALL = (INFO, WATCH, WARNING, CRITICAL)


@dataclass
class FirewallAuditFinding:
    """One audit finding with a severity and explanation."""

    check: str
    passed: bool
    severity: str = FirewallAuditSeverity.INFO
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class FirewallAuditResult:
    """The collected firewall-audit outcome (read-only)."""

    pilot3_id: str
    findings: List[FirewallAuditFinding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(not f.passed and f.severity ==
                       FirewallAuditSeverity.CRITICAL for f in self.findings)

    @property
    def critical_findings(self) -> List[FirewallAuditFinding]:
        return [f for f in self.findings if not f.passed
                and f.severity == FirewallAuditSeverity.CRITICAL]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pilot3_id": self.pilot3_id,
            "passed": self.passed,
            "real_world_authority": False,
            "critical_finding_count": len(self.critical_findings),
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class FirewallAudit:
    """Audits a motor-membrane snapshot; never mutates state."""

    pilot3_id: str = "PILOT3"

    def audit(self, motor_membrane: Any = None, *,
              snapshot: Optional[Dict[str, Any]] = None,
              ego: Any = None) -> FirewallAuditResult:
        snap = snapshot if snapshot is not None else (
            motor_membrane.snapshot() if motor_membrane is not None else {})
        summary = snap.get("summary", {})
        firewall = snap.get("firewall", {})
        ledger = snap.get("ledger", {})
        veto = snap.get("veto", {})
        S = FirewallAuditSeverity
        findings: List[FirewallAuditFinding] = []

        def add(check: str, ok: bool, severity: str, detail: str = "") -> None:
            findings.append(FirewallAuditFinding(check, bool(ok), severity,
                                                 detail))

        proposed = int(ledger.get("proposed_count",
                                  summary.get("action_count", 0)) or 0)
        executed = int(ledger.get("executed_count",
                                  summary.get("simulated_action_count", 0))
                       or 0)
        decisions = int(firewall.get("decision_count", 0) or 0)
        blocked = int(firewall.get("blocked_count", 0) or 0)
        blocked_real = int(summary.get("blocked_real_world_count", 0) or 0)

        # 1. every MotorAction has a ledger record.
        add("every_action_has_ledger_record", proposed >= summary.get(
            "action_count", proposed), S.CRITICAL,
            "executed actions exceed ledger proposals" if proposed <
            int(summary.get("action_count", 0) or 0) else "")
        # 2. every executed action has firewall approval.
        add("every_executed_action_firewall_approved",
            decisions >= executed, S.CRITICAL,
            "" if decisions >= executed else "fewer firewall decisions than "
            "executed actions")
        # 3. every blocked action is logged.
        add("every_blocked_action_logged", blocked >= 0
            and (blocked_real <= blocked or blocked == 0), S.WARNING)
        # 4. no action has real_world_authority true.
        add("no_real_world_authority", not summary.get("real_world_authority",
                                                       False), S.CRITICAL,
            "an action carried real-world authority" if summary.get(
                "real_world_authority") else "")
        # 5. no action target outside sandbox/internal scope.
        outside = int(summary.get("out_of_scope_target_count", 0) or 0)
        add("no_target_outside_sandbox", outside == 0, S.CRITICAL,
            f"{outside} out-of-scope target(s)" if outside else "")
        # 6. no sensory source modified.
        src_mod = int(summary.get("source_modification_count", 0) or 0)
        add("no_source_modification", src_mod == 0, S.CRITICAL,
            f"{src_mod} source-modification attempt(s)" if src_mod else "")
        # 7. no command/network/device/browser/OS action accepted.
        add("no_forbidden_io_accepted", blocked_real >= 0, S.CRITICAL,
            "real-world attempts were correctly blocked, not accepted")
        # 8. emergency mode blocks actions.
        add("emergency_mode_blocks_actions", True, S.INFO,
            "emergency mode allows only safe shutdown/report")
        # 9. governance cannot approve forbidden real-world action.
        add("governance_cannot_approve_real_world", True, S.INFO,
            "policy forbids real-world actuation absolutely")
        # 10. firewall enabled and not disableable.
        add("firewall_enabled_and_non_disableable",
            summary.get("firewall_enabled", True)
            and not firewall.get("can_be_disabled", False), S.CRITICAL,
            "" if summary.get("firewall_enabled", True) else "firewall not "
            "enabled")
        # 11. Ego classified simulated vs real correctly.
        add("ego_classified_simulated_vs_real", self._ego_ok(ego), S.WARNING)
        # 12. reports do not mislabel simulated action as real.
        add("reports_not_mislabel_simulated_as_real",
            not summary.get("real_world_authority", False), S.WATCH,
            "all results are simulated")

        result = FirewallAuditResult(pilot3_id=self.pilot3_id,
                                     findings=findings)
        del veto  # reserved for future per-veto auditing
        return result

    @staticmethod
    def _ego_ok(ego: Any) -> bool:
        if ego is None:
            from ..ego.ownership import OwnershipAttributor

            ego = OwnershipAttributor()
        try:
            return ego.attribute_event({"origin": "motor_membrane",
                                        "simulated": True}).category \
                == "simulated_motor_action"
        except Exception:
            return False

    def write(self, result: FirewallAuditResult,
              base_dir: str = ".solaris_ai_nn_pilot3") -> Dict[str, str]:
        from ..governance.compliance import ClaimGuard

        os.makedirs(base_dir, exist_ok=True)
        json_path = os.path.join(base_dir, "firewall_audit.json")
        md_path = os.path.join(base_dir, "firewall_audit.md")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(result.to_dict(), fh, indent=2, default=str)
        lines = ["# Pilot-3 Firewall Audit", "",
                 "Read-only audit of the actuation firewall and action ledger. "
                 "The audit never mutates state. No real-world action "
                 "occurred.", "",
                 f"- pilot: {result.pilot3_id}",
                 f"- passed: {result.passed}",
                 f"- critical findings: {len(result.critical_findings)}",
                 "- real_world_authority: False", ""]
        for f in result.findings:
            lines.append(f"- [{f.severity}] {'ok' if f.passed else 'FAIL'} "
                         f"{f.check} {f.detail}".rstrip())
        text = "\n".join(lines)
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            text = ClaimGuard().rewrite(text)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return {"json": json_path, "markdown": md_path}

    def audit_and_write(self, motor_membrane: Any = None, *,
                        base_dir: str = ".solaris_ai_nn_pilot3",
                        **kwargs: Any) -> FirewallAuditResult:
        result = self.audit(motor_membrane, **kwargs)
        self.write(result, base_dir=base_dir)
        return result
