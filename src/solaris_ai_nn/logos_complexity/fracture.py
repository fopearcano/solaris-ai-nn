"""Fracture detection -- where the system splits, contradicts, or opposes.

The :class:`FractureDetector` reads a normalized context and emits
:class:`LogosTension`s from world-model contradictions, ambiguous
proto-symbols, failed predictions, Mysterium spikes, hypothesis
falsification, executive inhibition loops, homeostatic conflict,
developmental stagnation/drift, ecology anomalies, auto-regeneration
degradation, ego boundary uncertainty, and memory-compression conflicts.
Detection only -- it never mutates state, works with partial context, and
never crashes on missing optional modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .tension import (
    LogosTension,
    TensionPolarity,
    TensionSeverity,
    TensionType,
)


def _num(d: Optional[Dict[str, Any]], key: str, default: float = 0.0) -> float:
    try:
        return float((d or {}).get(key, default) or 0.0)
    except (TypeError, ValueError):
        return default


@dataclass
class FractureDetector:
    """Low-compute, non-mutating opposition scanner over a context."""

    scans_run: int = field(default=0, init=False)
    last_tensions: List[LogosTension] = field(default_factory=list, init=False)

    def scan(self, context: Dict[str, Any]) -> List[LogosTension]:
        ctx = dict(context or {})
        tensions: List[LogosTension] = []
        for sub in (self.scan_world_model, self.scan_proto_symbols,
                    self.scan_hypotheses, self.scan_active_perception,
                    self.scan_developmental_state,
                    self.scan_autoregeneration, self._scan_runtime,
                    self._scan_boundaries):
            try:
                tensions.extend(sub(ctx))
            except Exception:  # detection must never crash the run
                continue
        self.scans_run += 1
        self.last_tensions = tensions
        return tensions

    # -- sub-scans ----------------------------------------------------------------

    def scan_world_model(self, context: Dict[str, Any],
                        ) -> List[LogosTension]:
        wm = (context or {}).get("world_model") or {}
        out: List[LogosTension] = []
        contradictions = wm.get("contradiction_edges") or []
        if contradictions or int(_num(wm, "contradiction_edge_count")):
            out.append(LogosTension(
                tension_type=TensionType.WORLD_MODEL_CONTRADICTION,
                polarity_a=TensionPolarity.SUPPORT,
                polarity_b=TensionPolarity.CONTRADICTION,
                severity=TensionSeverity.WARNING,
                source_modules=["world_model"],
                evidence_refs=[f"contradiction:{c}" for c in contradictions]
                or ["contradiction_edge_count"],
                related_world_nodes=[str(c) for c in contradictions[:5]],
                expected_resolution_value=0.6, risk_level="low",
                confidence=0.6))
        accuracy = wm.get("prediction_accuracy")
        if accuracy is not None and float(accuracy) < 0.4:
            out.append(LogosTension(
                tension_type=TensionType.PREDICTION_FAILURE,
                polarity_a=TensionPolarity.CONFIDENCE,
                polarity_b=TensionPolarity.FAILURE,
                severity=TensionSeverity.WARNING,
                source_modules=["world_model"],
                evidence_refs=["prediction_accuracy"],
                expected_resolution_value=0.5, confidence=0.6))
        return out

    def scan_proto_symbols(self, context: Dict[str, Any],
                          ) -> List[LogosTension]:
        proto = (context or {}).get("proto_language") or {}
        out: List[LogosTension] = []
        count = int(_num(proto, "symbol_count"))
        ambiguous = proto.get("ambiguous_symbols") or []
        amb_count = int(_num(proto, "ambiguous_symbol_count")) or len(
            ambiguous)
        if amb_count and count and (amb_count / count) >= 0.3:
            out.append(LogosTension(
                tension_type=TensionType.SYMBOL_AMBIGUITY,
                polarity_a=TensionPolarity.STABLE,
                polarity_b=TensionPolarity.AMBIGUOUS,
                severity=TensionSeverity.WATCH,
                source_modules=["protolanguage"],
                evidence_refs=["ambiguous_symbol_count"],
                related_symbols=[str(s) for s in ambiguous[:5]],
                expected_resolution_value=0.5, confidence=0.55))
        elif ambiguous:
            out.append(LogosTension(
                tension_type=TensionType.SYMBOL_AMBIGUITY,
                polarity_a=TensionPolarity.STABLE,
                polarity_b=TensionPolarity.AMBIGUOUS,
                severity=TensionSeverity.WATCH,
                source_modules=["protolanguage"],
                evidence_refs=[f"symbol:{ambiguous[0]}"],
                related_symbols=[str(s) for s in ambiguous[:5]],
                expected_resolution_value=0.4, confidence=0.5))
        return out

    def scan_hypotheses(self, context: Dict[str, Any],
                       ) -> List[LogosTension]:
        hyp = (context or {}).get("hypothesis") or {}
        out: List[LogosTension] = []
        if _num(hyp, "falsified_count") >= 1 \
                and _num(hyp, "supported_count") >= 1:
            out.append(LogosTension(
                tension_type=TensionType.HYPOTHESIS_CONFLICT,
                polarity_a=TensionPolarity.SUPPORT,
                polarity_b=TensionPolarity.CONTRADICTION,
                severity=TensionSeverity.WATCH,
                source_modules=["hypothesis"],
                evidence_refs=["supported_count", "falsified_count"],
                expected_resolution_value=0.4, confidence=0.5))
        return out

    def scan_active_perception(self, context: Dict[str, Any],
                              ) -> List[LogosTension]:
        ctx = dict(context or {})
        ap = ctx.get("active_perception") or {}
        out: List[LogosTension] = []
        curiosity = _num(ap, "curiosity_pressure", _num(ctx, "curiosity_"
                                                        "pressure"))
        if curiosity > 0.5:
            out.append(LogosTension(
                tension_type=TensionType.EXPLORE_STABILIZE,
                polarity_a=TensionPolarity.EXPLORE,
                polarity_b=TensionPolarity.STABILIZE,
                severity=TensionSeverity.INFO,
                source_modules=["active_perception"],
                evidence_refs=["curiosity_pressure"],
                expected_resolution_value=0.3, confidence=0.5))
        return out

    def scan_developmental_state(self, context: Dict[str, Any],
                                ) -> List[LogosTension]:
        ctx = dict(context or {})
        out: List[LogosTension] = []
        if ctx.get("stagnation_status") in ("stagnating", "inert"):
            out.append(LogosTension(
                tension_type=TensionType.GROWTH_STAGNATION,
                polarity_a=TensionPolarity.GROWTH,
                polarity_b=TensionPolarity.STAGNATION,
                severity=TensionSeverity.WATCH,
                source_modules=["developmental"],
                evidence_refs=["stagnation_status"],
                expected_resolution_value=0.4, confidence=0.5))
        drift = ctx.get("drift") or {}
        classification = (drift.get("classification")
                          or drift.get("latest_classification"))
        identity = ctx.get("identity") or {}
        if classification == "fast_warning" \
                or (identity.get("continuity_score") is not None
                    and float(identity["continuity_score"]) < 0.6):
            out.append(LogosTension(
                tension_type=TensionType.DRIFT_IDENTITY,
                polarity_a=TensionPolarity.DRIFT,
                polarity_b=TensionPolarity.IDENTITY,
                severity=TensionSeverity.WARNING,
                source_modules=["developmental", "ego_identity"],
                evidence_refs=["drift_classification",
                               "identity_continuity_score"],
                expected_resolution_value=0.5, risk_level="medium",
                confidence=0.55))
        return out

    def scan_autoregeneration(self, context: Dict[str, Any],
                             ) -> List[LogosTension]:
        ar = (context or {}).get("autoregeneration") or {}
        out: List[LogosTension] = []
        severity = ar.get("latest_degradation_severity")
        dtype = ar.get("latest_degradation_type")
        if severity in ("warning", "critical") and dtype:
            out.append(LogosTension(
                tension_type=TensionType.COMPLEXITY_OVERLOAD,
                polarity_a=TensionPolarity.COMPLEX,
                polarity_b=TensionPolarity.SIMPLE,
                severity=(TensionSeverity.HIGH if severity == "critical"
                          else TensionSeverity.WARNING),
                source_modules=["autoregeneration"],
                evidence_refs=[f"degradation:{dtype}"],
                expected_resolution_value=0.6, risk_level="medium",
                confidence=0.6))
        return out

    def _scan_runtime(self, context: Dict[str, Any]) -> List[LogosTension]:
        ctx = dict(context or {})
        out: List[LogosTension] = []
        mysterium = _num(ctx, "mysterium_pressure")
        if mysterium >= 0.5:
            out.append(LogosTension(
                tension_type=TensionType.MYSTERIUM_SYNTHESIS,
                polarity_a=TensionPolarity.MYSTERIUM,
                polarity_b=TensionPolarity.SYNTHESIS,
                severity=(TensionSeverity.WARNING if mysterium >= 0.9
                          else TensionSeverity.WATCH),
                source_modules=["latent"],
                evidence_refs=["mysterium_pressure"],
                expected_resolution_value=mysterium, confidence=0.6))
        ecology = ctx.get("ecology") or {}
        if _num(ecology, "anomaly_rate") > 0.1:
            out.append(LogosTension(
                tension_type=TensionType.REGULARITY_ANOMALY,
                polarity_a=TensionPolarity.REGULARITY,
                polarity_b=TensionPolarity.ANOMALY,
                severity=TensionSeverity.WATCH,
                source_modules=["ecology"],
                evidence_refs=["anomaly_rate"],
                expected_resolution_value=0.4, confidence=0.5))
        executive = ctx.get("executive") or {}
        if _num(executive, "no_safe_action_count") >= 5:
            out.append(LogosTension(
                tension_type=TensionType.ACTION_INHIBITION,
                polarity_a=TensionPolarity.ACTION,
                polarity_b=TensionPolarity.INHIBITION,
                severity=TensionSeverity.WATCH,
                source_modules=["executive"],
                evidence_refs=["no_safe_action_count"],
                expected_resolution_value=0.4, confidence=0.5))
        homeostasis = ctx.get("homeostasis") or {}
        if _num(homeostasis, "conflict_count") >= 1:
            out.append(LogosTension(
                tension_type=TensionType.NEED_SAFETY,
                polarity_a=TensionPolarity.NEED,
                polarity_b=TensionPolarity.SAFETY,
                severity=TensionSeverity.WATCH,
                source_modules=["homeostasis"],
                evidence_refs=["conflict_count"],
                expected_resolution_value=0.4, risk_level="low",
                confidence=0.5))
        memory = ctx.get("memory") or {}
        if memory.get("over_budget"):
            out.append(LogosTension(
                tension_type=TensionType.MEMORY_COMPRESSION,
                polarity_a=TensionPolarity.ACCUMULATION,
                polarity_b=TensionPolarity.COMPRESSION,
                severity=TensionSeverity.WATCH,
                source_modules=["memory"],
                evidence_refs=["over_budget"],
                expected_resolution_value=0.4, confidence=0.5))
        return out

    def _scan_boundaries(self, context: Dict[str, Any],
                        ) -> List[LogosTension]:
        ctx = dict(context or {})
        out: List[LogosTension] = []
        ego = ctx.get("ego") or {}
        if _num(ego, "boundary_violation_count") >= 1 \
                or _num(ego, "attribution_unknown_rate") > 0.5:
            out.append(LogosTension(
                tension_type=TensionType.SELF_OTHER_BOUNDARY,
                polarity_a=TensionPolarity.SELF,
                polarity_b=TensionPolarity.OTHER,
                severity=TensionSeverity.WATCH,
                source_modules=["ego"],
                evidence_refs=["boundary_violation_count"],
                expected_resolution_value=0.3, risk_level="low",
                confidence=0.5))
        if ctx.get("offline_real_conflict"):
            out.append(LogosTension(
                tension_type=TensionType.OFFLINE_REAL_BOUNDARY,
                polarity_a=TensionPolarity.OFFLINE,
                polarity_b=TensionPolarity.REAL,
                severity=TensionSeverity.WATCH,
                source_modules=["latent", "ego"],
                evidence_refs=["offline_real_conflict"],
                expected_resolution_value=0.3, confidence=0.5))
        return out

    def snapshot(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for t in self.last_tensions:
            counts[t.tension_type] = counts.get(t.tension_type, 0) + 1
        return {
            "scans_run": self.scans_run,
            "last_tension_count": len(self.last_tensions),
            "by_type": counts,
        }
