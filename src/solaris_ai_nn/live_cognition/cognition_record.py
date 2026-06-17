"""Live cognition record -- a plain account of the first cognition run.

:class:`LiveCognitionRecordBuilder` writes ``LIVE_COGNITION_RECORD_<run_id>``
(Markdown + JSON): a plain, honest account of one bounded live cognition run -- the
eligible signs, cognition traces, anticipations, internal simulations, prediction
assessment (matched / contradicted), contaminated traces, the readiness gate status,
top traces, blockers, and warnings -- with a mandatory non-claim disclaimer.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

_DISCLAIMER = (
    "This is a live-read-only cognition record. Cognition traces are operational "
    "sign-based anticipation and relation records over private signs and feature-"
    "grounded proto-concepts. They do not imply language understanding, "
    "consciousness, sentience, biological life, personhood, agency, free will, "
    "emotion, feeling, self-awareness, autonomous self-improvement, or subjective "
    "experience.")


@dataclass
class LiveCognitionRecord:
    """The structured first-cognition record."""

    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.data)


@dataclass
class LiveCognitionRecordBuilder:
    """Builds the live cognition record (Markdown + JSON)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.cognition_status()
        counts = rt._counts()
        top = sorted(rt.traces, key=lambda t: t.uncertainty)[:10]
        data = {
            "run_id": rt.run_id,
            "disclaimer": _DISCLAIMER,
            "profile": rt.cognition_profile.to_dict(),
            "governance_status": rt.governance_result.get("governance_status"),
            "governance_passed": rt.governance_result.get("governance_passed"),
            "birth_certificate_present": rt.birth_certificate_present,
            "observation_stability_status": rt.observation.get(
                "stability_status"),
            "observation_stability_blocked": rt.observation.get("blocked"),
            "sign_memory_reference": rt.sign_input.get("sign_memory_path"),
            "eligible_sign_count": len(rt.eligible_signs),
            "cognition_trace_count": counts["trace_count"],
            "anticipation_count": len(rt.anticipations),
            "internal_simulation_count": len(rt.simulations),
            "prediction_assessment_count": int(rt.prediction.get(
                "live_prediction_assessment_count", 0) or 0),
            "matched_prediction_count": int(rt.prediction.get(
                "live_prediction_matched_count", 0) or 0),
            "contradicted_prediction_count": int(rt.prediction.get(
                "live_prediction_contradicted_count", 0) or 0),
            "contaminated_trace_count": counts["contaminated_count"],
            "readiness_gate_status": rt.readiness.get(
                "cognition_readiness_status"),
            "uncertainty_mean": rt._mean_uncertainty(),
            "top_traces": [t.to_dict() for t in top],
            "recommended_next_phase": rt.recommended_next_phase(),
            "blocked": rt.blocked, "blockers": list(rt.blockers),
            "warnings": list(rt.warnings),
            "limitations": rt.cognition_profile.to_dict().get("limitations"),
        }
        markdown = self._render(data)
        return {"record": data, "markdown_text": markdown,
                "claim_guard_safe": _claim_guard_safe(markdown)}

    def _render(self, d: Dict[str, Any]) -> str:
        lines = [
            "# First Live Sensorium-Native Cognition Record", "",
            f"_{_DISCLAIMER}_", "",
            f"- run id: {d['run_id']}",
            f"- profile: {d['profile'].get('profile_id')} "
            f"(trace_only={d['profile'].get('trace_only')})",
            f"- governance: {d['governance_status']} "
            f"(passed {d['governance_passed']})",
            f"- birth certificate present: {d['birth_certificate_present']}",
            f"- observation stability: {d['observation_stability_status']} "
            f"(blocked {d['observation_stability_blocked']})",
            f"- eligible signs: {d['eligible_sign_count']}",
            f"- cognition traces: {d['cognition_trace_count']} (contaminated "
            f"{d['contaminated_trace_count']})",
            f"- anticipations: {d['anticipation_count']}; internal simulations: "
            f"{d['internal_simulation_count']}",
            f"- prediction assessment: {d['prediction_assessment_count']} "
            f"(matched {d['matched_prediction_count']}, contradicted "
            f"{d['contradicted_prediction_count']})",
            f"- mean uncertainty: {d['uncertainty_mean']}",
            f"- readiness gate: {d['readiness_gate_status']}",
            f"- recommended next phase: {d['recommended_next_phase']}",
            "",
        ]
        if d["blockers"]:
            lines += ["## Blockers", ""] + [f"- {b}" for b in d["blockers"]] + [""]
        if d["warnings"]:
            lines += ["## Warnings", ""] + [f"- {w}" for w in d["warnings"]] + [""]
        lines += ["## Top traces (lowest uncertainty)", ""]
        for t in d["top_traces"]:
            lines.append(f"- {t['trace_id']} [{t['status']}] kind={t['kind']} "
                         f"uncertainty={t['uncertainty']:.2f} "
                         f"signs={t['linked_sign_ids']}")
        lines += ["", "## Limitations", ""]
        lines += [f"- {l}" for l in (d.get("limitations") or [])]
        lines += ["", "_Operational live-read-only cognition only; not language, "
                  "not reasoning, not understanding, not consciousness, not "
                  "agency, and no inner-state claim. Prediction failures and "
                  "ambiguity are preserved; no cherry-picking._"]
        return "\n".join(lines)

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        built = self.build()
        base = os.path.join(state_dir or self.runtime.state_dir, "cognition",
                            "reports")
        os.makedirs(base, exist_ok=True)
        rid = self.runtime.run_id
        md_path = os.path.join(base, f"LIVE_COGNITION_RECORD_{rid}.md")
        json_path = os.path.join(base, f"LIVE_COGNITION_RECORD_{rid}.json")
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
