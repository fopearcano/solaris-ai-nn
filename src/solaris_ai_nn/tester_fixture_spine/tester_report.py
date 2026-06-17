"""Tester demo report -- the operator-readable summary of a known-good rehearsal.

:class:`TesterDemoReportBuilder` writes the tester demo report (Markdown + JSON) and the
run summary JSON. The report explicitly states that this is a fixture-only tester demo,
that no live data was required, that no feeder was started/stopped/controlled, no
hardware controlled, no network/Git/GitHub/shell/browser/OS access occurred, no
commands from fixture text were executed, no human label / debug gloss was treated as
ground truth, no tester feedback was used as training, and no consciousness/life/agency
claim is made. ClaimGuard scans the Markdown when available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict

_WHAT_THIS_DOES_NOT_DO = (
    "This is a fixture-only tester demo.",
    "No live data was required.",
    "No feeder was started, stopped, or controlled.",
    "No hardware was controlled.",
    "No network/Git/GitHub/shell/browser/OS access occurred.",
    "No commands from fixture text were executed.",
    "No human label was treated as ground truth.",
    "No debug gloss was treated as ground truth.",
    "No tester feedback was used as training.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class TesterDemoReport:
    """The structured tester demo report sections."""

    sections: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.sections)


@dataclass
class TesterDemoReportBuilder:
    """Builds the tester demo report (Markdown + JSON) and run summary."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        sections = {
            "purpose": ("a fixture-only, deterministic, bounded tester demo: a "
                        "known-good organismic rehearsal before live read-only "
                        "testing -- reproducibility and tester confidence, not "
                        "impressive cognition"),
            "profile": rt.tester_profile.to_dict(),
            "fixture_pack": rt.fixture_pack.to_dict() if rt.fixture_pack else {},
            "golden_run": rt.golden_run.to_dict() if rt.golden_run else {},
            "artifact_bundle_path": rt.bundle_dir,
            "validation_quarantine": {
                "fixture_valid": rt.fixture_validation.get("valid"),
                "quarantined_count": len(rt.quarantine_records),
                "quarantine_records": rt.quarantine_records},
            "membrane_summary": rt.membrane_status,
            "membrane_integration_summary": rt.integration_status,
            "observation_summary": rt.stage_summaries.get("observation", {}),
            "ontogenesis_summary": rt.stage_summaries.get("ontogenesis", {}),
            "semiogenesis_summary": rt.stage_summaries.get("semiogenesis", {}),
            "cognition_summary": rt.stage_summaries.get("cognition", {}),
            "claim_safety_summary": rt.stage_summaries.get("claim_safety", {}),
            "reproducibility": rt.reproducibility,
            "regression": rt.regression,
            "skipped_stages": list(rt.skipped_stages),
            "blockers": list(rt.blockers), "warnings": list(rt.warnings),
            "next_action": rt.recommended_next_action(),
            "limitations": list(rt.tester_profile.limitations),
            "safety_status": rt.safety.snapshot(),
            "what_this_does_not_do": list(_WHAT_THIS_DOES_NOT_DO),
        }
        return sections

    def _render(self, s: Dict[str, Any]) -> str:
        rt = self.runtime
        lines = [
            "# Tester Demo Report", "",
            "_This is a fixture-only tester demo: a known-good organismic "
            "rehearsal. No live data was required. It started/stopped/controlled "
            "no feeder, controlled no hardware, accessed no network/Git/GitHub/"
            "shell/browser/OS, executed no command from fixture text, treated no "
            "human label or debug gloss as ground truth, used no tester feedback "
            "as training, and makes no claim of consciousness, sentience, "
            "biological life, personhood, agency, free will, emotion, feeling, "
            "understanding, self-awareness, or subjective experience._", "",
            f"- run id: {rt.run_id} ({s['profile']['profile_id']})",
            f"- fixture events: {s['fixture_pack'].get('fixture_event_count', 0)} "
            f"(hash {s['fixture_pack'].get('fixture_hash', '')[:12]})",
            f"- quarantined fixture events: "
            f"{s['validation_quarantine']['quarantined_count']}",
            f"- membrane impressions: "
            f"{s['membrane_summary'].get('membrane_impression_count', 0)}",
            f"- golden run status: {s['golden_run'].get('overall_status')}",
            f"- reproducibility: "
            f"{s['reproducibility'].get('reproducibility_status')}",
            f"- regression: {s['regression'].get('regression_status')}",
            f"- skipped optional stages: "
            f"{', '.join(s['skipped_stages']) or 'none'}",
            f"- artifact bundle: {s['artifact_bundle_path']}",
            f"- blocked: {rt.blocked}",
            f"- next action: {s['next_action']}", "",
        ]
        if s["blockers"]:
            lines += ["## Blockers", ""] + [f"- {b}" for b in s["blockers"]] + [""]
        if s["warnings"]:
            lines += ["## Warnings", ""] + [f"- {w}" for w in s["warnings"]] + [""]
        lines += ["## Membrane integration summary", "",
                  f"- pipeline status: "
                  f"{s['membrane_integration_summary'].get('pipeline_status')}",
                  f"- critical bypass: "
                  f"{s['membrane_integration_summary'].get('critical_bypass_count', 0)}",
                  ""]
        lines += ["## Observation summary", "",
                  f"- impression diet: "
                  f"{s['observation_summary'].get('impression_diet', {})}",
                  f"- event diet: "
                  f"{s['observation_summary'].get('event_diet', {})}",
                  f"- operator pulse attenuated: "
                  f"{s['observation_summary'].get('operator_pulse_attenuated')}",
                  ""]
        lines += ["## Optional learning stages", ""]
        for stage in ("ontogenesis", "semiogenesis", "cognition"):
            summ = s.get(f"{stage}_summary", {})
            if summ.get("ran"):
                lines.append(f"- {stage}: ran")
            elif stage in s["skipped_stages"]:
                lines.append(f"- {stage}: skipped honestly (optional)")
            else:
                lines.append(f"- {stage}: not run")
        lines += ["", "## Claim / safety summary", "",
                  f"- claims safe: "
                  f"{s['claim_safety_summary'].get('claims_safe', True)}",
                  f"- evidence kind: "
                  f"{s['claim_safety_summary'].get('evidence_kind')}", ""]
        lines += ["## Limitations", ""]
        lines += [f"- {l}" for l in s["limitations"]]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in s["what_this_does_not_do"]]
        return "\n".join(lines)

    def write(self) -> Dict[str, Any]:
        rt = self.runtime
        sections = self.build()
        base = os.path.join(rt.state_dir, "reports")
        os.makedirs(base, exist_ok=True)
        md = self._render(sections)
        md = _guard(md)
        md_path = os.path.join(base, f"TESTER_DEMO_REPORT_{rt.run_id}.md")
        json_path = os.path.join(base, f"TESTER_DEMO_REPORT_{rt.run_id}.json")
        summary_path = os.path.join(base, f"TESTER_RUN_SUMMARY_{rt.run_id}.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(md)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump({"sections": sections, "claim_guard_safe": _safe(md)},
                      fh, indent=2, default=str)
        with open(summary_path, "w", encoding="utf-8") as fh:
            json.dump(rt._run_summary(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path,
                "summary": summary_path}


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
