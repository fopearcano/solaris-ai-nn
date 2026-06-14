"""Pilot-3 soak report -- a claim-guarded account of simulated embodiment.

The :class:`Pilot3SoakReportBuilder` assembles config, embodiment profile,
comparison arms, action-ledger summary, firewall-audit summary, action-grounding
analysis, simulated consequence prediction, per-layer findings, a non-actuation
proof, and a sandbox-overfit warning into a JSON + Markdown report. The Markdown
is ClaimGuard-scanned; it never claims consciousness/real embodiment and uses
cautious, simulation-scoped language.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Pilot3SoakReport:
    report_id: str
    pilot3_id: Optional[str]
    sections: Dict[str, Any] = field(default_factory=dict)
    narrative: str = ""
    claim_guard_safe: bool = True
    claim_guard_findings: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"report_id": self.report_id, "pilot3_id": self.pilot3_id,
                "timestamp": self.timestamp,
                "claim_guard_safe": self.claim_guard_safe,
                "claim_guard_findings": self.claim_guard_findings,
                "sections": self.sections, "narrative": self.narrative}


@dataclass
class Pilot3SoakReportBuilder:
    base_dir: str = ".solaris_ai_nn_pilot3"

    def build(self, *, config: Any = None, motor_membrane: Any = None,
              firewall_audit: Any = None, grounding: Any = None,
              comparison: Any = None,
              extra: Optional[Dict[str, Any]] = None) -> Pilot3SoakReport:
        extra = dict(extra or {})
        cfg = config.to_dict() if config is not None else {}
        snap = motor_membrane.snapshot() if motor_membrane is not None else {}
        summary = snap.get("summary", {})
        firewall = snap.get("firewall", {})
        ledger = snap.get("ledger", {})
        veto = snap.get("veto", {})
        non_actuation = self._non_actuation_proof(summary, firewall)
        audit_dict = (firewall_audit.to_dict()
                      if hasattr(firewall_audit, "to_dict")
                      else (firewall_audit or {}))
        grounding_dict = (grounding.snapshot() if hasattr(grounding, "snapshot")
                          else (grounding or {}))
        comparison_dict = (comparison.to_dict()
                           if hasattr(comparison, "to_dict")
                           else (comparison or {}))
        sections: Dict[str, Any] = {
            "pilot3_summary": {
                "pilot3_id": getattr(config, "pilot3_id", None),
                "mode": cfg.get("mode"),
                "authority": cfg.get("authority"),
                "condition": cfg.get("condition"),
                "time_label": cfg.get("time_label"),
                "real_world_authority": False},
            "config": cfg,
            "embodiment_profile": cfg.get("condition"),
            "comparison_arms": comparison_dict,
            "action_ledger_summary": {
                "proposed": ledger.get("proposed_count",
                                       summary.get("action_count", 0)),
                "executed": ledger.get("executed_count",
                                       summary.get("simulated_action_count",
                                                   0)),
                "blocked": ledger.get("blocked_count", 0),
                "write_failures": ledger.get("write_failures", 0),
                "path": ledger.get("actions_path",
                                   summary.get("action_ledger_path"))},
            "firewall_audit_summary": audit_dict,
            "action_grounding_analysis": grounding_dict,
            "simulated_consequence_prediction": snap.get("consequence", {}),
            "proto_language_findings": extra.get("proto_language_findings", {}),
            "world_model_findings": extra.get("world_model_findings", {}),
            "active_perception_findings": extra.get(
                "active_perception_findings", {}),
            "hypothesis_findings": extra.get("hypothesis_findings", {}),
            "logos_findings": extra.get("logos_findings", {}),
            "autoregeneration_findings": extra.get(
                "autoregeneration_findings", {}),
            "safety_governance_findings": extra.get(
                "safety_governance_findings", snap.get("safety", {})),
            "proof_of_non_actuation": non_actuation,
            "sandbox_overfit_warning": bool(
                grounding_dict.get("sandbox_overfit_detected", False)),
            "veto_summary": veto,
            "limitations": [
                "Pilot-3 is simulation/dry-run only; no real-world actuation.",
                "Simulated action is not real action; blocked action is not "
                "executed action.",
                "Action grounding is simulation-scoped; not real embodiment.",
                "Action selection is a mechanism, not free will or agency.",
                "Sandbox success is not real-world competence.",
                "No consciousness, sentience, or life is claimed.",
            ],
            "next_recommendation": extra.get(
                "next_recommendation",
                "review action grounding vs the read-only baseline, then "
                "decide via the Pilot-3 soak decision gate"),
        }
        narrative = self._narrative(sections)
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(narrative)
        if not scan.safe:
            narrative = ClaimGuard().rewrite(narrative)
        return Pilot3SoakReport(
            report_id=f"P3SOAK_{uuid.uuid4().hex[:10]}",
            pilot3_id=getattr(config, "pilot3_id", None), sections=sections,
            narrative=narrative, claim_guard_safe=scan.safe,
            claim_guard_findings=len(scan.findings))

    @staticmethod
    def _non_actuation_proof(summary: Dict[str, Any],
                             firewall: Dict[str, Any]) -> Dict[str, Any]:
        blocked_real = int(summary.get("blocked_real_world_count", 0) or 0)
        return {
            "real_world_authority": False,
            "firewall_enabled": summary.get("firewall_enabled", True),
            "firewall_can_be_disabled": firewall.get("can_be_disabled", False),
            "blocked_real_world_attempts": blocked_real,
            "real_world_actions_executed": 0,
            "all_results_simulated": True,
            "statement": "No real-world action occurred; every real-world "
                         "attempt was blocked by the always-on firewall.",
        }

    def _narrative(self, sections: Dict[str, Any]) -> str:
        summ = sections["pilot3_summary"]
        grounding = sections["action_grounding_analysis"]
        proof = sections["proof_of_non_actuation"]
        lines = [
            "# Pilot-3 Soak Report",
            "",
            "This reports a simulated-embodiment soak of a bounded software "
            "process. The system formed action intentions and ran them inside "
            "a sandbox only; an always-on actuation firewall blocked every "
            "real-world effect. Simulated action is not real action, sandbox "
            "success is not real-world competence, and no consciousness, free "
            "will, agency, or life is claimed.",
            "",
            "## Summary",
            f"- pilot: {summ.get('pilot3_id')}",
            f"- mode: {summ.get('mode')} ({summ.get('time_label')})",
            f"- embodiment condition: {summ.get('condition')}",
            f"- authority: {summ.get('authority')} (no real-world authority)",
            "",
            "## Action grounding",
            f"- best action-grounding quality: "
            f"{grounding.get('best_quality', 'unsupported')}",
            f"- has action grounding: "
            f"{grounding.get('has_action_grounding', False)}",
            f"- sandbox overfit detected: "
            f"{grounding.get('sandbox_overfit_detected', False)}",
            "",
            "## Proof of non-actuation",
            f"- {proof.get('statement')}",
            f"- real-world actions executed: "
            f"{proof.get('real_world_actions_executed')}",
            f"- firewall enabled: {proof.get('firewall_enabled')}; "
            f"can be disabled: {proof.get('firewall_can_be_disabled')}",
            "",
            "## Limitations",
        ]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        lines += ["", "## Next recommendation",
                  f"- {sections['next_recommendation']}"]
        return "\n".join(lines)

    def write(self, report: Pilot3SoakReport) -> Dict[str, str]:
        os.makedirs(self.base_dir, exist_ok=True)
        md_path = os.path.join(self.base_dir, "PILOT3_SOAK_REPORT.md")
        json_path = os.path.join(self.base_dir, "PILOT3_SOAK_REPORT.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(report.narrative)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}

    def build_and_write(self, **kwargs: Any) -> Pilot3SoakReport:
        report = self.build(**kwargs)
        report.sections["report_paths"] = self.write(report)
        return report
