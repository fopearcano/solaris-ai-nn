"""Live ontogenesis reports -- features, recurrence, candidates, gate, memory.

:class:`LiveOntogenesisReportBuilder` writes the ontogenesis report set. Every report
states explicitly that no feeder was started/stopped/controlled, no hardware was
controlled, no network/Git/GitHub/shell/browser/OS access occurred, no commands were
executed, no sensory text was treated as a command, no human label or debug gloss was
treated as ground truth, no semiogenesis was enabled by default, no action-reaction
or autonomous development was enabled by default, and no consciousness/life/agency
claim is made. ClaimGuard scans the Markdown when available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_WHAT_THIS_DOES_NOT_DO = (
    "No feeder was started, stopped, or controlled.",
    "No hardware was controlled.",
    "No network/Git/GitHub/shell/browser/OS access occurred.",
    "No commands were executed.",
    "No sensory text was treated as a command.",
    "No human label or debug gloss was treated as ground truth.",
    "No semiogenesis was enabled by default.",
    "No action-reaction or autonomous development was enabled by default.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class LiveOntogenesisReportBuilder:
    """Builds the live ontogenesis report set (Markdown + JSON)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        sections = {
            "purpose": ("form conservative proto-concept candidates from "
                        "validated live read-only feature recurrence after birth "
                        "and observation stability; gate concept birth by "
                        "recurrence, stability, source diet, contamination, and "
                        "safety"),
            "profile": rt.ontogenesis_profile.to_dict(),
            "status": rt.ontogenesis_status(),
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
            "feature_extraction": rt.feature_result,
            "recurrence": rt.recurrence_summary,
            "candidates": [c.to_dict() for c in rt.candidates],
            "stability": rt.stability_scores,
            "contamination": rt.contamination_results,
            "birth_gate": rt.birth_gate_results,
            "concept_memory": (rt.concept_memory.index().to_dict()
                               if rt.concept_memory else {}),
            "recommended_next_phase": rt.recommended_next_phase(),
            "blocked": rt.blocked,
            "blockers": list(rt.blockers),
            "warnings": list(rt.warnings),
            "safety_status": rt.safety.snapshot(),
            "what_this_does_not_do": list(_WHAT_THIS_DOES_NOT_DO),
        }
        markdown = self._render_main(sections)
        return {"sections": sections, "claim_guard_safe": _safe(markdown)}

    def _render_main(self, s: Dict[str, Any]) -> str:
        st = s["status"]
        lines = [
            "# First Live Ontogenesis Report", "",
            "_Forms conservative proto-concept candidates from validated, local, "
            "live read-only feature recurrence. It does NOT enable semiogenesis, "
            "action-reaction learning, or developmental autonomy; start/stop/"
            "configure feeders; control hardware; access the network/shell/"
            "browser/OS; call Git/GitHub; execute commands; treat sensory text as "
            "a command; treat human labels or debug gloss as ground truth; or "
            "make any claim of consciousness, sentience, biological life, "
            "personhood, agency, free will, emotion, feeling, understanding, "
            "self-awareness, or subjective experience._", "",
            f"- run id: {st['ontogenesis_run_id']} "
            f"({s['profile'].get('profile_id')})",
            f"- blocked: {s['blocked']}",
            f"- observation stability: {s['observation']['stability_status']} "
            f"(blocked {s['observation']['blocked']})",
            f"- feature vectors: {st['live_feature_vector_count']}; recurrence "
            f"patterns: {st['live_recurrence_pattern_count']}",
            f"- candidates: {st['live_candidate_count']} (stable "
            f"{st['live_stable_candidate_count']}, born "
            f"{st['live_born_proto_concept_count']}, rejected "
            f"{st['live_rejected_candidate_count']}, contaminated "
            f"{st['live_contaminated_candidate_count']}, source-artifact "
            f"{st['live_source_artifact_candidate_count']})",
            f"- birth gate status: {st['live_birth_gate_status']}",
            f"- recommended next phase: {st['recommended_next_phase']}",
            "",
        ]
        if s["blockers"]:
            lines += ["## Blockers", ""]
            lines += [f"- {b}" for b in s["blockers"]]
            lines.append("")
        if s["warnings"]:
            lines += ["## Warnings", ""]
            lines += [f"- {w}" for w in s["warnings"]]
            lines.append("")
        lines += ["## Recommended next phase (not executed)", "",
                  f"- {s['recommended_next_phase']}", "",
                  "## Limitations", ""]
        lines += [f"- {l}" for l in s["profile"].get("limitations", [])]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in s["what_this_does_not_do"]]
        return "\n".join(lines)

    def _sub_reports(self, s: Dict[str, Any]) -> Dict[str, str]:
        return {
            "FEATURE_EXTRACTION_REPORT.md": self._feature_md(s),
            "RECURRENCE_REPORT.md": self._recurrence_md(s),
            "PROTO_CONCEPT_CANDIDATES.md": self._candidates_md(s),
            "STABILITY_SCORING_REPORT.md": self._stability_md(s),
            "CONTAMINATION_REPORT.md": self._contamination_md(s),
            "CONCEPT_BIRTH_GATE_REPORT.md": self._gate_md(s),
            "LIVE_CONCEPT_MEMORY_REPORT.md": self._memory_md(s),
        }

    def _feature_md(self, s: Dict[str, Any]) -> str:
        fe = s["feature_extraction"]
        lines = ["# Feature Extraction Report", "",
                 f"- feature vectors: {fe.get('live_feature_vector_count', 0)}",
                 f"- by source: {fe.get('by_source', {})}",
                 f"- by modality: {fe.get('by_modality', {})}",
                 f"- skipped (private/secret): {fe.get('skipped_count', 0)}", "",
                 "_Debug gloss is stored only as a non-ground-truth annotation; "
                 "human text is represented structurally, not semantically; the "
                 "operator pulse must not dominate; raw private/secret events are "
                 "never extracted._"]
        return _guard("\n".join(lines))

    def _recurrence_md(self, s: Dict[str, Any]) -> str:
        r = s["recurrence"]
        lines = ["# Recurrence Report", "",
                 f"- recurrence patterns: "
                 f"{r.get('live_recurrence_pattern_count', 0)} "
                 f"(strong {r.get('strong_pattern_count', 0)}, moderate "
                 f"{r.get('moderate_pattern_count', 0)}, weak "
                 f"{r.get('weak_pattern_count', 0)}, unstable "
                 f"{r.get('unstable_pattern_count', 0)})", "",
                 "_Recurrence requires multiple observations; a single event "
                 "cannot birth a concept; operator-pulse-only recurrence is "
                 "insufficient; human-text-only recurrence is a contamination "
                 "risk._"]
        return _guard("\n".join(lines))

    def _candidates_md(self, s: Dict[str, Any]) -> str:
        lines = ["# Proto-Concept Candidates", "",
                 "| candidate | status | recurrence | stability | sources |",
                 "| --- | --- | --- | --- | --- |"]
        for c in s["candidates"]:
            lines.append(f"| {c['candidate_id']} | {c['status']} | "
                         f"{c['recurrence_count']} | "
                         f"{c['stability_score']:.2f} | {c['source_count']} |")
        lines += ["", "_A candidate is not a concept until it passes the birth "
                  "gate. Weak, rejected, suspended, and contaminated candidates "
                  "are all preserved; supporting and contradicting evidence are "
                  "kept._"]
        return _guard("\n".join(lines))

    def _stability_md(self, s: Dict[str, Any]) -> str:
        lines = ["# Stability Scoring Report", ""]
        for cid, score in s["stability"].items():
            lines.append(f"- {cid}: {score.get('stability_score', 0.0):.2f} "
                         f"(stable={score.get('is_stable')})")
        lines += ["", "_Scoring is conservative: high recurrence from one noisy "
                  "source or from operator text is not enough; missing or "
                  "contradictory evidence lowers confidence._"]
        return _guard("\n".join(lines))

    def _contamination_md(self, s: Dict[str, Any]) -> str:
        types: Dict[str, int] = {}
        contaminated = 0
        for r in s["contamination"]:
            if r.get("contaminated"):
                contaminated += 1
            for f in r.get("findings", []):
                ct = f.get("contamination_type")
                types[ct] = types.get(ct, 0) + 1
        lines = ["# Contamination Report", "",
                 f"- contaminated candidates: {contaminated}",
                 f"- contamination types: {types}", "",
                 "_Contaminated candidates cannot be born; source artifacts may "
                 "persist only if marked as such; human labels and debug gloss "
                 "annotate but never define; the operator pulse is stimulus, not "
                 "teaching. No finding is hidden._"]
        return _guard("\n".join(lines))

    def _gate_md(self, s: Dict[str, Any]) -> str:
        lines = ["# Concept Birth Gate Report", ""]
        for g in s["birth_gate"]:
            lines.append(f"- {g['candidate_id']}: "
                         f"{g['concept_birth_gate_status']} "
                         f"(born={g['born']}) -- {g.get('rationale', '')}")
            for b in g.get("blockers", []):
                lines.append(f"    - blocker: {b['blocker']} -> "
                             f"{b['correction']}")
        lines += ["", "_The birth gate is conservative. It does not enable "
                  "semiogenesis, create language, or claim understanding; it "
                  "creates only operational proto-concept records._"]
        return _guard("\n".join(lines))

    def _memory_md(self, s: Dict[str, Any]) -> str:
        m = s["concept_memory"]
        lines = ["# Live Concept Memory Report", "",
                 f"- records: {m.get('live_concept_record_count', 0)}",
                 f"- by status: {m.get('by_status', {})}",
                 f"- born: {m.get('born_count', 0)}", "",
                 "_Append-only local metadata. Candidates, weak, rejected, and "
                 "contaminated records are all preserved; every record links to "
                 "evidence. Proto-concepts do not imply understanding._"]
        return _guard("\n".join(lines))

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = os.path.join(state_dir or self.runtime.state_dir, "ontogenesis",
                            "reports")
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "LIVE_ONTOGENESIS_REPORT.md")
        json_path = os.path.join(base, "LIVE_ONTOGENESIS_REPORT.json")
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
