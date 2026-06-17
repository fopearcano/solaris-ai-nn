"""Live semiogenesis record -- a plain account of the first semiogenesis run.

:class:`LiveSemiogenesisRecordBuilder` writes ``LIVE_SEMIOGENESIS_RECORD_<run_id>``
(Markdown + JSON): a plain, honest account of one bounded live semiogenesis run --
the eligible concepts, sign candidates, stable candidates, born signs, rejected /
contaminated / label-dependent signs, private-syntax relations, top signs, birth-gate
results, the contamination summary, the recommended next phase, blockers, and
warnings -- with a mandatory non-claim disclaimer.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

_DISCLAIMER = (
    "This is a live-read-only semiogenesis record. Private signs are operational "
    "internal reference structures over feature-grounded proto-concepts. They do "
    "not imply language understanding, consciousness, sentience, biological life, "
    "personhood, agency, free will, emotion, feeling, self-awareness, autonomous "
    "self-improvement, or subjective experience.")


@dataclass
class LiveSemiogenesisRecord:
    """The structured first-semiogenesis record."""

    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.data)


@dataclass
class LiveSemiogenesisRecordBuilder:
    """Builds the live semiogenesis record (Markdown + JSON)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.semiogenesis_status()
        counts = rt._counts()
        top = sorted(rt.candidates, key=lambda c: c.utility_score,
                     reverse=True)[:10]
        data = {
            "run_id": rt.run_id,
            "disclaimer": _DISCLAIMER,
            "profile": rt.semiogenesis_profile.to_dict(),
            "governance_status": rt.governance_result.get("governance_status"),
            "governance_passed": rt.governance_result.get("governance_passed"),
            "birth_certificate_present": rt.birth_certificate_present,
            "observation_stability_status": rt.observation.get(
                "stability_status"),
            "observation_stability_blocked": rt.observation.get("blocked"),
            "ontogenesis_report_present": rt._ontogenesis_report_present(),
            "concept_memory_path": rt.concept_input.get("concept_memory_path"),
            "eligible_concept_count": len(rt.eligible_concepts),
            "sign_candidate_count": counts["candidate_count"],
            "stable_sign_candidate_count": counts["stable_candidate_count"],
            "born_sign_count": counts["born_count"],
            "rejected_sign_count": counts["rejected_count"],
            "contaminated_sign_count": counts["contaminated_count"],
            "label_dependent_sign_count": counts["label_dependent_count"],
            "private_syntax_relation_count": rt.syntax_graph.get(
                "live_private_syntax_relation_count", 0),
            "top_signs": [c.to_dict() for c in top],
            "birth_gate_results": rt.birth_gate_results,
            "contamination_summary": self._contamination_summary(),
            "recommended_next_phase": rt.recommended_next_phase(),
            "blocked": rt.blocked, "blockers": list(rt.blockers),
            "warnings": list(rt.warnings),
            "limitations": rt.semiogenesis_profile.to_dict().get("limitations"),
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
            for f in r.get("findings", []):
                ct = f.get("contamination_type")
                if ct:
                    types[ct] = types.get(ct, 0) + 1
        return {"contaminated_sign_count": contaminated,
                "contamination_types": types}

    def _render(self, d: Dict[str, Any]) -> str:
        lines = [
            "# First Live Semiogenesis Record", "",
            f"_{_DISCLAIMER}_", "",
            f"- run id: {d['run_id']}",
            f"- profile: {d['profile'].get('profile_id')} "
            f"(candidate_only={d['profile'].get('candidate_only')})",
            f"- governance: {d['governance_status']} "
            f"(passed {d['governance_passed']})",
            f"- birth certificate present: {d['birth_certificate_present']}",
            f"- observation stability: {d['observation_stability_status']} "
            f"(blocked {d['observation_stability_blocked']})",
            f"- ontogenesis report present: {d['ontogenesis_report_present']}",
            f"- eligible concepts: {d['eligible_concept_count']}",
            f"- sign candidates: {d['sign_candidate_count']} (stable "
            f"{d['stable_sign_candidate_count']}, born {d['born_sign_count']}, "
            f"rejected {d['rejected_sign_count']}, contaminated "
            f"{d['contaminated_sign_count']}, label-dependent "
            f"{d['label_dependent_sign_count']})",
            f"- private syntax relations: {d['private_syntax_relation_count']}",
            f"- recommended next phase: {d['recommended_next_phase']}",
            "",
        ]
        if d["blockers"]:
            lines += ["## Blockers", ""] + [f"- {b}" for b in d["blockers"]] + [""]
        if d["warnings"]:
            lines += ["## Warnings", ""] + [f"- {w}" for w in d["warnings"]] + [""]
        lines += ["## Top signs", ""]
        for c in d["top_signs"]:
            lines.append(f"- {c['sign_id']} [{c['status']}] "
                         f"token={c['private_token']} "
                         f"utility={c['utility_score']:.2f} "
                         f"concepts={c['linked_concept_ids']}")
        lines += ["", "## Contamination summary", "",
                  f"- contaminated signs: "
                  f"{d['contamination_summary']['contaminated_sign_count']}",
                  f"- types: {d['contamination_summary']['contamination_types']}",
                  "", "## Limitations", ""]
        lines += [f"- {l}" for l in (d.get("limitations") or [])]
        lines += ["", "_Operational live-read-only semiogenesis only; not "
                  "language, not understanding, not a biological development, and "
                  "no inner-state claim._"]
        return "\n".join(lines)

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        built = self.build()
        base = os.path.join(state_dir or self.runtime.state_dir, "semiogenesis",
                            "reports")
        os.makedirs(base, exist_ok=True)
        rid = self.runtime.run_id
        md_path = os.path.join(base, f"LIVE_SEMIOGENESIS_RECORD_{rid}.md")
        json_path = os.path.join(base, f"LIVE_SEMIOGENESIS_RECORD_{rid}.json")
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
