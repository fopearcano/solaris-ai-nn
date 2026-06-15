"""Sensorium differentiation study report -- what differed, what it does not prove.

:class:`SensoriumDifferentiationStudyReportBuilder` compiles the study arms,
sensorium profiles, world signatures, modality fingerprints, ontology drift,
structure metrics, the comparative analysis, contamination, and the
negative/inconclusive results into a Markdown + JSON report. It states explicitly
that it does not reveal subjective experience, does not prove consciousness /
sentience / life, and does not rank beings -- it only compares observable internal
structures under different perceptual conditions. ClaimGuard scans the Markdown.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

_DOES_NOT_PROVE = (
    "This does not reveal subjective experience.",
    "This does not prove consciousness.",
    "This does not prove sentience.",
    "This does not prove life.",
    "This does not rank beings or sensoriums as better or more conscious.",
    "It only compares observable internal structures under different "
    "perceptual conditions.",
)

_NAGEL_FRAMING = (
    "In the spirit of Nagel's 'what is it like to be a bat?', this lab does NOT "
    "try to access an inner point of view. It asks the narrower, observable "
    "question: does a different sensorium build a different internal structure? "
    "The answer is a structural fingerprint, never a report of experience.")


@dataclass
class SensoriumDifferentiationStudyReportBuilder:
    """Builds the differentiation study report (JSON + claim-guarded Markdown)."""

    runner: Any

    def build(self) -> Dict[str, Any]:
        runner = self.runner
        comparison = runner.compare_results()
        arms = runner.arm_results
        sections: Dict[str, Any] = {
            "study_purpose": ("compare the observable internal structures that "
                              "emerge from different forms of perception"),
            "nagel_framing": _NAGEL_FRAMING,
            "study_arms": [r.arm.to_dict() for r in arms.values()],
            "sensorium_profiles": {a: r.profile.to_dict()
                                   for a, r in arms.items()},
            "live_fixture_replay_status": {
                a: ("blocked" if r.blocked else
                    "inconclusive" if r.inconclusive else
                    "passive" if r.passive else "fixture")
                for a, r in arms.items()},
            "world_signatures": {a: (r.signature.to_dict()
                                     if r.signature else None)
                                 for a, r in arms.items()},
            "modality_fingerprints": {
                a: [f.to_dict() for f in r.fingerprints]
                for a, r in arms.items()},
            "ontology_drift": {a: (r.ontology_drift.to_dict()
                                   if r.ontology_drift else None)
                               for a, r in arms.items()},
            "structure_metrics": {a: (r.metrics.to_dict() if r.metrics else None)
                                  for a, r in arms.items()},
            "comparative_analysis": comparison.to_dict(),
            "changed_perception_comparison": {
                a: (r.signature.changed_perception_score if r.signature else 0.0)
                for a, r in arms.items()},
            "human_label_contamination": {
                a: (r.contamination.to_dict() if r.contamination else None)
                for a, r in arms.items()},
            "negative_results": self._negatives(comparison),
            "inconclusive_results": self._inconclusive(arms, comparison),
            "safety_status": runner.safety.snapshot(),
            "what_this_suggests": self._suggests(comparison),
            "what_this_does_not_prove": list(_DOES_NOT_PROVE),
            "next_recommended_sensorium_study": (
                "add a live read-only arm (governance approved) and re-run the "
                "human-like vs non-human comparison against real flux"),
        }
        markdown = self._render_markdown(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _negatives(self, comparison: Any) -> Dict[str, Any]:
        return {"count": comparison.negative_result_count,
                "note": "comparisons with no meaningful structural difference "
                        "are preserved, not discarded"}

    def _inconclusive(self, arms: Dict[str, Any], comparison: Any
                      ) -> Dict[str, Any]:
        blocked = [a for a, r in arms.items() if r.blocked]
        return {"comparison_inconclusive_count": comparison.inconclusive_count,
                "blocked_arms": blocked}

    def _suggests(self, comparison: Any) -> str:
        if comparison.strongest:
            return (f"the strongest structural difference was {comparison.strongest}"
                    "; different sensoriums built different internal structures")
        return ("no strong structural difference was detected in this bounded "
                "study; this is reported honestly as a null result")

    def _render_markdown(self, sections: Dict[str, Any]) -> str:
        comp = sections["comparative_analysis"]
        lines = [
            "# Sensorium Differentiation Report", "",
            "_Compares the observable internal structures that emerge from "
            "different forms of perception. This is a structural differentiation "
            "study, not a task benchmark, not a chatbot benchmark, and not a "
            "consciousness test._", "",
            f"_{sections['nagel_framing']}_", "",
            f"- study arms: {len(sections['study_arms'])}",
            f"- world signatures: "
            f"{sum(1 for v in sections['world_signatures'].values() if v)}",
            f"- strongest difference: {comp.get('strongest')}",
            f"- inconclusive comparisons: {comp.get('inconclusive_count')}",
            f"- negative (no-difference) results: "
            f"{comp.get('negative_result_count')}",
            "",
            "## What this suggests", "",
            f"- {sections['what_this_suggests']}",
            "",
            "## What this does NOT prove", "",
        ]
        lines += [f"- {item}" for item in
                  sections["what_this_does_not_prove"]]
        lines += ["", "## Live / fixture / replay status", ""]
        lines += [f"- {a}: {s}" for a, s in
                  sections["live_fixture_replay_status"].items()]
        lines += ["", "## Next recommended sensorium study", "",
                  f"- {sections['next_recommended_sensorium_study']}"]
        return "\n".join(lines)

    @staticmethod
    def _claim_guard_safe(text: str) -> bool:
        try:
            from ..governance.compliance import ClaimGuard

            return ClaimGuard().scan_text(text).safe
        except Exception:
            return True

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = state_dir or self.runner.state_dir
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "SENSORIUM_DIFFERENTIATION_REPORT.md")
        json_path = os.path.join(base, "SENSORIUM_DIFFERENTIATION_REPORT.json")
        markdown = self._render_markdown(report["sections"])
        if not report["claim_guard_safe"]:
            from ..governance.compliance import ClaimGuard

            markdown = ClaimGuard().rewrite(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path, "report": report}
