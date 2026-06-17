"""Membrane integration reports -- contracts, bypass, ancestry, pipeline audit.

:class:`MembraneIntegrationReportBuilder` writes the integration report set. Every
report states explicitly that no feeder was started/stopped/controlled, no hardware
was controlled, no network/Git/GitHub/shell/browser/OS access occurred, no commands
were executed, no sensory text was treated as a command, no human label / debug gloss
was treated as ground truth, membrane integration is an architectural audit/
enforcement layer (not evidence of consciousness/life/agency), and no consciousness/
life/agency claim is made. ClaimGuard scans the Markdown when available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .bypass_detector import MembraneBypassDetector
from .downstream_contracts import summary as contract_summary

_WHAT_THIS_DOES_NOT_DO = (
    "No feeder was started, stopped, or controlled.",
    "No hardware was controlled.",
    "No network/Git/GitHub/shell/browser/OS access occurred.",
    "No commands were executed.",
    "No sensory text was treated as a command.",
    "No human label was treated as ground truth.",
    "No debug gloss was treated as ground truth.",
    "Membrane integration is an architectural audit/enforcement layer, not "
    "evidence of consciousness/life/agency.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class MembraneIntegrationReportBuilder:
    """Builds the membrane integration report set (Markdown + JSON)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        bypass = MembraneBypassDetector.summary(rt.bypass_findings)
        contracts = contract_summary(rt.contracts) if rt.contracts else {}
        sections = {
            "purpose": ("ensure live downstream modules consume membrane-"
                        "filtered sensory impressions rather than raw events; "
                        "validate ancestry, evaluate contracts, detect bypasses, "
                        "and audit the live pipeline"),
            "profile": rt.integration_profile.to_dict(),
            "status": rt.integration_status(),
            "membrane_artifacts": rt.load_result.to_dict()
            if rt.load_result else {},
            "ancestry": rt.ancestry.to_dict() if rt.ancestry else {},
            "contracts": contracts,
            "bypass": bypass,
            "pipeline_audit": rt.audit.to_dict() if rt.audit else {},
            "adapters": {k: v.to_dict() for k, v in rt.adapters.items()},
            "blocked": rt.blocked, "blockers": list(rt.blockers),
            "warnings": list(rt.warnings),
            "recommended_next_action": rt.recommended_next_action(),
            "safety_status": rt.safety.snapshot(),
            "what_this_does_not_do": list(_WHAT_THIS_DOES_NOT_DO),
        }
        markdown = self._render_main(sections)
        return {"sections": sections, "claim_guard_safe": _safe(markdown)}

    def _render_main(self, s: Dict[str, Any]) -> str:
        st = s["status"]
        lines = [
            "# Membrane Integration Report", "",
            "_Membrane integration ensures that live downstream modules consume "
            "membrane-filtered sensory impressions rather than raw events. Raw "
            "events remain audit material. It is an architectural audit/"
            "enforcement layer; it does NOT start/stop/configure feeders, control "
            "hardware, access the network/shell/browser/OS, call Git/GitHub, "
            "execute commands, treat sensory text as a command, treat human "
            "labels or debug gloss as ground truth, or make any claim of "
            "consciousness, sentience, biological life, personhood, agency, free "
            "will, emotion, feeling, understanding, self-awareness, or subjective "
            "experience._", "",
            f"- run id: {st['integration_run_id']} "
            f"({st['integration_profile']})",
            f"- blocked: {s['blocked']}",
            f"- membrane present: {st['membrane_present']}; impressions: "
            f"{st['impression_count']}",
            f"- ancestry chains: {st['ancestry_chain_count']} (with impression "
            f"ancestry {st['with_impression_ancestry']}, missing "
            f"{st['missing_ancestry']})",
            f"- bypass findings: {st['bypass_finding_count']} (critical "
            f"{st['critical_bypass_count']}, blocker "
            f"{st['blocker_bypass_count']})",
            f"- raw fallback count: {st['raw_fallback_count']}",
            f"- contract violations: {st['contract_violated_count']}",
            f"- pipeline status: {st['pipeline_status']}",
            f"- recommended next action: {s['recommended_next_action']}",
            "",
        ]
        if s["blockers"]:
            lines += ["## Blockers", ""] + [f"- {b}" for b in s["blockers"]] + [""]
        if s["warnings"]:
            lines += ["## Warnings", ""] + [f"- {w}" for w in s["warnings"]] + [""]
        lines += ["## Limitations", ""]
        lines += [f"- {l}" for l in s["profile"].get("limitations", [])]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in s["what_this_does_not_do"]]
        return "\n".join(lines)

    def _sub_reports(self, s: Dict[str, Any]) -> Dict[str, str]:
        return {
            "MEMBRANE_DOWNSTREAM_CONTRACTS.md": self._contracts_md(s),
            "MEMBRANE_BYPASS_REPORT.md": self._bypass_md(s),
            "MEMBRANE_ANCESTRY_REPORT.md": self._ancestry_md(s),
            "MEMBRANE_PIPELINE_AUDIT.md": self._audit_md(s),
            "MEMBRANE_INTEGRATION_SAFETY_REPORT.md": self._safety_md(s),
        }

    def _contracts_md(self, s: Dict[str, Any]) -> str:
        c = s["contracts"]
        lines = ["# Membrane Downstream Contracts", "",
                 f"- contracts: {c.get('contract_count', 0)}",
                 f"- by status: {c.get('by_status', {})}",
                 f"- violated: {c.get('violated_count', 0)}", ""]
        for con in c.get("contracts", []):
            lines.append(f"## {con['module']}: {con['status']}")
            for r in con["requirements"]:
                lines.append(f"- [{'x' if r['satisfied'] else ' '}] "
                             f"{r['requirement']}"
                             + (f" -- {r['detail']}" if r["detail"] else ""))
            lines.append("")
        lines += ["_Downstream modules should consume membrane-filtered sensory "
                  "impressions, not raw events._"]
        return _guard("\n".join(lines))

    def _bypass_md(self, s: Dict[str, Any]) -> str:
        b = s["bypass"]
        lines = ["# Membrane Bypass Report", "",
                 f"- findings: {b.get('bypass_finding_count', 0)}",
                 f"- by severity: {b.get('by_severity', {})}",
                 f"- worst severity: {b.get('worst_severity')}", ""]
        for f in b.get("findings", []):
            lines.append(f"- [{f['severity']}] {f['finding']}: {f['detail']}")
        lines += ["", "_No bypass may be silently ignored. In strict live mode a "
                  "direct raw-event downstream path is a blocker; raw fallback is "
                  "loudly reported._"]
        return _guard("\n".join(lines))

    def _ancestry_md(self, s: Dict[str, Any]) -> str:
        a = s["ancestry"]
        lines = ["# Membrane Ancestry Report", "",
                 f"- chains: {a.get('ancestry_chain_count', 0)}",
                 f"- with impression ancestry: "
                 f"{a.get('with_impression_ancestry', 0)}",
                 f"- missing ancestry: {a.get('missing_ancestry', 0)}",
                 f"- contaminated ancestry: {a.get('contaminated_ancestry', 0)}",
                 f"- by artifact type: {a.get('by_artifact_type', {})}", "",
                 "_Ancestry runs cognition_trace -> private_sign -> proto_concept "
                 "-> sensory_impression -> receptor -> source_event -> source. "
                 "Missing ancestry is visible; contaminated ancestry downgrades "
                 "or blocks promotion._"]
        return _guard("\n".join(lines))

    def _audit_md(self, s: Dict[str, Any]) -> str:
        au = s["pipeline_audit"]
        lines = ["# Membrane Pipeline Audit", "",
                 f"- overall status: {au.get('overall_status')}",
                 f"- stages: {au.get('stage_count', 0)}", "",
                 "| stage | status | impressions | fallback | bypass |",
                 "| --- | --- | --- | --- | --- |"]
        for stg in au.get("stages", []):
            lines.append(f"| {stg['stage']} | {stg['status']} | "
                         f"{stg['impression_count']} | {stg['fallback_count']} | "
                         f"{stg['bypass_findings']} |")
        lines += ["", "_The audit walks the live perceptual pipeline stage by "
                  "stage; fallback, missing artifacts, and bypasses are all "
                  "visible._"]
        return _guard("\n".join(lines))

    def _safety_md(self, s: Dict[str, Any]) -> str:
        snap = s["safety_status"]
        lines = ["# Membrane Integration Safety Report", "",
                 f"- safety blocks recorded: {snap.get('rejected_count', 0)}",
                 f"- can start feeders: {snap.get('can_start_feeders')}",
                 f"- can allow silent raw downstream: "
                 f"{snap.get('can_allow_silent_raw_downstream')}",
                 f"- can promote without ancestry: "
                 f"{snap.get('can_promote_without_ancestry')}", "",
                 "## Hard rules", ""]
        lines += [f"- {r}" for r in snap.get("hard_rules", [])]
        lines += ["", "_All control/bypass/hiding capabilities are False by "
                  "design._"]
        return _guard("\n".join(lines))

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = os.path.join(state_dir or self.runtime.state_dir, "membrane",
                            "integration")
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "MEMBRANE_INTEGRATION_REPORT.md")
        json_path = os.path.join(base, "MEMBRANE_INTEGRATION_REPORT.json")
        markdown = self._render_main(report["sections"])
        if not report["claim_guard_safe"]:
            markdown = _guard(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        written = [md_path, json_path]
        for name, body in self._sub_reports(report["sections"]).items():
            path = os.path.join(base, name)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)
            written.append(path)
        return {"markdown": md_path, "json": json_path, "documents": written,
                "report": report}


def _safe(text: str) -> bool:
    try:
        from ..governance.compliance import ClaimGuard

        return ClaimGuard().scan_text(text).safe
    except Exception:
        return True


def _guard(text: str) -> str:
    try:
        from ..governance.compliance import ClaimGuard

        guard = ClaimGuard()
        if not guard.scan_text(text).safe:
            return guard.rewrite(text)
    except Exception:
        pass
    return text
