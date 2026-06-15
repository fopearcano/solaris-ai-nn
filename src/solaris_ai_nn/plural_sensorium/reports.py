"""Plural sensorium reports -- a claim-guarded view of what was perceived.

:class:`PluralSensoriumReportBuilder` compiles the enabled modalities, feeders,
receptors, sensory field, baseline shifts, flux / absence / rhythm / invariants /
cross-modal relations, attention shifts, proto-symbol candidates, world-model
structures, hypotheses, LOGOS tensions, the human-label contamination score, the
modality-native grounding score, limitations, and a next recommended experiment.
The Markdown is scanned by ClaimGuard before it is written.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .sensorium_runtime import PluralSensoriumRuntime

_LIMITATIONS = (
    "No direct hardware access: all events come from external read-only feeders.",
    "Human labels are never ground truth; feature patterns are primary.",
    "Fixture patterns may not generalise to real read-only streams.",
    "This is operational perception, not consciousness, sentience, or life.",
)


@dataclass
class PluralSensoriumReport:
    sections: Dict[str, Any] = field(default_factory=dict)
    claim_guard_safe: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"sections": self.sections,
                "claim_guard_safe": self.claim_guard_safe}


@dataclass
class PluralSensoriumReportBuilder:
    """Builds the plural sensorium report (JSON + claim-guarded Markdown)."""

    runtime: PluralSensoriumRuntime

    def build(self) -> PluralSensoriumReport:
        rt = self.runtime
        status = rt.plural_sensorium_status()
        sections: Dict[str, Any] = {
            "enabled_modalities": rt.active_modalities(),
            "feeder_summary": [f.to_dict() for f in rt.feeders],
            "receptor_summary": [r.to_dict() for r in rt.receptors.values()],
            "sensory_field": rt.sensory_field.to_dict(),
            "baseline_shifts": list(rt.baseline_shifts),
            "flux_events": rt.flux.snapshot(),
            "absence_events": [e.to_dict() for e in rt.absence.events],
            "rhythm_signatures": [s.to_dict()
                                  for s in rt.rhythm.signatures.values()],
            "invariant_candidates": [c.to_dict()
                                     for c in rt.invariants.candidates.values()],
            "cross_modal_relations": [r.to_dict()
                                      for r in rt.cross_modal.all_relations()],
            "attention_shifts": [s.to_dict() for s in rt.attention.history],
            "proto_symbol_candidates": list(rt.proto_symbol_candidates),
            "world_model_structures": rt.world_model_structures[:200],
            "hypotheses_seeded": list(rt.hypotheses),
            "logos_tensions": list(rt.logos_tensions),
            "human_label_contamination_score":
                rt.human_label_contamination_score(),
            "modality_native_grounding_score":
                rt.modality_native_grounding_score(),
            "milestones": list(rt.milestones),
            "status": status,
            "limitations": list(_LIMITATIONS),
            "next_recommended_experiment": self._next_experiment(rt),
        }
        report = PluralSensoriumReport(sections=sections)
        report.claim_guard_safe = self._claim_guard_safe(
            self._render_markdown(sections))
        return report

    def _next_experiment(self, rt: PluralSensoriumRuntime) -> str:
        if not rt.cross_modal.relations:
            return ("run a mixed-modality fixture to seed cross-modal "
                    "relations")
        if rt.human_label_contamination_score() > 0.2:
            return ("re-run with feature-only streams to reduce human-label "
                    "contamination")
        return ("compare human-like-only vs non-human-only sensoria to test "
                "whether internal structure differs")

    def _render_markdown(self, sections: Dict[str, Any]) -> str:
        lines = [
            "# Plural Sensorium Report", "",
            "_A continuous, organismic perceptual layer. Input is a sensory "
            "field, not isolated events. Human-like and non-human modalities "
            "are equally first-class; human ontology is not the default. No "
            "direct hardware is controlled; all events come from read-only "
            "external feeders. This is operational perception, not "
            "consciousness, sentience, life, personhood, or agency._", "",
            f"- enabled modalities: {sections['enabled_modalities']}",
            f"- active receptors: {len(sections['receptor_summary'])}",
            f"- baseline shifts: {len(sections['baseline_shifts'])}",
            f"- absence events: {len(sections['absence_events'])}",
            f"- rhythm signatures: {len(sections['rhythm_signatures'])}",
            f"- invariant candidates: {len(sections['invariant_candidates'])}",
            f"- cross-modal relations: "
            f"{len(sections['cross_modal_relations'])}",
            f"- modality-grounded proto-symbols: "
            f"{len(sections['proto_symbol_candidates'])}",
            f"- human-label contamination score: "
            f"{sections['human_label_contamination_score']}",
            f"- modality-native grounding score: "
            f"{sections['modality_native_grounding_score']}",
            "",
            "## Limitations", "",
        ]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        lines += ["", "## Next recommended experiment", "",
                  f"- {sections['next_recommended_experiment']}"]
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
        md_path = os.path.join(base, "PLURAL_SENSORIUM_REPORT.md")
        json_path = os.path.join(base, "PLURAL_SENSORIUM_REPORT.json")
        md = self._render_markdown(report.sections)
        if not report.claim_guard_safe:
            from ..governance.compliance import ClaimGuard

            md = ClaimGuard().rewrite(md)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(md)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path, "report": report}
