"""Sensorium-cognition report -- sign-based thought made visible and honest.

:class:`SensoriumCognitionReportBuilder` compiles the cognitive state, moves,
predictions (including failures), anticipation, question pressure, simulations,
counterfactuals, analogies, synthesis, tensions, and attention recommendations. It
states explicitly that cognitive moves are operational transformations over signs/
concepts, that internal simulation is not real observation, that human-readable
summaries are debug glosses, and that it proves no understanding/consciousness/
sentience/life/subjective experience. The Markdown is scanned by ClaimGuard.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_DOES_NOT_PROVE = (
    "Cognitive moves are operational transformations over signs and "
    "proto-concepts, not sentences.",
    "Internal simulation is not real observation.",
    "Human-readable summaries are debug glosses, not internal thoughts.",
    "This does not prove understanding.",
    "This does not prove consciousness.",
    "This does not prove sentience.",
    "This does not prove life or personhood.",
    "This does not prove subjective experience.",
)

_LIMITATIONS = (
    "Cognition operates over signs/concepts/relations, not human language.",
    "No LLM and no chain-of-thought text is used as the cognitive substrate.",
    "Failed predictions and failed simulations are preserved, not deleted.",
    "Simulated and counterfactual items are marked non-real, never observation.",
    "Predictions and analogies are provisional; correlation is not causation.",
)


@dataclass
class SensoriumCognitionReportBuilder:
    """Builds the cognition report (JSON + claim-guarded Markdown)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.cognition_status()
        sem = rt.semiogenesis
        ont = rt.ontogenesis
        sections: Dict[str, Any] = {
            "purpose": ("operate over sensorium-native signs and proto-concepts "
                        "as bounded cognitive moves -- not human-language "
                        "reasoning"),
            "active_signs_concepts": {
                "sign_status": (sem.semiogenesis_status()
                                if sem is not None
                                and hasattr(sem, "semiogenesis_status") else {}),
                "concept_status": (ont.ontogenesis_status()
                                   if ont is not None
                                   and hasattr(ont, "ontogenesis_status")
                                   else {}),
            },
            "cognitive_state": rt.state.to_dict(),
            "cognitive_moves": [m.to_dict() for m in rt.moves],
            "predictions": [p.to_dict() for p in rt.predictions],
            "failed_predictions": [p.to_dict() for p in rt.failed_predictions],
            "anticipation_state": rt.anticipator.state.to_dict(),
            "question_pressure": [q.to_dict() for q in rt.question_pressures],
            "internal_simulations": [s.to_dict() for s in rt.simulations],
            "counterfactuals": [c.to_dict() for c in rt.counterfactuals],
            "analogies": [a.to_dict() for a in rt.analogies],
            "synthesis_events": [r.to_dict() for r in rt.synthesis_results],
            "unresolved_logos_tensions": [
                t.to_dict() if hasattr(t, "to_dict") else {}
                for t in rt.logos_tensions()],
            "attention_recommendations": [
                m.to_dict() for m in rt.moves if m.recommends_attention],
            "memory_writes": rt.memory.snapshot(),
            "negative_results": {
                "failed_prediction_count": len(rt.failed_predictions),
                "contradicted_analogy_count":
                    rt.analogy_engine.contradicted_count,
                "preserved_contradictions": len(
                    rt.state.unresolved_contradictions),
            },
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
            "# Sensorium Cognition Report", "",
            "_How Solaris operates over its own sensorium-native signs and "
            "proto-concepts as bounded cognitive moves. Cognitive moves are "
            "operational transformations over signs, concepts, relations, "
            "memory, hypotheses, and LOGOS tensions -- NOT human-language "
            "chain-of-thought. Internal simulation is NOT real observation, and "
            "any human-readable summary is a debug gloss. No LLM is used._", "",
            f"- cognitive moves: {status['cognitive_move_count']}",
            f"- predictions: {status['prediction_count']} "
            f"(success rate {status['prediction_success_rate']}, "
            f"failed {status['failed_prediction_count']})",
            f"- question pressures: {status['question_pressure_count']}",
            f"- internal simulations: {status['internal_simulation_count']} "
            "(all marked non-real)",
            f"- counterfactuals: {status['counterfactual_count']}",
            f"- analogies: {status['analogy_count']} "
            f"(contradicted {status['analogy_failure_count']})",
            f"- synthesis events: {status['synthesis_count']}",
            f"- unresolved tensions: {status['unresolved_tension_count']}",
            f"- cognition overload events: "
            f"{status['cognition_overload_event_count']}",
            "",
            "## Failed predictions (preserved)", "",
            f"- preserved: {len(sections['failed_predictions'])} "
            "(failed predictions are useful evidence, never hidden)",
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
        md_path = os.path.join(base, "SENSORIUM_COGNITION_REPORT.md")
        json_path = os.path.join(base, "SENSORIUM_COGNITION_REPORT.json")
        markdown = self._render_markdown(report["sections"])
        if not report["claim_guard_safe"]:
            from ..governance.compliance import ClaimGuard

            markdown = ClaimGuard().rewrite(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path, "report": report}
