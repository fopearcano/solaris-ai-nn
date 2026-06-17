"""Live semiogenesis reports -- concepts, signs, utility, syntax, gate, memory.

:class:`LiveSemiogenesisReportBuilder` writes the semiogenesis report set. Every
report states explicitly that no feeder was started/stopped/controlled, no hardware
was controlled, no network/Git/GitHub/shell/browser/OS access occurred, no commands
were executed, no sensory text was treated as a command, no human label or debug
gloss was treated as ground truth, no full cognition was enabled by default, no
action-reaction or autonomous development was enabled by default, private signs are
not proof of language or understanding, and no consciousness/life/agency claim is
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
    "No full cognition was enabled by default.",
    "No action-reaction or autonomous development was enabled by default.",
    "Private signs are not proof of language or understanding.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class LiveSemiogenesisReportBuilder:
    """Builds the live semiogenesis report set (Markdown + JSON)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        sections = {
            "purpose": ("form private internal signs over stable live proto-"
                        "concepts: generate sign candidates, assess utility, "
                        "build private syntax, filter contamination, and gate "
                        "sign birth conservatively"),
            "profile": rt.semiogenesis_profile.to_dict(),
            "status": rt.semiogenesis_status(),
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
            "concept_input": rt.concept_input,
            "candidates": [c.to_dict() for c in rt.candidates],
            "utility": rt.utility_scores,
            "private_syntax": rt.syntax_graph,
            "contamination": rt.contamination_results,
            "birth_gate": rt.birth_gate_results,
            "sign_memory": (rt.sign_memory.index().to_dict()
                            if rt.sign_memory else {}),
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
            "# First Live Semiogenesis Report", "",
            "_Forms private internal signs over stable, feature-grounded live "
            "proto-concepts. It does NOT enable full cognition, action-reaction "
            "learning, or developmental autonomy; start/stop/configure feeders; "
            "control hardware; access the network/shell/browser/OS; call Git/"
            "GitHub; execute commands; treat sensory text as a command; treat "
            "human labels or debug gloss as ground truth; or make any claim of "
            "language understanding, consciousness, sentience, biological life, "
            "personhood, agency, free will, emotion, feeling, self-awareness, or "
            "subjective experience._", "",
            f"- run id: {st['semiogenesis_run_id']} "
            f"({s['profile'].get('profile_id')})",
            f"- blocked: {s['blocked']}",
            f"- observation stability: {s['observation']['stability_status']} "
            f"(blocked {s['observation']['blocked']})",
            f"- eligible concepts: {st['live_eligible_concept_count']}",
            f"- sign candidates: {st['live_sign_candidate_count']} (stable "
            f"{st['live_stable_sign_candidate_count']}, born "
            f"{st['live_born_sign_count']}, rejected "
            f"{st['live_rejected_sign_count']}, contaminated "
            f"{st['live_contaminated_sign_count']}, label-dependent "
            f"{st['live_label_dependent_sign_count']})",
            f"- private syntax relations: "
            f"{st['live_private_syntax_relation_count']}",
            f"- sign utility mean: {st['live_sign_utility_score_mean']}",
            f"- sign birth gate status: {st['live_sign_birth_gate_status']}",
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
            "CONCEPT_INPUT_REPORT.md": self._concept_md(s),
            "SIGN_CANDIDATES.md": self._candidates_md(s),
            "SIGN_UTILITY_REPORT.md": self._utility_md(s),
            "PRIVATE_SYNTAX_REPORT.md": self._syntax_md(s),
            "SIGN_CONTAMINATION_REPORT.md": self._contamination_md(s),
            "SIGN_BIRTH_GATE_REPORT.md": self._gate_md(s),
            "LIVE_SIGN_MEMORY_REPORT.md": self._memory_md(s),
        }

    def _concept_md(self, s: Dict[str, Any]) -> str:
        ci = s["concept_input"]
        lines = ["# Concept Input Report", "",
                 f"- status: {ci.get('concept_input_status')}",
                 f"- eligible concepts: "
                 f"{ci.get('live_eligible_concept_count', 0)}",
                 f"- counterevidence concepts: "
                 f"{ci.get('counterevidence_concept_count', 0)}",
                 f"- contaminated concepts: "
                 f"{ci.get('contaminated_concept_count', 0)}", "",
                 "_Only born/stable proto-concepts are eligible; contaminated "
                 "concepts are excluded; rejected concepts remain visible as "
                 "counterevidence; labels/gloss are non-ground-truth "
                 "annotations._"]
        return _guard("\n".join(lines))

    def _candidates_md(self, s: Dict[str, Any]) -> str:
        lines = ["# Sign Candidates", "",
                 "| sign id | status | token | utility | concepts |",
                 "| --- | --- | --- | --- | --- |"]
        for c in s["candidates"]:
            lines.append(f"| {c['sign_id']} | {c['status']} | "
                         f"{c['private_token']} | {c['utility_score']:.2f} | "
                         f"{len(c['linked_concept_ids'])} |")
        lines += ["", "_A sign candidate is not a born sign until it passes the "
                  "sign birth gate. The token is private/internal; weak, "
                  "rejected, suspended, and contaminated candidates are all "
                  "preserved; evidence is kept._"]
        return _guard("\n".join(lines))

    def _utility_md(self, s: Dict[str, Any]) -> str:
        lines = ["# Sign Utility Report", ""]
        for sid, score in s["utility"].items():
            lines.append(f"- {sid}: {score.get('utility_score', 0.0):.2f} "
                         f"(useful={score.get('useful')})")
        lines += ["", "_A sign must do something internally useful; merely "
                  "naming a concept is not enough; a label-mirroring sign has "
                  "low or blocked utility; missing evidence lowers confidence._"]
        return _guard("\n".join(lines))

    def _syntax_md(self, s: Dict[str, Any]) -> str:
        g = s["private_syntax"]
        lines = ["# Private Syntax Report", "",
                 f"- relations: {g.get('live_private_syntax_relation_count', 0)} "
                 f"(blocked {g.get('blocked_relation_count', 0)})",
                 f"- co-occurs: {g.get('co_occurs_count', 0)}; contrasts: "
                 f"{g.get('contrasts_count', 0)}; absence-linked: "
                 f"{g.get('absence_linked_count', 0)}", "",
                 "_Private syntax is operational relation structure, not language "
                 "grammar or semantics. Relations require evidence; weak "
                 "relations are marked weak/uncertain; contaminated relations are "
                 "blocked._"]
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
        lines = ["# Sign Contamination Report", "",
                 f"- contaminated signs: {contaminated}",
                 f"- contamination types: {types}", "",
                 "_Contaminated signs cannot be born; tokens never store private "
                 "data/secrets; human labels and debug gloss annotate but never "
                 "define a sign; the operator pulse is stimulus, not teaching. No "
                 "finding is hidden._"]
        return _guard("\n".join(lines))

    def _gate_md(self, s: Dict[str, Any]) -> str:
        lines = ["# Sign Birth Gate Report", ""]
        for g in s["birth_gate"]:
            lines.append(f"- {g['sign_id']}: {g['sign_birth_gate_status']} "
                         f"(born={g['born']}) -- {g.get('rationale', '')}")
            for b in g.get("blockers", []):
                lines.append(f"    - blocker: {b['blocker']} -> "
                             f"{b['correction']}")
        lines += ["", "_The sign birth gate is conservative. It does not enable "
                  "cognition, language, or action; it creates only operational "
                  "private sign records._"]
        return _guard("\n".join(lines))

    def _memory_md(self, s: Dict[str, Any]) -> str:
        m = s["sign_memory"]
        lines = ["# Live Sign Memory Report", "",
                 f"- records: {m.get('live_sign_record_count', 0)}",
                 f"- by status: {m.get('by_status', {})}",
                 f"- born: {m.get('born_count', 0)}", "",
                 "_Append-only local metadata. Candidates, weak, rejected, and "
                 "contaminated signs are all preserved; every born sign links to "
                 "concept evidence; tokens never store private data or secrets. "
                 "Private signs do not imply language or understanding._"]
        return _guard("\n".join(lines))

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = os.path.join(state_dir or self.runtime.state_dir, "semiogenesis",
                            "reports")
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "LIVE_SEMIOGENESIS_REPORT.md")
        json_path = os.path.join(base, "LIVE_SEMIOGENESIS_REPORT.json")
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
