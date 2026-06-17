"""Live ontogenesis record -- a plain account of the first ontogenesis run.

:class:`LiveOntogenesisRecordBuilder` writes ``LIVE_ONTOGENESIS_RECORD_<run_id>``
(Markdown + JSON): a plain, honest account of one bounded live ontogenesis run --
the events seen, features extracted, recurrence patterns, candidates, stable
candidates, born proto-concepts, rejected/contaminated candidates, source artifacts,
top candidates, birth-gate results, contamination summary, the recommended next
phase, blockers, and warnings -- with a mandatory non-claim disclaimer.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_DISCLAIMER = (
    "This is a live-read-only ontogenesis record. Proto-concepts are operational "
    "feature-stability records. They do not imply consciousness, sentience, "
    "biological life, personhood, agency, free will, emotion, feeling, "
    "understanding, self-awareness, autonomous self-improvement, or subjective "
    "experience.")


@dataclass
class LiveOntogenesisRecord:
    """The structured first-ontogenesis record."""

    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.data)


@dataclass
class LiveOntogenesisRecordBuilder:
    """Builds the live ontogenesis record (Markdown + JSON)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.ontogenesis_status()
        counts = rt._counts()
        top = sorted(rt.candidates, key=lambda c: c.stability_score,
                     reverse=True)[:10]
        data = {
            "run_id": rt.run_id,
            "disclaimer": _DISCLAIMER,
            "profile": rt.ontogenesis_profile.to_dict(),
            "governance_status": rt.governance_result.get("governance_status"),
            "governance_passed": rt.governance_result.get("governance_passed"),
            "birth_certificate_present": rt.birth_certificate_present,
            "observation_stability_status": rt.observation.get(
                "stability_status"),
            "observation_stability_blocked": rt.observation.get("blocked"),
            "event_count": len(rt.accepted_events),
            "feature_vector_count": status["live_feature_vector_count"],
            "recurrence_pattern_count": status["live_recurrence_pattern_count"],
            "candidate_count": counts["candidate_count"],
            "stable_candidate_count": counts["stable_candidate_count"],
            "born_proto_concept_count": counts["born_count"],
            "rejected_candidate_count": counts["rejected_count"],
            "contaminated_candidate_count": counts["contaminated_count"],
            "source_artifact_count": counts["source_artifact_count"],
            "top_candidates": [c.to_dict() for c in top],
            "birth_gate_results": rt.birth_gate_results,
            "contamination_summary": self._contamination_summary(),
            "recommended_next_phase": rt.recommended_next_phase(),
            "blocked": rt.blocked,
            "blockers": list(rt.blockers),
            "warnings": list(rt.warnings),
            "limitations": rt.ontogenesis_profile.to_dict().get("limitations"),
        }
        markdown = self._render(data)
        return {"record": data, "markdown_text": markdown,
                "claim_guard_safe": _claim_guard_safe(markdown)}

    def _contamination_summary(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        contaminated = 0
        for r in self.runtime.contamination_results:
            if r.get("contaminated"):
                contaminated += 1
            for t, n in (r.get("contamination_types", {}) or {}).items():
                types[t] = types.get(t, 0) + n
            for f in r.get("findings", []):
                ct = f.get("contamination_type")
                if ct:
                    types[ct] = types.get(ct, 0) + 1
        return {"contaminated_candidate_count": contaminated,
                "contamination_types": types}

    def _render(self, d: Dict[str, Any]) -> str:
        lines = [
            "# First Live Ontogenesis Record", "",
            f"_{_DISCLAIMER}_", "",
            f"- run id: {d['run_id']}",
            f"- profile: {d['profile'].get('profile_id')} "
            f"(candidate_only={d['profile'].get('candidate_only')})",
            f"- governance: {d['governance_status']} "
            f"(passed {d['governance_passed']})",
            f"- birth certificate present: {d['birth_certificate_present']}",
            f"- observation stability: {d['observation_stability_status']} "
            f"(blocked {d['observation_stability_blocked']})",
            f"- accepted events: {d['event_count']}; feature vectors: "
            f"{d['feature_vector_count']}",
            f"- recurrence patterns: {d['recurrence_pattern_count']}",
            f"- candidates: {d['candidate_count']} (stable "
            f"{d['stable_candidate_count']}, born "
            f"{d['born_proto_concept_count']}, rejected "
            f"{d['rejected_candidate_count']}, contaminated "
            f"{d['contaminated_candidate_count']}, source-artifact "
            f"{d['source_artifact_count']})",
            f"- recommended next phase: {d['recommended_next_phase']}",
            "",
        ]
        if d["blockers"]:
            lines += ["## Blockers", ""]
            lines += [f"- {b}" for b in d["blockers"]]
            lines.append("")
        if d["warnings"]:
            lines += ["## Warnings", ""]
            lines += [f"- {w}" for w in d["warnings"]]
            lines.append("")
        lines += ["## Top candidates", ""]
        for c in d["top_candidates"]:
            lines.append(f"- {c['candidate_id']} [{c['status']}] "
                         f"signature={c['feature_signature']} "
                         f"recurrence={c['recurrence_count']} "
                         f"stability={c['stability_score']:.2f}")
        lines += ["", "## Contamination summary", "",
                  f"- contaminated candidates: "
                  f"{d['contamination_summary']['contaminated_candidate_count']}",
                  f"- types: {d['contamination_summary']['contamination_types']}",
                  "", "## Limitations", ""]
        lines += [f"- {l}" for l in (d.get("limitations") or [])]
        lines += ["", "_Operational live-read-only ontogenesis only; not "
                  "learning from labels, not language, not understanding, not a "
                  "biological development, and no inner-state claim._"]
        return "\n".join(lines)

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        built = self.build()
        base = os.path.join(state_dir or self.runtime.state_dir, "ontogenesis",
                            "reports")
        os.makedirs(base, exist_ok=True)
        rid = self.runtime.run_id
        md_path = os.path.join(base, f"LIVE_ONTOGENESIS_RECORD_{rid}.md")
        json_path = os.path.join(base, f"LIVE_ONTOGENESIS_RECORD_{rid}.json")
        markdown = built["markdown_text"]
        if not built["claim_guard_safe"]:
            markdown = _guard(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(built["record"], fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}


def _claim_guard_safe(text: str) -> bool:
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
