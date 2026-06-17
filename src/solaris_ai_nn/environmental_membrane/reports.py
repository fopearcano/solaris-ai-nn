"""Environmental membrane reports -- receptors, permeability, impressions, immune.

:class:`EnvironmentalMembraneReportBuilder` writes the membrane report set. Every
report states explicitly that no feeder was started/stopped/controlled, no hardware
was controlled, no network/Git/GitHub/shell/browser/OS access occurred, no commands
were executed, no sensory text was treated as a command, no human label or debug
gloss was treated as ground truth, sensory impressions are operational boundary
records (not evidence of consciousness/life/agency), and no consciousness/life/agency
claim is made. ClaimGuard scans the Markdown when available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

_WHAT_THIS_DOES_NOT_DO = (
    "No feeder was started, stopped, or controlled.",
    "No hardware was controlled.",
    "No network/Git/GitHub/shell/browser/OS access occurred.",
    "No commands were executed.",
    "No sensory text was treated as a command.",
    "No human label was treated as ground truth.",
    "No debug gloss was treated as ground truth.",
    "Sensory impressions are operational boundary records, not evidence of "
    "consciousness/life/agency.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class EnvironmentalMembraneReportBuilder:
    """Builds the environmental membrane report set (Markdown + JSON)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.membrane_status()
        sections = {
            "purpose": ("convert validated read-only events into sensory "
                        "impressions through receptor matching, permeability "
                        "regulation, salience modulation, source-pressure "
                        "analysis, contamination checks, immune responses, and "
                        "membrane memory -- the perceptual boundary"),
            "profile": rt.membrane_profile.to_dict(),
            "status": status,
            "governance": rt.governance_result,
            "feeder_registry_present": bool(
                rt.feeders and rt.feeders.present) if rt.feeders else False,
            "receptor_field": (rt.receptor_field.index()
                               if rt.receptor_field else {}),
            "source_pressure": rt.source_pressure,
            "permeability": rt.permeability_decisions,
            "contamination": rt.contamination_results,
            "impressions": (rt.impression_store.index()
                            if rt.impression_store else {}),
            "downstream_readiness": rt.downstream_readiness(),
            "membrane_memory": (rt.membrane_memory.index()
                                if rt.membrane_memory else {}),
            "blocked": rt.blocked, "blockers": list(rt.blockers),
            "warnings": list(rt.warnings),
            "safety_status": rt.safety.snapshot(),
            "what_this_does_not_do": list(_WHAT_THIS_DOES_NOT_DO),
        }
        markdown = self._render_main(sections)
        return {"sections": sections, "claim_guard_safe": _safe(markdown)}

    def _render_main(self, s: Dict[str, Any]) -> str:
        st = s["status"]
        lines = [
            "# Environmental Membrane Report", "",
            "_The Environmental Membrane is the perceptual boundary between "
            "validated external events and Solaris perception. It converts "
            "validated read-only events into sensory impressions. It does NOT "
            "start/stop/configure feeders, control hardware, access the network/"
            "shell/browser/OS, call Git/GitHub, execute commands, treat sensory "
            "text as a command, treat human labels or debug gloss as ground "
            "truth, or make any claim of consciousness, sentience, biological "
            "life, personhood, agency, free will, emotion, feeling, "
            "understanding, self-awareness, or subjective experience._", "",
            f"- run id: {st['membrane_run_id']} ({st['membrane_profile']})",
            f"- blocked: {s['blocked']}",
            f"- receptors: {st['membrane_receptor_count']}",
            f"- events in: {st['membrane_event_input_count']}; impressions: "
            f"{st['membrane_impression_count']}",
            f"- allowed: {st['membrane_allowed_count']}; attenuated: "
            f"{st['membrane_attenuated_count']}; blocked: "
            f"{st['membrane_blocked_count']}; quarantined: "
            f"{st['membrane_quarantined_count']}",
            f"- absence/overload/deprivation impressions: "
            f"{st['membrane_absence_impression_count']} / "
            f"{st['membrane_overload_impression_count']} / "
            f"{st['membrane_deprivation_impression_count']}",
            f"- source pressure: {st['source_pressure_status']} "
            f"(dominance {st['membrane_source_pressure_dominance_score']}, "
            f"operator {st['membrane_operator_dominance_score']})",
            f"- contamination findings: {st['membrane_contamination_count']}",
            f"- downstream ready: {s['downstream_readiness']['downstream_ready']}"
            f" -> {s['downstream_readiness']['recommended_next_phase']}",
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
            "RECEPTOR_FIELD_REPORT.md": self._receptor_md(s),
            "PERMEABILITY_REPORT.md": self._permeability_md(s),
            "SENSORY_IMPRESSION_REPORT.md": self._impression_md(s),
            "SOURCE_PRESSURE_REPORT.md": self._pressure_md(s),
            "SALIENCE_REPORT.md": self._salience_md(s),
            "CONTAMINATION_REPORT.md": self._contamination_md(s),
            "IMMUNE_RESPONSE_REPORT.md": self._immune_md(s),
            "MEMBRANE_MEMORY_REPORT.md": self._memory_md(s),
            "MEMBRANE_SAFETY_REPORT.md": self._safety_md(s),
        }

    def _receptor_md(self, s: Dict[str, Any]) -> str:
        rf = s["receptor_field"]
        lines = ["# Receptor Field Report", "",
                 f"- receptors: {rf.get('membrane_receptor_count', 0)}", "",
                 "| receptor | sources | permeability | salience | risk |",
                 "| --- | --- | --- | --- | --- |"]
        for r in rf.get("receptors", []):
            lines.append(f"| {r['receptor_id']} | {r['accepted_source_ids']} | "
                         f"{r['baseline_permeability']} | "
                         f"{r['baseline_salience']} | {r['baseline_risk']} |")
        lines += ["", "_The unknown-source receptor is conservative; the "
                  "operator-pulse receptor is attenuated by default; debug gloss "
                  "never defines internal truth._"]
        return _guard("\n".join(lines))

    def _permeability_md(self, s: Dict[str, Any]) -> str:
        from .permeability import MembranePermeabilityGate

        decisions = [self.runtime._mk_decision(d) for d in s["permeability"]]
        summ = MembranePermeabilityGate.summary(decisions)
        lines = ["# Permeability Report", "",
                 f"- allowed: {summ['membrane_allowed_count']}; attenuated: "
                 f"{summ['membrane_attenuated_count']}; amplified: "
                 f"{summ['membrane_amplified_count']}",
                 f"- deferred: {summ['membrane_deferred_count']}; blocked: "
                 f"{summ['membrane_blocked_count']}; quarantined: "
                 f"{summ['membrane_quarantined_count']}", "",
                 "_The membrane says allowed/blocked/attenuated/amplified/"
                 "deferred/quarantined -- not merely valid/invalid; every "
                 "decision is explained. Blocked and quarantined impressions are "
                 "visible, never hidden._"]
        return _guard("\n".join(lines))

    def _impression_md(self, s: Dict[str, Any]) -> str:
        idx = s["impressions"]
        lines = ["# Sensory Impression Report", "",
                 f"- impressions: {idx.get('membrane_impression_count', 0)}",
                 f"- by kind: {idx.get('by_kind', {})}",
                 f"- by permeability status: "
                 f"{idx.get('by_permeability_status', {})}",
                 f"- blocked: {idx.get('blocked_impression_count', 0)}", "",
                 "_Sensory impressions are the first internal perceptual objects "
                 "and what downstream modules should consume; raw events should "
                 "not be used directly once the membrane is integrated. They are "
                 "operational boundary records, not evidence of consciousness._"]
        return _guard("\n".join(lines))

    def _pressure_md(self, s: Dict[str, Any]) -> str:
        p = s["source_pressure"]
        lines = ["# Source Pressure Report", "",
                 f"- status: {p.get('status')}",
                 f"- dominant source: {p.get('dominant_source') or 'none'}",
                 f"- dominance score: "
                 f"{p.get('membrane_source_pressure_dominance_score', 0.0)}",
                 f"- operator dominance: "
                 f"{p.get('membrane_operator_dominance_score', 0.0)}",
                 f"- human-text dominance: "
                 f"{p.get('human_text_dominance_score', 0.0)}",
                 f"- per-source status: {p.get('per_source_status', {})}", "",
                 "_Source pressure informs permeability but never modifies "
                 "feeders; recommendations are report-only; dominance is always "
                 "visible._"]
        return _guard("\n".join(lines))

    def _salience_md(self, s: Dict[str, Any]) -> str:
        idx = s["impressions"]
        lines = ["# Salience Report", "",
                 f"- impressions: {idx.get('membrane_impression_count', 0)}", "",
                 "_Salience is attention weighting, not truth or intelligence. "
                 "High salience can still be contaminated; operator-pulse and "
                 "human-text salience are capped by default._"]
        return _guard("\n".join(lines))

    def _contamination_md(self, s: Dict[str, Any]) -> str:
        from .contamination import MembraneContaminationAnalyzer

        results = [self.runtime._mk_contamination(c)
                   for c in s["contamination"]]
        summ = MembraneContaminationAnalyzer.summary(results)
        lines = ["# Contamination Report", "",
                 f"- contamination findings: "
                 f"{summ['membrane_contamination_count']}",
                 f"- contaminated events: {summ['contaminated_event_count']}",
                 f"- blocking events: {summ['blocking_event_count']}",
                 f"- contamination types: {summ['contamination_types']}", "",
                 "_Contamination is recorded even when an event is allowed "
                 "attenuated; high contamination blocks or quarantines; scores "
                 "propagate to sensory impressions. No contamination is hidden._"]
        return _guard("\n".join(lines))

    def _immune_md(self, s: Dict[str, Any]) -> str:
        from .immune_response import MembraneImmuneResponse

        summ = MembraneImmuneResponse.summary(self.runtime.immune_records)
        lines = ["# Immune Response Report", "",
                 f"- responses: {summ['membrane_immune_response_count']}",
                 f"- actions: {summ['action_counts']}", "",
                 "_Immune response is local metadata and routing only. It changes "
                 "no feeder behavior, modifies no source files, deletes no "
                 "events, and preserves blocked/quarantined evidence._"]
        return _guard("\n".join(lines))

    def _memory_md(self, s: Dict[str, Any]) -> str:
        m = s["membrane_memory"]
        lines = ["# Membrane Memory Report", "",
                 f"- sources: {m.get('membrane_memory_source_count', 0)}",
                 f"- toxic sources: {m.get('toxic_source_count', 0)}", "",
                 "_Boundary memory, not cognition. Append-only; toxic history is "
                 "never deleted; a bad source is never silently forgiven; "
                 "permanent blocks come only from governance/safety._"]
        return _guard("\n".join(lines))

    def _safety_md(self, s: Dict[str, Any]) -> str:
        snap = s["safety_status"]
        lines = ["# Membrane Safety Report", "",
                 f"- safety blocks recorded: {snap.get('rejected_count', 0)}",
                 f"- can start feeders: {snap.get('can_start_feeders')}",
                 f"- can access network: {snap.get('can_access_network')}",
                 f"- can bypass membrane: {snap.get('can_bypass_membrane')}",
                 "", "## Hard rules", ""]
        lines += [f"- {r}" for r in snap.get("hard_rules", [])]
        lines += ["", "_All control/bypass capabilities are False by design._"]
        return _guard("\n".join(lines))

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = os.path.join(state_dir or self.runtime.state_dir, "membrane",
                            "reports")
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "ENVIRONMENTAL_MEMBRANE_REPORT.md")
        json_path = os.path.join(base, "ENVIRONMENTAL_MEMBRANE_REPORT.json")
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
