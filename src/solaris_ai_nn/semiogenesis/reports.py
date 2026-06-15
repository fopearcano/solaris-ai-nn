"""Semiogenesis report -- internal sign formation made visible and honest.

:class:`SemiogenesisReportBuilder` compiles the internal signs, sign families,
private syntax, internal utterances, utility, drift, contamination, and
human-readable glosses. It states explicitly that signs are operational markers
(not words), that private syntax is internal relation structure (not human
grammar), that gloss is approximate/debug-only, and that it proves no language
understanding / consciousness / sentience / life / subjective experience. The
Markdown is scanned by ClaimGuard.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .signs import SignKind, SignStatus

_DOES_NOT_PROVE = (
    "Signs are operational markers, not human words.",
    "Private syntax is internal relation structure, not human grammar.",
    "Human-readable gloss is approximate and debug-only, never ground truth.",
    "This does not prove language understanding.",
    "This does not prove consciousness.",
    "This does not prove sentience.",
    "This does not prove life.",
    "This does not prove subjective experience.",
)

_LIMITATIONS = (
    "Signs are sensorium-native markers; they are not human words by default.",
    "No LLM and no human language generation is used to form signs.",
    "Useful does not mean true, and stable does not mean understood.",
    "Rejected, failed, and ambiguous signs are preserved, not deleted.",
    "Human gloss is an approximate debug annotation, never the internal sign.",
)


@dataclass
class SemiogenesisReportBuilder:
    """Builds the semiogenesis report (JSON + claim-guarded Markdown)."""

    runtime: Any

    def _signs_by(self, *statuses: str) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self.runtime.signs.values()
                if s.status in statuses]

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.semiogenesis_status()
        ont = rt.ontogenesis
        signs = list(rt.signs.values())
        sections: Dict[str, Any] = {
            "purpose": ("describe how internal signs form from sensorium-native "
                        "proto-concepts -- operational markers, not human words"),
            "input_proto_concepts": (
                ont.ontogenesis_status()
                if ont is not None and hasattr(ont, "ontogenesis_status")
                else {}),
            "internal_sign_candidates": self._signs_by(
                SignStatus.CANDIDATE, SignStatus.EMERGING),
            "stable_signs": self._signs_by(SignStatus.STABLE),
            "ambiguous_decaying_rejected_signs": self._signs_by(
                SignStatus.AMBIGUOUS, SignStatus.DECAYING,
                SignStatus.REJECTED),
            "sign_families": rt.family_builder.to_dict(),
            "private_syntax_patterns": rt.syntax_builder.to_dict(),
            "internal_utterances": rt.utterance_builder.to_dict(),
            "sign_utility_means": {
                "compression": status["sign_compression_utility_mean"],
                "prediction": status["sign_prediction_utility_mean"],
                "attention": status["sign_attention_utility_mean"],
            },
            "sign_drift": list(rt.drift_results),
            "contamination": {
                "contaminated_sign_count": status["contaminated_sign_count"],
                "contaminated_sign_ratio": status["contaminated_sign_ratio"],
                "gloss_dependence_score": status["gloss_dependence_score"],
            },
            "human_readable_glosses": [
                {"sign_code": s.sign_code, "gloss": s.human_gloss,
                 "gloss_status": s.human_gloss_status}
                for s in signs if s.human_gloss],
            "modality_native_signs": [s.to_dict() for s in signs
                                      if s.kind == SignKind.MODALITY_NATIVE],
            "cross_modal_signs": [s.to_dict() for s in signs
                                  if s.is_cross_modal],
            "absence_signs": [s.to_dict() for s in signs if s.is_absence],
            "logos_tension_signs": [s.to_dict() for s in signs
                                    if s.kind == SignKind.LOGOS_TENSION],
            "negative_results": self._signs_by(SignStatus.REJECTED,
                                               SignStatus.AMBIGUOUS),
            "latent_replay_recommendations":
                rt.latent_replay_recommendations(),
            "milestones": list(rt.milestones),
            "safety_status": rt.safety.snapshot(),
            "status": status,
            "limitations": list(_LIMITATIONS),
            "what_this_does_not_prove": list(_DOES_NOT_PROVE),
        }
        markdown = self._render_markdown(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _render_markdown(self, sections: Dict[str, Any]) -> str:
        status = sections["status"]
        lines = [
            "# Semiogenesis Report", "",
            "_How internal signs form from sensorium-native proto-concepts. "
            "Signs are operational markers (compression / prediction / attention "
            "/ relation), NOT human words; private syntax is internal "
            "sign-relation structure, NOT human grammar; any human-readable "
            "gloss is an approximate debug annotation, never ground truth and "
            "never the internal sign. No LLM and no human-language generation is "
            "used._", "",
            f"- internal signs: {status['internal_sign_count']} "
            f"(stable {status['stable_sign_count']}, "
            f"ambiguous {status['ambiguous_sign_count']}, "
            f"decaying {status['decaying_sign_count']})",
            f"- sign families: {status['sign_family_count']} "
            f"(dominant {status['dominant_sign_family']})",
            f"- private syntax patterns: "
            f"{status['private_syntax_pattern_count']}",
            f"- internal utterances: {status['internal_utterance_count']}",
            f"- modality-native ratio: "
            f"{status['modality_native_sign_ratio']}",
            f"- cross-modal ratio: {status['cross_modal_sign_ratio']}",
            f"- absence ratio: {status['absence_sign_ratio']}",
            f"- contaminated signs: {status['contaminated_sign_count']} "
            f"(ratio {status['contaminated_sign_ratio']})",
            f"- gloss dependence: {status['gloss_dependence_score']}",
            f"- sign drift events: {status['sign_drift_count']}",
            f"- sign explosion warnings: "
            f"{status['sign_explosion_warning_count']}",
            "",
            "## Negative / failed / ambiguous signs (preserved)", "",
            f"- preserved: {len(sections['negative_results'])} "
            "(decay/rejection is recorded as new state, never deleted)",
            "",
            "## What this does NOT prove", "",
        ]
        lines += [f"- {item}" for item in sections["what_this_does_not_prove"]]
        lines += ["", "## Limitations", ""]
        lines += [f"- {lim}" for lim in sections["limitations"]]
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
        base = state_dir or self.runtime.state_dir
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "SEMIOGENESIS_REPORT.md")
        json_path = os.path.join(base, "SEMIOGENESIS_REPORT.json")
        markdown = self._render_markdown(report["sections"])
        if not report["claim_guard_safe"]:
            from ..governance.compliance import ClaimGuard

            markdown = ClaimGuard().rewrite(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path, "report": report}
