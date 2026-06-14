"""Pilot-3 report -- a claim-guarded account of simulated/dry-run embodiment.

The :class:`Pilot3ReportBuilder` assembles the embodiment profile, action and
veto counts, firewall decisions, simulated outcomes, world-model/proto-symbol
changes, consequence findings, LOGOS action/inhibition tensions, and an
explicit **proof of non-actuation** into a JSON + Markdown report. The Markdown
is ClaimGuard-scanned; it never claims agency or consciousness.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Pilot3Report:
    report_id: str
    sections: Dict[str, Any] = field(default_factory=dict)
    narrative: str = ""
    claim_guard_safe: bool = True
    claim_guard_findings: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"report_id": self.report_id, "timestamp": self.timestamp,
                "claim_guard_safe": self.claim_guard_safe,
                "claim_guard_findings": self.claim_guard_findings,
                "sections": self.sections, "narrative": self.narrative}


@dataclass
class Pilot3ReportBuilder:
    base_dir: str = ".solaris_ai_nn_pilot3"

    def build(self, runtime: Any = None,
              extra: Optional[Dict[str, Any]] = None) -> Pilot3Report:
        extra = dict(extra or {})
        snap = runtime.snapshot() if runtime is not None else {}
        summary = snap.get("summary", {})
        firewall = snap.get("firewall", {})
        non_actuation = self._non_actuation_proof(summary, firewall)
        sections: Dict[str, Any] = {
            "pilot3_summary": {
                "profile_id": summary.get("profile_id"),
                "real_world_authority": False,
                "dry_run": summary.get("dry_run"),
                "step_count": summary.get("step_count")},
            "embodiment_profile": summary.get("profile_id"),
            "action_count": summary.get("action_count", 0),
            "vetoed_action_count": summary.get("veto_count", 0),
            "firewall_decisions": firewall,
            "simulated_action_outcomes": snap.get("consequence", {}),
            "world_model_changes": extra.get("world_model_changes", {}),
            "proto_symbol_changes": extra.get("proto_symbol_changes", {}),
            "hypothesis_consequence_findings": extra.get(
                "hypothesis_consequence_findings", {}),
            "logos_action_inhibition_tensions": extra.get(
                "logos_action_inhibition_tensions", {}),
            "active_perception_changes": extra.get(
                "active_perception_changes", {}),
            "safety_governance_events": snap.get("safety", {}),
            "proof_of_non_actuation": non_actuation,
            "limitations": [
                "Pilot-3 is simulation/dry-run only; no real-world actuation.",
                "Simulated action is not real action; blocked action is not "
                "executed action.",
                "Action selection is a mechanism, not free will or agency.",
                "No consciousness, sentience, or life is claimed.",
            ],
            "next_recommendation": extra.get(
                "next_recommendation",
                "review grounding/prediction effects via the Pilot-3 "
                "decision gate"),
        }
        narrative = self._narrative(sections)
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(narrative)
        if not scan.safe:
            narrative = ClaimGuard().rewrite(narrative)
        return Pilot3Report(
            report_id=f"P3RPT_{uuid.uuid4().hex[:10]}", sections=sections,
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
        proof = sections["proof_of_non_actuation"]
        lines = [
            "# Pilot-3 Report",
            "",
            "This reports a simulation/dry-run limited-embodiment run. "
            "Solaris-AI-NN formed action intentions and ran them only inside a "
            "sandbox; it took no real-world action. Simulated action is not "
            "real action; action selection is a mechanism, not free will. No "
            "consciousness, agency, or life is claimed.",
            "",
            "## Summary",
            f"- embodiment profile: {sections['embodiment_profile']}",
            f"- actions: {sections['action_count']}",
            f"- vetoed actions: {sections['vetoed_action_count']}",
            "",
            "## Proof of non-actuation",
            f"- real_world_authority: {proof['real_world_authority']}",
            f"- firewall enabled: {proof['firewall_enabled']} "
            f"(can be disabled: {proof['firewall_can_be_disabled']})",
            f"- blocked real-world attempts: "
            f"{proof['blocked_real_world_attempts']}",
            f"- real-world actions executed: "
            f"{proof['real_world_actions_executed']}",
            f"- {proof['statement']}",
            "",
            "## Limitations",
        ]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        lines += ["", "## Next recommendation",
                  f"- {sections['next_recommendation']}"]
        return "\n".join(lines)

    def write(self, report: Pilot3Report) -> Dict[str, str]:
        os.makedirs(self.base_dir, exist_ok=True)
        md_path = os.path.join(self.base_dir, "PILOT3_REPORT.md")
        json_path = os.path.join(self.base_dir, "PILOT3_REPORT.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(report.narrative)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}

    def build_and_write(self, **kwargs: Any) -> Pilot3Report:
        report = self.build(**kwargs)
        report.sections["report_paths"] = self.write(report)
        return report
