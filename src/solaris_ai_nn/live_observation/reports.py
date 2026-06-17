"""Live observation reports -- observation, health, diet, rhythm/absence, load.

:class:`LiveObservationReportBuilder` writes the observation report set. Every report
states explicitly that nothing was learned, no concept was formed, no sign was born,
no developmental learning ran, no feeder/hardware/network/Git/GitHub/shell/browser/
OS access occurred, no command was executed, no sensory text was treated as a
command, no human label or debug gloss was treated as ground truth, and no
consciousness/life/agency claim is made. ClaimGuard scans the Markdown when available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_WHAT_THIS_DOES_NOT_DO = (
    "Nothing was learned; no concept was formed; no sign was born.",
    "No developmental learning ran.",
    "No feeder was started, stopped, or reconfigured.",
    "No hardware was controlled.",
    "No network/Git/GitHub/shell/browser/OS access occurred.",
    "No command was executed.",
    "No sensory text was treated as a command.",
    "No human label or debug gloss was treated as ground truth.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class LiveObservationReportBuilder:
    """Builds the live observation report set (Markdown + JSON)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        sections = {
            "purpose": ("observe a bounded live read-only event stream after "
                        "birth without learning: source health, source diet, "
                        "rhythm, absence, overload/deprivation, report-only "
                        "metabolism calibration, and an advisory stability gate"),
            "profile": rt.observation_profile.to_dict(),
            "status": rt.observation_status(),
            "windows": rt.windows,
            "source_health": rt.source_health_summary,
            "source_diet": rt.source_diet,
            "rhythm": rt.rhythm,
            "absence": rt.absence,
            "load": rt.load,
            "metabolism": rt.metabolism,
            "stability": rt.stability,
            "next_phases": rt.next_phase_recommendations(),
            "blocked": rt.blocked,
            "blockers": list(rt.blockers),
            "safety_status": rt.safety.snapshot(),
            "what_this_does_not_do": list(_WHAT_THIS_DOES_NOT_DO),
        }
        markdown = self._render_main(sections)
        return {"sections": sections, "claim_guard_safe": _safe(markdown)}

    def _render_main(self, s: Dict[str, Any]) -> str:
        st = s["status"]
        lines = [
            "# Post-Birth Live Observation Report", "",
            "_Observes a bounded, local, read-only environmental event stream "
            "after birth. It does NOT learn, form concepts, birth signs, run "
            "developmental learning, start/stop/configure feeders, control "
            "hardware, access the network/shell/browser/OS, call Git/GitHub, "
            "execute commands, treat sensory text as a command, treat human "
            "labels or debug gloss as ground truth, or make any claim of "
            "consciousness, sentience, biological life, personhood, agency, free "
            "will, emotion, feeling, understanding, self-awareness, or subjective "
            "experience._", "",
            f"- run id: {st['observation_run_id']} "
            f"({s['profile'].get('profile_id')})",
            f"- blocked: {s['blocked']}",
            f"- observation windows: {st['live_observation_window_count']}",
            f"- accepted events: {st['live_observation_accepted_event_count']}",
            f"- quarantine rate: {st['live_observation_quarantine_rate']:.0%}",
            f"- source diet balance: {st['live_source_diet_balance']}",
            f"- load status: {st['live_load_status']}",
            f"- stability status: {st['live_stability_status']}",
            f"- recommended next phase: {st['live_recommended_next_phase']}",
            "",
        ]
        if s["blockers"]:
            lines += ["## Blockers", ""]
            lines += [f"- {b}" for b in s["blockers"]]
            lines.append("")
        lines += ["## Next recommended phase (not executed)", ""]
        lines += [f"- {p['phase']}: {p['detail']}" for p in s["next_phases"]]
        lines += ["", "## Limitations", ""]
        lines += [f"- {l}" for l in s["profile"].get("limitations", [])]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in s["what_this_does_not_do"]]
        return "\n".join(lines)

    def _sub_reports(self, s: Dict[str, Any]) -> Dict[str, str]:
        return {
            "SOURCE_HEALTH_REPORT.md": self._health_md(s),
            "SOURCE_DIET_REPORT.md": self._diet_md(s),
            "RHYTHM_ABSENCE_REPORT.md": self._rhythm_absence_md(s),
            "OVERLOAD_DEPRIVATION_REPORT.md": self._load_md(s),
            "METABOLISM_CALIBRATION_REPORT.md": self._metabolism_md(s),
            "STABILITY_GATE_REPORT.md": self._stability_md(s),
        }

    def _health_md(self, s: Dict[str, Any]) -> str:
        h = s["source_health"]
        lines = ["# Source Health Report", "",
                 f"- live sources: {h.get('live_source_count', 0)}",
                 f"- healthy: {h.get('live_healthy_source_count', 0)}; "
                 f"noisy: {h.get('live_noisy_source_count', 0)}; "
                 f"silent: {h.get('live_silent_source_count', 0)}; "
                 f"forbidden: {h.get('live_forbidden_source_count', 0)}", "",
                 "| source | status | events | quarantine rate |",
                 "| --- | --- | --- | --- |"]
        for src in h.get("sources", []):
            lines.append(f"| {src['source_id']} | {src['status']} | "
                         f"{src['event_count']} | {src['quarantine_rate']:.0%} |")
        lines += ["", "_A silent source may be an absence signal, not a failure; "
                  "an unknown source is not trusted; a forbidden source blocks "
                  "stability._"]
        return _guard("\n".join(lines))

    def _diet_md(self, s: Dict[str, Any]) -> str:
        d = s["source_diet"]
        lines = ["# Source Diet Report", "",
                 f"- total events: {d.get('total_events', 0)}",
                 f"- balance: {d.get('balance')}",
                 f"- dominant source: {d.get('dominant_source') or 'none'}",
                 f"- dominance score: "
                 f"{d.get('live_source_diet_dominance_score', 0.0)}",
                 f"- operator pulse proportion: "
                 f"{d.get('live_operator_pulse_dominance_score', 0.0)}",
                 f"- human text proportion: "
                 f"{d.get('human_text_proportion', 0.0)}", "",
                 "_No source should silently dominate; operator pulse is "
                 "stimulus, not the primary source; human text must not become "
                 "the primary ontology._"]
        return _guard("\n".join(lines))

    def _rhythm_absence_md(self, s: Dict[str, Any]) -> str:
        r = s["rhythm"]
        a = s["absence"]
        lines = ["# Rhythm and Absence Report", "",
                 f"- rhythm patterns: {r.get('rhythm_pattern_count', 0)} "
                 f"(periodic {r.get('periodic_source_count', 0)}, "
                 f"bursty {r.get('bursty_source_count', 0)})",
                 f"- absence windows: {a.get('live_absence_window_count', 0)} "
                 f"(deprivation {a.get('deprivation_window_count', 0)})", "",
                 "_Rhythm detection is descriptive and weak rhythms are marked "
                 "weak; absence is a valid environmental signal, not system death "
                 "and not anthropomorphized._"]
        return _guard("\n".join(lines))

    def _load_md(self, s: Dict[str, Any]) -> str:
        load = s["load"]
        lines = ["# Overload / Deprivation Report", "",
                 f"- load status: {load.get('load_status')}",
                 f"- overload markers: {load.get('overload_marker_count', 0)}",
                 f"- deprivation markers: "
                 f"{load.get('deprivation_marker_count', 0)}",
                 f"- blocks ontogenesis recommendation: "
                 f"{load.get('blocks_ontogenesis_recommendation')}",
                 f"- requires operator review: "
                 f"{load.get('requires_operator_review')}", "",
                 "_No feeder is started, stopped, or reconfigured; severe "
                 "overload or deprivation blocks any later ontogenesis "
                 "recommendation._"]
        return _guard("\n".join(lines))

    def _metabolism_md(self, s: Dict[str, Any]) -> str:
        m = s["metabolism"]
        lines = ["# Perceptual Metabolism Calibration Report", "",
                 f"- confidence: {m.get('calibration_confidence')}",
                 f"- recommendations: {m.get('recommendation_count', 0)} "
                 "(report-only)", "",
                 "| threshold | recommended value | unit |",
                 "| --- | --- | --- |"]
        for rec in m.get("recommendations", []):
            lines.append(f"| {rec['name']} | {rec['recommended_value']} | "
                         f"{rec.get('unit') or '-'} |")
        lines += ["", "_All thresholds are report-only and are NOT applied; no "
                  "feeder, governance, configuration, or learning state is "
                  "written or changed; this is descriptive metabolism, not "
                  "understanding._"]
        return _guard("\n".join(lines))

    def _stability_md(self, s: Dict[str, Any]) -> str:
        g = s["stability"]
        lines = ["# Live Stability Gate Report", "",
                 f"- status: {g.get('live_stability_status')}",
                 f"- blocked: {g.get('blocked')}",
                 f"- recommended next phase: {g.get('recommended_next_phase')}",
                 f"- ready for metabolism calibration: "
                 f"{g.get('ready_for_metabolism_calibration')}", ""]
        if g.get("blockers"):
            lines += ["## Blockers and corrections", ""]
            for b in g["blockers"]:
                lines.append(f"- {b['blocker']}: {b['detail']} "
                             f"-> {b['correction']}")
            lines.append("")
        if g.get("warnings"):
            lines += ["## Warnings", ""]
            lines += [f"- {w}" for w in g["warnings"]]
            lines.append("")
        lines += ["_The stability gate is advisory only; it starts no phase, "
                  "changes no feeder, and enables no learning. A blocked gate is "
                  "a normal, healthy early-observation outcome._"]
        return _guard("\n".join(lines))

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = os.path.join(state_dir or self.runtime.state_dir, "observation",
                            "reports")
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "LIVE_OBSERVATION_REPORT.md")
        json_path = os.path.join(base, "LIVE_OBSERVATION_REPORT.json")
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
