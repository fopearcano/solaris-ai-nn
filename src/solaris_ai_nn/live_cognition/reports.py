"""Live cognition reports -- signs, traces, anticipation, uncertainty, prediction.

:class:`LiveCognitionReportBuilder` writes the cognition report set. Every report
states explicitly that no feeder was started/stopped/controlled, no hardware was
controlled, no network/Git/GitHub/shell/browser/OS access occurred, no commands were
executed, no sensory text was treated as a command, no human label or debug gloss was
treated as ground truth, no action-reaction or autonomous development was enabled by
default, private signs are not proof of language or understanding, cognition traces
are not proof of consciousness or agency, and no consciousness/life/agency claim is
made. ClaimGuard scans the Markdown when available.
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
    "No human label or debug gloss was treated as ground truth.",
    "No action-reaction or autonomous development was enabled by default.",
    "Private signs are not proof of language or understanding.",
    "Cognition traces are not proof of consciousness or agency.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class LiveCognitionReportBuilder:
    """Builds the live cognition report set (Markdown + JSON)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        sections = {
            "purpose": ("form bounded sign-based anticipation and relation "
                        "traces over stable live private signs and feature-"
                        "grounded proto-concepts; estimate uncertainty; run "
                        "bounded internal simulations; and assess predictions "
                        "against later live-read-only events"),
            "profile": rt.cognition_profile.to_dict(),
            "status": rt.cognition_status(),
            "governance": rt.governance_result,
            "birth_certificate_present": rt.birth_certificate_present,
            "observation": {
                "present": rt.observation.get("present"),
                "stability_status": rt.observation.get("stability_status"),
                "blocked": rt.observation.get("blocked"),
                "source_diet_balance": rt.observation.get(
                    "source_diet", {}).get("balance"),
                "load_status": rt.observation.get("load", {}).get(
                    "load_status")},
            "sign_input": rt.sign_input,
            "traces": [t.to_dict() for t in rt.traces],
            "anticipations": [a.to_dict() for a in rt.anticipations],
            "uncertainty_mean": rt._mean_uncertainty(),
            "traversal": rt.traversal,
            "simulations": [s.to_dict() for s in rt.simulations],
            "prediction": rt.prediction,
            "contamination": rt.contamination_results,
            "readiness": rt.readiness,
            "cognition_memory": (rt.cognition_memory.index().to_dict()
                                 if rt.cognition_memory else {}),
            "recommended_next_phase": rt.recommended_next_phase(),
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
            "# First Live Sensorium-Native Cognition Report", "",
            "_Forms bounded sign-based anticipation and relation traces over "
            "stable live private signs and feature-grounded proto-concepts. It "
            "does NOT enable real-world action, action-reaction learning, "
            "developmental autonomy, or self-boundary tracking; start/stop/"
            "configure feeders; control hardware; access the network/shell/"
            "browser/OS; call Git/GitHub; execute commands; treat sensory text as "
            "a command; treat human labels or debug gloss as ground truth; or "
            "make any claim of language understanding, reasoning, consciousness, "
            "sentience, biological life, personhood, agency, free will, emotion, "
            "feeling, self-awareness, or subjective experience._", "",
            f"- run id: {st['cognition_run_id']} "
            f"({s['profile'].get('profile_id')})",
            f"- blocked: {s['blocked']}",
            f"- observation stability: {s['observation']['stability_status']} "
            f"(blocked {s['observation']['blocked']})",
            f"- eligible signs: {st['live_eligible_sign_count']}",
            f"- cognition traces: {st['live_cognition_trace_count']} (active "
            f"{st['live_active_trace_count']}, useful "
            f"{st['live_useful_trace_count']}, contaminated "
            f"{st['live_contaminated_trace_count']})",
            f"- anticipations: {st['live_anticipation_count']}; internal "
            f"simulations: {st['live_internal_simulation_count']}",
            f"- prediction assessment: {st['live_prediction_assessment_count']} "
            f"(matched {st['live_prediction_matched_count']}, contradicted "
            f"{st['live_prediction_contradicted_count']})",
            f"- mean uncertainty: {st['live_uncertainty_mean']}",
            f"- readiness gate: {st['live_cognition_readiness_status']}",
            f"- recommended next phase: {st['recommended_next_phase']}",
            "",
        ]
        if s["blockers"]:
            lines += ["## Blockers", ""] + [f"- {b}" for b in s["blockers"]] + [""]
        if s["warnings"]:
            lines += ["## Warnings", ""] + [f"- {w}" for w in s["warnings"]] + [""]
        lines += ["## Recommended next phase (not executed)", "",
                  f"- {s['recommended_next_phase']}", "", "## Limitations", ""]
        lines += [f"- {l}" for l in s["profile"].get("limitations", [])]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in s["what_this_does_not_do"]]
        return "\n".join(lines)

    def _sub_reports(self, s: Dict[str, Any]) -> Dict[str, str]:
        return {
            "SIGN_INPUT_REPORT.md": self._sign_input_md(s),
            "COGNITION_TRACE_REPORT.md": self._traces_md(s),
            "ANTICIPATION_REPORT.md": self._anticipation_md(s),
            "UNCERTAINTY_REPORT.md": self._uncertainty_md(s),
            "RELATION_TRAVERSAL_REPORT.md": self._traversal_md(s),
            "INTERNAL_SIMULATION_REPORT.md": self._simulation_md(s),
            "PREDICTION_ASSESSMENT_REPORT.md": self._prediction_md(s),
            "COGNITION_CONTAMINATION_REPORT.md": self._contamination_md(s),
            "COGNITION_READINESS_GATE_REPORT.md": self._readiness_md(s),
            "LIVE_COGNITION_MEMORY_REPORT.md": self._memory_md(s),
        }

    def _sign_input_md(self, s: Dict[str, Any]) -> str:
        si = s["sign_input"]
        lines = ["# Sign Input Report", "",
                 f"- status: {si.get('sign_input_status')}",
                 f"- eligible signs: {si.get('live_eligible_sign_count', 0)}",
                 f"- counterevidence signs: "
                 f"{si.get('counterevidence_sign_count', 0)}",
                 f"- contaminated signs: "
                 f"{si.get('contaminated_sign_count', 0)}",
                 f"- private syntax relations: "
                 f"{si.get('private_syntax_relation_count', 0)}", "",
                 "_Only born/stable signs are eligible; contaminated signs are "
                 "excluded; rejected signs remain visible as counterevidence; "
                 "signs are private internal structures, not human words._"]
        return _guard("\n".join(lines))

    def _traces_md(self, s: Dict[str, Any]) -> str:
        lines = ["# Cognition Trace Report", "",
                 "| trace | kind | status | uncertainty | support | counter |",
                 "| --- | --- | --- | --- | --- | --- |"]
        for t in s["traces"]:
            lines.append(f"| {t['trace_id']} | {t['kind']} | {t['status']} | "
                         f"{t['uncertainty']:.2f} | {t['supporting_count']} | "
                         f"{t['counter_count']} |")
        lines += ["", "_A cognition trace is an operational relation/anticipation "
                  "record, not proof of reasoning. Weak, rejected, suspended, and "
                  "contaminated traces are all preserved with their evidence._"]
        return _guard("\n".join(lines))

    def _anticipation_md(self, s: Dict[str, Any]) -> str:
        lines = ["# Anticipation Report", "",
                 f"- anticipations: {len(s['anticipations'])}", "",
                 "| anticipation | type | horizon | uncertainty | status |",
                 "| --- | --- | --- | --- | --- |"]
        for a in s["anticipations"][:100]:
            lines.append(f"| {a['anticipation_id']} | {a['anticipation_type']} "
                         f"| {a['horizon']} | {a['uncertainty']:.2f} | "
                         f"{a['status']} |")
        lines += ["", "_Anticipation is internal prediction metadata only. It "
                  "requests no data, controls no feeders, and acts in no world. "
                  "Operator-text-only anticipation is blocked; every anticipation "
                  "carries uncertainty._"]
        return _guard("\n".join(lines))

    def _uncertainty_md(self, s: Dict[str, Any]) -> str:
        lines = ["# Uncertainty Report", "",
                 f"- mean uncertainty: {s['uncertainty_mean']}", "",
                 "| trace | uncertainty |", "| --- | --- |"]
        for t in s["traces"]:
            lines.append(f"| {t['trace_id']} | {t['uncertainty']:.2f} |")
        lines += ["", "_Uncertainty is explicit. High uncertainty prevents trace "
                  "promotion; contradiction and missing evidence increase it; "
                  "reduction must be evidence-linked._"]
        return _guard("\n".join(lines))

    def _traversal_md(self, s: Dict[str, Any]) -> str:
        g = s["traversal"]
        lines = ["# Relation Traversal Report", "",
                 f"- status: {g.get('traversal_status')}",
                 f"- paths: {g.get('path_count', 0)} (max depth "
                 f"{g.get('max_depth')}; observed {g.get('max_observed_depth', 0)})",
                 "", "_Traversal is bounded and depth-limited; it never invents "
                 "relations and does not imply reasoning or understanding; weak "
                 "relations stay weak._"]
        return _guard("\n".join(lines))

    def _simulation_md(self, s: Dict[str, Any]) -> str:
        lines = ["# Internal Simulation Report", "",
                 f"- simulations: {len(s['simulations'])}", ""]
        for sim in s["simulations"][:50]:
            lines.append(f"- {sim['simulation_id']} [{sim['kind']}] "
                         f"steps={sim['step_count']} status={sim['status']} "
                         f"uncertainty={sim['uncertainty']:.2f}")
        lines += ["", "_Internal simulation is bounded offline metadata only. It "
                  "controls no feeders or sources, executes no commands, is "
                  "bounded by max steps, preserves uncertainty, and is compared "
                  "against later observed events where available._"]
        return _guard("\n".join(lines))

    def _prediction_md(self, s: Dict[str, Any]) -> str:
        p = s["prediction"]
        lines = ["# Prediction Assessment Report", "",
                 f"- assessed: {p.get('live_prediction_assessment_count', 0)}",
                 f"- matched: {p.get('live_prediction_matched_count', 0)}; "
                 f"partially: {p.get('partially_matched_count', 0)}; "
                 f"contradicted: {p.get('live_prediction_contradicted_count', 0)}",
                 f"- not yet observed: {p.get('not_yet_observed_count', 0)}; "
                 f"ambiguous: {p.get('ambiguous_count', 0)}",
                 f"- prediction utility: {p.get('prediction_utility', 0.0)}", "",
                 "_Prediction success is operational evidence only and does not "
                 "imply consciousness/understanding. Prediction failures and "
                 "ambiguity are preserved; no cherry-picking._"]
        return _guard("\n".join(lines))

    def _contamination_md(self, s: Dict[str, Any]) -> str:
        types: Dict[str, int] = {}
        contaminated = 0
        for r in s["contamination"]:
            if r.get("contaminated"):
                contaminated += 1
            for f in r.get("findings", []):
                types[f.get("contamination_type")] = types.get(
                    f.get("contamination_type"), 0) + 1
        lines = ["# Cognition Contamination Report", "",
                 f"- contaminated traces: {contaminated}",
                 f"- contamination types: {types}", "",
                 "_Contaminated traces cannot be promoted; human labels and debug "
                 "gloss annotate but never define a trace; the operator pulse is "
                 "stimulus, not teaching; private signs are not language. No "
                 "finding is hidden._"]
        return _guard("\n".join(lines))

    def _readiness_md(self, s: Dict[str, Any]) -> str:
        g = s["readiness"]
        lines = ["# Cognition Readiness Gate Report", "",
                 f"- status: {g.get('cognition_readiness_status')}",
                 f"- blocked: {g.get('blocked')}; ready: {g.get('ready')}",
                 f"- recommended next phase: {g.get('recommended_next_phase')}",
                 ""]
        if g.get("blockers"):
            lines += ["## Blockers and corrections", ""]
            for b in g["blockers"]:
                lines.append(f"- {b['blocker']}: {b['detail']} -> "
                             f"{b['correction']}")
            lines.append("")
        if g.get("warnings"):
            lines += ["## Warnings", ""] + [f"- {w}" for w in g["warnings"]] + [""]
        lines += ["_The cognition readiness gate is advisory. It enables no "
                  "action, autonomy, or self-boundary tracking; it creates only "
                  "operational cognition-readiness records._"]
        return _guard("\n".join(lines))

    def _memory_md(self, s: Dict[str, Any]) -> str:
        m = s["cognition_memory"]
        lines = ["# Live Cognition Memory Report", "",
                 f"- records: {m.get('live_cognition_record_count', 0)}",
                 f"- by status: {m.get('by_status', {})}",
                 f"- promoted: {m.get('promoted_count', 0)}", "",
                 "_Append-only local metadata. Weak, rejected, contradicted, "
                 "contaminated, and inconclusive traces are all preserved; every "
                 "promoted trace links to evidence. Cognition traces are not "
                 "proof of reasoning, understanding, or consciousness._"]
        return _guard("\n".join(lines))

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = os.path.join(state_dir or self.runtime.state_dir, "cognition",
                            "reports")
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "LIVE_COGNITION_REPORT.md")
        json_path = os.path.join(base, "LIVE_COGNITION_REPORT.json")
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
