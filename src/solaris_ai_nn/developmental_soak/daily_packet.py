"""Daily evidence packet -- one honest day of the developmental soak.

:class:`DailyEvidencePacketBuilder` compiles a per-day evidence packet from the
upstream module statuses and the developmental-life status. The packet is
*evidence, not marketing*: negative and inconclusive results are always
included, and the operator-readable Markdown is scanned by ClaimGuard.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_LIMITATIONS = (
    "A daily packet is evidence, not marketing.",
    "Negative and inconclusive results are included, not hidden.",
    "One day is too short to claim durable structural growth.",
    "This does not prove life, consciousness, or understanding.",
)


@dataclass
class DailyEvidencePacket:
    """A single day's evidence (structural, conservative, ClaimGuard-scanned)."""

    run_day: int
    active_phase: str = ""
    tick_range: List[int] = field(default_factory=list)
    sensorium_summary: Dict[str, Any] = field(default_factory=dict)
    source_health_summary: Dict[str, Any] = field(default_factory=dict)
    metabolism_summary: Dict[str, Any] = field(default_factory=dict)
    proto_concept_changes: Dict[str, Any] = field(default_factory=dict)
    sign_changes: Dict[str, Any] = field(default_factory=dict)
    cognition_changes: Dict[str, Any] = field(default_factory=dict)
    self_boundary_changes: Dict[str, Any] = field(default_factory=dict)
    desire_action_changes: Dict[str, Any] = field(default_factory=dict)
    habit_changes: Dict[str, Any] = field(default_factory=dict)
    maturation_markers: int = 0
    plateaus: int = 0
    regressions: int = 0
    safety_blocks: int = 0
    contamination_warnings: int = 0
    growth_vs_accumulation_early_signal: str = "inconclusive"
    artifact_list: List[str] = field(default_factory=list)
    operator_summary: str = ""
    limitations: List[str] = field(default_factory=lambda: list(_LIMITATIONS))
    claim_guard_safe: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_day": self.run_day, "active_phase": self.active_phase,
            "tick_range": list(self.tick_range),
            "sensorium_summary": self.sensorium_summary,
            "source_health_summary": self.source_health_summary,
            "metabolism_summary": self.metabolism_summary,
            "proto_concept_changes": self.proto_concept_changes,
            "sign_changes": self.sign_changes,
            "cognition_changes": self.cognition_changes,
            "self_boundary_changes": self.self_boundary_changes,
            "desire_action_changes": self.desire_action_changes,
            "habit_changes": self.habit_changes,
            "maturation_markers": self.maturation_markers,
            "plateaus": self.plateaus, "regressions": self.regressions,
            "safety_blocks": self.safety_blocks,
            "contamination_warnings": self.contamination_warnings,
            "growth_vs_accumulation_early_signal":
                self.growth_vs_accumulation_early_signal,
            "artifact_list": list(self.artifact_list),
            "operator_summary": self.operator_summary,
            "limitations": list(self.limitations),
            "claim_guard_safe": self.claim_guard_safe,
        }


@dataclass
class DailyEvidencePacketBuilder:
    """Builds a daily evidence packet from module + developmental statuses."""

    def build(self, *, run_day: int, active_phase: str,
              tick_range: Optional[List[int]] = None,
              statuses: Optional[Dict[str, Dict[str, Any]]] = None,
              dev_status: Optional[Dict[str, Any]] = None,
              artifact_list: Optional[List[str]] = None,
              safety_blocks: int = 0) -> DailyEvidencePacket:
        statuses = statuses or {}
        dev_status = dev_status or {}
        sens = statuses.get("plural_sensorium", {})
        met = statuses.get("perceptual_metabolism", {})
        ont = statuses.get("perceptual_ontogenesis", {})
        sem = statuses.get("semiogenesis", {})
        cog = statuses.get("sensorium_cognition", {})
        sb = statuses.get("self_boundary", {})
        df = statuses.get("desire_formation", {})
        ar = statuses.get("action_reaction", {})

        contamination = (int(ont.get("contamination_warning_count", 0) or 0)
                         + int(sem.get("contamination_warning_count", 0) or 0))
        packet = DailyEvidencePacket(
            run_day=run_day, active_phase=active_phase,
            tick_range=list(tick_range or []),
            sensorium_summary={
                "modality_count": sens.get("modality_count",
                                           sens.get("active_modalities", 0)),
                "event_count": sens.get("event_count", 0)},
            source_health_summary={
                "active_sources": sens.get("active_source_count",
                                           sens.get("active_modalities", 0)),
                "silent_sources": sens.get("silent_source_count", 0)},
            metabolism_summary={
                "overload": met.get("overload", met.get("is_overloaded",
                                                         False)),
                "deprivation": met.get("deprivation",
                                       met.get("is_deprived", False))},
            proto_concept_changes={
                "stable_concepts": ont.get("stable_concept_count", 0),
                "decayed_concepts": ont.get("decayed_concept_count", 0)},
            sign_changes={
                "signs": sem.get("sign_count", 0),
                "useful_signs": sem.get("useful_sign_count", 0)},
            cognition_changes={
                "predictions": cog.get("prediction_count", 0),
                "correct_predictions": cog.get("correct_prediction_count", 0)},
            self_boundary_changes={
                "boundary_clarity": sb.get("boundary_clarity_score", 0.0)},
            desire_action_changes={
                "desires": df.get("desire_count", 0),
                "selected_actions": ar.get("selected_action_count", 0),
                "reactions": ar.get("reaction_count", 0)},
            habit_changes={
                "habits": ar.get("habit_candidate_count", 0),
                "inhibitions": ar.get("inhibition_count", 0)},
            maturation_markers=int(dev_status.get("maturation_marker_count", 0)
                                   or 0),
            plateaus=int(dev_status.get("plateau_count", 0) or 0),
            regressions=int(dev_status.get("regression_count", 0) or 0),
            safety_blocks=int(safety_blocks),
            contamination_warnings=contamination,
            growth_vs_accumulation_early_signal=str(
                dev_status.get("structural_growth_status", "inconclusive")),
            artifact_list=list(artifact_list or []))
        packet.operator_summary = self._operator_summary(packet)
        packet.claim_guard_safe = self._claim_guard_safe(
            packet.operator_summary)
        return packet

    @staticmethod
    def _operator_summary(p: DailyEvidencePacket) -> str:
        return (
            f"Day {p.run_day} ({p.active_phase}): "
            f"{p.maturation_markers} maturation marker(s), "
            f"{p.plateaus} plateau(s), {p.regressions} regression(s), "
            f"{p.safety_blocks} safety block(s), "
            f"{p.contamination_warnings} contamination warning(s); early "
            f"growth signal: {p.growth_vs_accumulation_early_signal}. This is "
            "operational structural evidence, not proof of life or "
            "consciousness.")

    @staticmethod
    def _claim_guard_safe(text: str) -> bool:
        try:
            from ..governance.compliance import ClaimGuard

            return ClaimGuard().scan_text(text).safe
        except Exception:
            return True
