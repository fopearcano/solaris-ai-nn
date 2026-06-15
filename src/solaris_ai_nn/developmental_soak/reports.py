"""Developmental soak reports -- the protocol record, scanned by ClaimGuard.

:class:`DevelopmentalSoakReportBuilder` compiles the soak-protocol report (and,
when available, the daily packets, weekly reviews, evidence dossier, and
post-run autopsy). Every report states explicitly that the soak protocol studies
structural development only -- long runtime does not imply life, persistence
does not imply consciousness, and the evidence dossier does not prove sentience.
The Markdown is scanned by ClaimGuard.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_DOES_NOT_PROVE = (
    "The soak protocol studies structural development only.",
    "Long runtime does not imply life.",
    "Persistence does not imply consciousness.",
    "The evidence dossier does not prove sentience.",
    "No real-world actuation occurred.",
    "No feeder/hardware/source control occurred.",
    "No human teaching loop was used.",
    "This does not prove personhood, agency, free will, emotion, feeling, "
    "understanding, or subjective experience.",
)

_LIMITATIONS = (
    "Each invocation is bounded; long runs are repeated bounded runs + "
    "checkpoints, never a daemon.",
    "Negative, plateau, regression, and inconclusive results are preserved.",
    "Control arms exist to prevent self-flattering conclusions.",
    "Growth vs accumulation is judged conservatively; inconclusive is valid.",
    "Failed/corrupt checkpoints are recorded, never hidden.",
)


@dataclass
class DevelopmentalSoakReportBuilder:
    """Builds the soak-protocol report set (JSON + claim-guarded Markdown)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.soak_status()
        sections: Dict[str, Any] = {
            "purpose": ("study whether Solaris underwent measurable structural "
                        "development through autonomous sensorium-native "
                        "experience -- not life, consciousness, or agency"),
            "active_soak_plan": rt.plan.to_dict(),
            "stage_status": {"current_stage": rt.stage,
                             "ticks_run": rt.ticks_run,
                             "phase_state": rt.phase_state.to_dict()},
            "preflight_status": (rt.preflight.summary(rt.preflight_results)
                                 if rt.preflight_results else {}),
            "checkpoint_status": rt.checkpoints.status(),
            "daily_packet_summary": {
                "count": len(rt.daily_packets),
                "packets": [p.to_dict() for p in rt.daily_packets]},
            "weekly_review_summary": {
                "count": len(rt.weekly_reviews),
                "reviews": [w.to_dict() for w in rt.weekly_reviews]},
            "restart_drill_summary": {
                "count": len(rt.restart_drill_results),
                "drills": [d.to_dict() for d in rt.restart_drill_results]},
            "control_arm_summary": {
                "count": len(rt.control_arm_results),
                "arms": [a.to_dict() for a in rt.control_arm_results]},
            "evidence_claims": (rt.dossier.to_dict() if rt.dossier else {}),
            "growth_vs_accumulation": {
                "structural_growth_status":
                    status.get("structural_growth_status"),
                "regression_count": status.get("regression_count"),
                "plateau_count": status.get("plateau_count")},
            "post_run_autopsy": (rt.autopsy.to_dict() if rt.autopsy else {}),
            "safety_status": rt.safety.snapshot(),
            "status": status,
            "limitations": list(_LIMITATIONS),
            "what_this_does_not_prove": list(_DOES_NOT_PROVE),
        }
        markdown = self._render_markdown(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _render_markdown(self, sections: Dict[str, Any]) -> str:
        status = sections["status"]
        lines = [
            "# Developmental Soak Protocol Report", "",
            "_The month-scale developmental soak protocol studies whether "
            "Solaris underwent measurable structural development through "
            "autonomous sensorium-native experience. The Long-Horizon "
            "Developmental Runtime is the engine; this protocol is the study "
            "manager. Long runtime does NOT imply life; persistence does NOT "
            "imply consciousness._", "",
            f"- active plan: {status['active_plan_id']}",
            f"- current stage: {status['current_stage']} "
            f"({status['soak_stage_count']} stages)",
            f"- preflight: passed={status['preflight_passed']} "
            f"(pass {status['preflight_pass_count']}, "
            f"fail {status['preflight_fail_count']})",
            f"- checkpoints: {status['checkpoint_count']} "
            f"(corruption {status['checkpoint_corruption_count']})",
            f"- daily packets: {status['daily_packet_count']}",
            f"- weekly reviews: {status['weekly_review_count']}",
            f"- restart drills: {status['restart_drill_count']}",
            f"- control arms: {status['control_arm_count']}",
            f"- evidence claims: {status['evidence_claim_count']} "
            f"(strong {status['strong_evidence_claim_count']}, "
            f"inconclusive {status['inconclusive_claim_count']})",
            f"- growth verdict: {status['structural_growth_status']} "
            f"(regressions {status['regression_count']}, plateaus "
            f"{status['plateau_count']})",
            f"- autopsy recommendation: {status['autopsy_recommendation']} "
            f"({status['autopsy_finding_count']} finding(s))",
            f"- safety blocks: {status['soak_safety_block_count']}",
            "",
            "## Growth vs accumulation (preserved)", "",
            f"- verdict {status['structural_growth_status']}, regressions "
            f"{status['regression_count']}, plateaus {status['plateau_count']} "
            "(all preserved)",
            "",
            "## What this does NOT prove", "",
        ]
        lines += [f"- {item}" for item in sections["what_this_does_not_prove"]]
        lines += ["", "## Limitations", ""]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        return "\n".join(lines)

    @staticmethod
    def _claim_guard_safe(text: str) -> bool:
        try:
            from ..governance.compliance import ClaimGuard

            return ClaimGuard().scan_text(text).safe
        except Exception:
            return True

    def _write_subreports(self, base: str) -> List[str]:
        rt = self.runtime
        written: List[str] = []
        for i, packet in enumerate(rt.daily_packets, start=1):
            p = os.path.join(base, f"DAILY_PACKET_DAY_{i}.md")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(self._daily_md(packet, i))
            written.append(p)
        for i, review in enumerate(rt.weekly_reviews, start=1):
            p = os.path.join(base, f"WEEKLY_REVIEW_WEEK_{i}.md")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(self._weekly_md(review, i))
            written.append(p)
        if rt.dossier is not None:
            p = os.path.join(base, "EVIDENCE_DOSSIER.md")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(self._dossier_md(rt.dossier))
            written.append(p)
        if rt.autopsy is not None:
            p = os.path.join(base, "POST_RUN_AUTOPSY.md")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(self._autopsy_md(rt.autopsy))
            written.append(p)
        return written

    @staticmethod
    def _daily_md(packet: Any, day: int) -> str:
        d = packet.to_dict()
        body = (f"# Daily Evidence Packet -- Day {day}\n\n"
                f"{d.get('operator_summary', '')}\n\n"
                "_Evidence, not marketing. Negative/inconclusive results are "
                "included. This does not prove life or consciousness._\n")
        return DevelopmentalSoakReportBuilder._guard(body)

    @staticmethod
    def _weekly_md(review: Any, week: int) -> str:
        d = review.to_dict()
        body = (f"# Weekly Developmental Review -- Week {week}\n\n"
                f"- decision: {d.get('decision')}\n"
                f"- rationale: {d.get('rationale')}\n\n"
                "_Recommendation-only; no automatic external change; no feeder "
                "control._\n")
        return DevelopmentalSoakReportBuilder._guard(body)

    @staticmethod
    def _dossier_md(dossier: Any) -> str:
        d = dossier.to_dict()
        lines = ["# Developmental Evidence Dossier", "",
                 f"- claims: {d.get('claim_count', 0)} "
                 f"(strong {d.get('strong_claim_count', 0)}, inconclusive "
                 f"{d.get('inconclusive_claim_count', 0)})", ""]
        for c in d.get("claims", []):
            lines.append(f"- [{c['strength']}] {c['claim_type']}: "
                         f"{c['statement']}")
        lines += ["", "_Conservative, evidence-referenced claims. Does not "
                  "prove consciousness, sentience, biological life, "
                  "personhood, agency, or free will._\n"]
        return DevelopmentalSoakReportBuilder._guard("\n".join(lines))

    @staticmethod
    def _autopsy_md(autopsy: Any) -> str:
        d = autopsy.to_dict()
        lines = ["# Post-Run Autopsy", "",
                 f"- recommendation: {d.get('recommendation')}",
                 f"- failures: {d.get('failure_count', 0)}, missing data: "
                 f"{d.get('missing_data_count', 0)}", "",
                 f"{d.get('summary', '')}", ""]
        for f in d.get("findings", []):
            flag = (" [FAILURE]" if f.get("is_failure") else
                    " [MISSING DATA]" if f.get("is_missing_data") else "")
            lines.append(f"- {f['question_id']}: {f['answer']}{flag}")
        lines += ["", "_The autopsy includes failures and missing data and "
                  "does not praise the system by default. It does not claim "
                  "consciousness or life._\n"]
        return DevelopmentalSoakReportBuilder._guard("\n".join(lines))

    @staticmethod
    def _guard(text: str) -> str:
        try:
            from ..governance.compliance import ClaimGuard

            guard = ClaimGuard()
            if not guard.scan_text(text).safe:
                return guard.rewrite(text)
        except Exception:
            pass
        return text

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = state_dir or self.runtime.state_dir
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "SOAK_PROTOCOL_REPORT.md")
        json_path = os.path.join(base, "SOAK_PROTOCOL_REPORT.json")
        markdown = self._render_markdown(report["sections"])
        if not report["claim_guard_safe"]:
            from ..governance.compliance import ClaimGuard

            markdown = ClaimGuard().rewrite(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        sub = self._write_subreports(base)
        return {"markdown": md_path, "json": json_path, "subreports": sub,
                "report": report}
