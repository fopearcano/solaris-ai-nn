"""Post-pilot structural-change analysis -- evidence, not count-watching.

The :class:`StructuralChangeAnalyzer` turns baseline deltas (plus the loaded
artifacts) into :class:`StructuralChangeEvidence` records. Each record points
to artifacts, carries an alternative explanation, a conservative confidence,
and a stability flag (transient/persistent/unknown). A bare count increase is
never, by itself, structural change.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class StructuralChangeCategory:
    MEMORY_REORGANIZATION = "memory_reorganization"
    STABLE_HABIT_FORMATION = "stable_habit_formation"
    HABIT_COLLAPSE_OR_REPLACEMENT = "habit_collapse_or_replacement"
    WORLD_MODEL_SCHEMA_EMERGENCE = "world_model_schema_emergence"
    WORLD_MODEL_PRUNING = "world_model_pruning"
    PROTO_SYMBOL_EMERGENCE = "proto_symbol_emergence"
    PROTO_SYMBOL_STABILIZATION = "proto_symbol_stabilization"
    PROTO_SYNTAX_REGULARIZATION = "proto_syntax_regularization"
    HYPOTHESIS_TO_WORLD_MODEL_UPDATE = "hypothesis_to_world_model_update"
    ACTIVE_SAMPLING_POLICY_SHIFT = "active_sampling_policy_shift"
    LOGOS_TENSION_RESOLUTION = "LOGOS_tension_resolution"
    COMPLEXITY_BAND_SHIFT = "complexity_band_shift"
    AUTO_REGENERATION_REPAIR_EFFECT = "auto_regeneration_repair_effect"
    DEVELOPMENTAL_EPOCH_TRANSITION = "developmental_epoch_transition"
    IDENTITY_RESTART_CONTINUITY = "identity_restart_continuity"
    UNKNOWN_PRESSURE_REORGANIZATION = "unknown_pressure_reorganization"

    ALL = (MEMORY_REORGANIZATION, STABLE_HABIT_FORMATION,
           HABIT_COLLAPSE_OR_REPLACEMENT, WORLD_MODEL_SCHEMA_EMERGENCE,
           WORLD_MODEL_PRUNING, PROTO_SYMBOL_EMERGENCE,
           PROTO_SYMBOL_STABILIZATION, PROTO_SYNTAX_REGULARIZATION,
           HYPOTHESIS_TO_WORLD_MODEL_UPDATE, ACTIVE_SAMPLING_POLICY_SHIFT,
           LOGOS_TENSION_RESOLUTION, COMPLEXITY_BAND_SHIFT,
           AUTO_REGENERATION_REPAIR_EFFECT, DEVELOPMENTAL_EPOCH_TRANSITION,
           IDENTITY_RESTART_CONTINUITY, UNKNOWN_PRESSURE_REORGANIZATION)


class Stability:
    TRANSIENT = "transient"
    PERSISTENT = "persistent"
    UNKNOWN = "unknown"

    ALL = (TRANSIENT, PERSISTENT, UNKNOWN)


@dataclass
class StructuralChangeEvidence:
    """One evidence record for a candidate structural change."""

    category: str
    metric_delta: float = 0.0
    before_ref: Optional[str] = None
    after_ref: Optional[str] = None
    supporting_artifacts: List[str] = field(default_factory=list)
    alternative_explanation: str = ""
    confidence: float = 0.0
    stability: str = Stability.UNKNOWN
    limitations: List[str] = field(default_factory=list)
    evidence_id: str = field(
        default_factory=lambda: f"SCE_{uuid.uuid4().hex[:10]}")
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class StructuralChangeAnalyzer:
    """Derives conservative structural-change evidence from deltas+artifacts."""

    def analyze(self, comparison: Any, artifacts: Any = None,
                persistence_windows: Optional[List[Any]] = None,
                ) -> List[StructuralChangeEvidence]:
        """Return evidence records for the supplied baseline comparison.

        ``persistence_windows`` is an optional list of additional comparisons
        (e.g. week-by-week); a change seen across them is marked persistent.
        """
        deltas = getattr(comparison, "deltas", {}) or {}
        before_label = getattr(comparison, "before_label", "before")
        after_label = getattr(comparison, "after_label", "after")
        present = set(getattr(getattr(artifacts, "index", None), "present", [])
                     or [])
        out: List[StructuralChangeEvidence] = []

        def persistent(key: str) -> str:
            if not persistence_windows:
                return Stability.UNKNOWN
            seen = sum(1 for w in persistence_windows
                       if abs((getattr(w, "deltas", {}) or {}).get(key, 0.0))
                       > 1e-9)
            return (Stability.PERSISTENT if seen >= len(persistence_windows)
                    else Stability.TRANSIENT if seen else Stability.UNKNOWN)

        def add(category: str, key: str, support: List[str], alt: str,
                base_conf: float, lims: List[str]) -> None:
            delta = float(deltas.get(key, 0.0) or 0.0)
            if delta == 0.0:
                return
            avail = [s for s in support if s in present]
            # Confidence is conservative: needs supporting artifacts present.
            conf = round(base_conf * (0.5 + 0.5 * bool(avail)), 4)
            stab = persistent(key)
            if stab == Stability.PERSISTENT:
                conf = round(min(1.0, conf + 0.15), 4)
            elif stab == Stability.TRANSIENT:
                conf = round(conf * 0.6, 4)
            out.append(StructuralChangeEvidence(
                category=category, metric_delta=delta,
                before_ref=before_label, after_ref=after_label,
                supporting_artifacts=avail or list(support),
                alternative_explanation=alt, confidence=conf, stability=stab,
                limitations=lims))

        # Memory reorganization: compression improved (not just more files).
        add(StructuralChangeCategory.MEMORY_REORGANIZATION, "compression_ratio",
            ["developmental_state", "autobiographical_memory"],
            "compression ratio could shift from log rotation, not learning",
            0.6, ["needs schema-level evidence, not file counts"])
        # Proto-symbol stabilization: ambiguity fell.
        if float(deltas.get("ambiguous_symbol_ratio", 0.0) or 0.0) < 0:
            add(StructuralChangeCategory.PROTO_SYMBOL_STABILIZATION,
                "ambiguous_symbol_ratio",
                ["proto_symbols", "symbol_memory"],
                "ambiguity can drop simply from pruning rare symbols",
                0.6, ["stabilization must persist across windows"])
        # Proto-symbol emergence: stable symbols grew.
        add(StructuralChangeCategory.PROTO_SYMBOL_STABILIZATION,
            "stable_symbol_count", ["proto_symbols", "symbol_memory"],
            "more stable symbols may reflect exposure, not regularization",
            0.5, ["count growth alone is weak evidence"])
        # World-model pruning: contradictions fell.
        if float(deltas.get("world_model_contradiction_count", 0.0) or 0.0) < 0:
            add(StructuralChangeCategory.WORLD_MODEL_PRUNING,
                "world_model_contradiction_count",
                ["conscience_bus", "hypothesis_history"],
                "fewer contradictions may reflect less input, not resolution",
                0.55, ["must preserve contradiction evidence"])
        # Hypothesis -> world model update: supported hypotheses grew.
        add(StructuralChangeCategory.HYPOTHESIS_TO_WORLD_MODEL_UPDATE,
            "supported_hypothesis_count",
            ["hypotheses", "hypothesis_history"],
            "support may reflect weak tests, not real confirmation",
            0.55, ["confirm test quality, not just support count"])
        # LOGOS tension resolution.
        add(StructuralChangeCategory.LOGOS_TENSION_RESOLUTION,
            "resolved_tension_count", ["logos_tensions"],
            "resolution may be premature synthesis, not genuine integration",
            0.55, ["preserve unresolved tensions deliberately kept open"])
        # Auto-regeneration repair effect.
        add(StructuralChangeCategory.AUTO_REGENERATION_REPAIR_EFFECT,
            "autoregeneration_event_count", ["repair_memory"],
            "repairs may hide a recurring problem rather than fix it",
            0.5, ["distinguish repair from suppression"])
        # Developmental epoch transition.
        add(StructuralChangeCategory.DEVELOPMENTAL_EPOCH_TRANSITION,
            "structural_change_score",
            ["developmental_epochs", "developmental_state"],
            "score movement may be noise without epoch corroboration",
            0.6, ["needs multi-metric corroboration"])
        # Identity continuity across restarts.
        if getattr(comparison, "identity_continuous", True):
            out.append(StructuralChangeEvidence(
                category=StructuralChangeCategory.IDENTITY_RESTART_CONTINUITY,
                metric_delta=0.0, before_ref=before_label,
                after_ref=after_label,
                supporting_artifacts=[a for a in ("incidents",
                                                  "developmental_state")
                                      if a in present],
                alternative_explanation="continuity may be untested if no "
                                        "restart occurred",
                confidence=0.5, stability=Stability.UNKNOWN,
                limitations=["continuity is only meaningful if a restart "
                             "happened"]))
        # Habit stability change.
        add(StructuralChangeCategory.STABLE_HABIT_FORMATION, "habit_stability",
            ["conscience_bus"],
            "habit stability may reflect a static environment",
            0.5, ["context sensitivity must be checked"])
        return out

    def summarize(self, evidence: List[StructuralChangeEvidence],
                  ) -> Dict[str, Any]:
        by_cat: Dict[str, int] = {}
        for e in evidence:
            by_cat[e.category] = by_cat.get(e.category, 0) + 1
        persistent = [e.evidence_id for e in evidence
                      if e.stability == Stability.PERSISTENT]
        return {
            "evidence_count": len(evidence),
            "by_category": by_cat,
            "persistent_count": len(persistent),
            "mean_confidence": round(
                sum(e.confidence for e in evidence) / len(evidence), 4)
            if evidence else 0.0,
            "high_confidence_count": sum(1 for e in evidence
                                         if e.confidence >= 0.6),
        }
