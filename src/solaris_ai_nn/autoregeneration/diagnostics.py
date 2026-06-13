"""Diagnostics -- low-compute, non-mutating scans for degradation.

The :class:`AutoRegenerationDiagnostics` reads a normalized context (memory
layers, symbols, world model, habits, checkpoints, telemetry, hypothesis
memory, active-perception records, drift, identity) and produces
:class:`DegradationSignal`s. It never mutates state, supports partial scans,
and never crashes on missing or corrupted optional inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .degradation import (
    DegradationSeverity,
    DegradationSignal,
    DegradationState,
    DegradationType,
)


def _num(d: Optional[Dict[str, Any]], key: str, default: float = 0.0) -> float:
    try:
        return float((d or {}).get(key, default) or 0.0)
    except (TypeError, ValueError):
        return default


# Tunable thresholds (low-compute heuristics; all overridable via config).
@dataclass
class DiagnosticsThresholds:
    memory_layer_over_budget: int = 1          # any over-budget layer
    telemetry_event_warn: int = 1_000_000
    symbol_explosion_warn: int = 500
    symbol_stale_ratio_warn: float = 0.5
    ambiguous_ratio_warn: float = 0.6
    prediction_floor: float = 0.35
    mysterium_saturation: float = 0.95
    executive_no_safe_action_warn: int = 5
    homeostasis_conflict_warn: int = 5
    hypothesis_inconclusive_warn: int = 15
    unsafe_sampling_warn: int = 10
    identity_continuity_floor: float = 0.6


@dataclass
class AutoRegenerationDiagnostics:
    """Non-mutating degradation scanner over a normalized context."""

    thresholds: DiagnosticsThresholds = field(
        default_factory=DiagnosticsThresholds)
    scans_run: int = field(default=0, init=False)
    last_state: Optional[DegradationState] = field(default=None, init=False)

    # -- top-level ----------------------------------------------------------------

    def scan(self, context: Dict[str, Any]) -> DegradationState:
        ctx = dict(context or {})
        state = DegradationState()
        for sub in (self.scan_memory, self.scan_symbols,
                    self.scan_world_model, self.scan_habits,
                    self.scan_checkpoints, self.scan_references,
                    self.scan_drift, self._scan_runtime,
                    self._scan_telemetry):
            try:
                for signal in sub(ctx):
                    state.add(signal)
            except Exception:  # diagnostics must never crash the run
                continue
        self.scans_run += 1
        self.last_state = state
        return state

    # -- sub-scans (each returns a list, never mutates) ---------------------------

    def scan_memory(self, context: Dict[str, Any]) -> List[DegradationSignal]:
        memory = context.get("memory") or {}
        out: List[DegradationSignal] = []
        over = memory.get("over_budget") or []
        if over:
            out.append(DegradationSignal(
                type=DegradationType.MEMORY_BLOAT,
                severity=DegradationSeverity.WARNING,
                source_module="memory_layers",
                evidence_refs=[f"over_budget:{l}" for l in over],
                metric_snapshot={"over_budget": list(over)},
                probable_causes=["hot layer exceeded its budget",
                                 "consolidation has not run recently"]))
        comp = memory.get("compression_ratio")
        if comp is not None and float(comp) > 0.95 and over:
            out.append(DegradationSignal(
                type=DegradationType.MEMORY_BLOAT,
                severity=DegradationSeverity.WATCH,
                source_module="memory_layers",
                evidence_refs=["compression_ratio"],
                metric_snapshot={"compression_ratio": comp},
                probable_causes=["little compression achieved"]))
        return out

    def scan_symbols(self, context: Dict[str, Any]) -> List[DegradationSignal]:
        proto = context.get("proto_language") or {}
        out: List[DegradationSignal] = []
        count = int(_num(proto, "symbol_count"))
        if count > self.thresholds.symbol_explosion_warn:
            out.append(DegradationSignal(
                type=DegradationType.SYMBOL_EXPLOSION,
                severity=DegradationSeverity.WARNING,
                source_module="symbol_registry",
                evidence_refs=["symbol_count"],
                metric_snapshot={"symbol_count": count},
                probable_causes=["emergence threshold too low",
                                 "noise being named"]))
        stale = proto.get("stale_symbols") or []
        if count and (len(stale) / count) >= \
                self.thresholds.symbol_stale_ratio_warn:
            out.append(DegradationSignal(
                type=DegradationType.SYMBOL_STALENESS,
                severity=DegradationSeverity.WATCH,
                source_module="symbol_registry",
                evidence_refs=["stale_symbols"],
                metric_snapshot={"stale": len(stale), "total": count},
                probable_causes=["symbols no longer recur"]))
        ambiguous = int(_num(proto, "ambiguous_symbol_count"))
        if count and (ambiguous / count) >= self.thresholds.ambiguous_ratio_warn:
            out.append(DegradationSignal(
                type=DegradationType.SYMBOL_STALENESS,
                severity=DegradationSeverity.WATCH,
                source_module="symbol_registry",
                evidence_refs=["ambiguous_symbol_count"],
                metric_snapshot={"ambiguous": ambiguous, "total": count},
                probable_causes=["grounding inconsistent across contexts"]))
        return out

    def scan_world_model(self, context: Dict[str, Any],
                        ) -> List[DegradationSignal]:
        wm = context.get("world_model") or {}
        out: List[DegradationSignal] = []
        contradictions = wm.get("contradiction_edges") or []
        if contradictions or int(_num(wm, "contradiction_edge_count")):
            n = len(contradictions) or int(_num(wm, "contradiction_edge_count"))
            out.append(DegradationSignal(
                type=DegradationType.WORLD_MODEL_CONTRADICTION,
                severity=DegradationSeverity.WARNING,
                source_module="world_model",
                evidence_refs=[f"contradiction:{c}" for c in contradictions]
                or ["contradiction_edge_count"],
                metric_snapshot={"contradiction_edges": n},
                probable_causes=["conflicting observations",
                                 "unresolved hypothesis"]))
        weak = wm.get("weak_edges") or []
        if weak:
            out.append(DegradationSignal(
                type=DegradationType.WORLD_MODEL_EDGE_DECAY,
                severity=DegradationSeverity.WATCH,
                source_module="world_model",
                evidence_refs=[f"weak_edge:{e}" for e in weak[:5]],
                metric_snapshot={"weak_edges": len(weak)},
                probable_causes=["edges decayed below support threshold"]))
        accuracy = wm.get("prediction_accuracy")
        if accuracy is not None and float(accuracy) < \
                self.thresholds.prediction_floor:
            out.append(DegradationSignal(
                type=DegradationType.PREDICTION_DEGRADATION,
                severity=DegradationSeverity.WARNING,
                source_module="world_model",
                evidence_refs=["prediction_accuracy"],
                metric_snapshot={"prediction_accuracy": accuracy},
                probable_causes=["model drifted from the environment",
                                 "non-stationary world"]))
        return out

    def scan_habits(self, context: Dict[str, Any]) -> List[DegradationSignal]:
        habits = context.get("habits") or {}
        out: List[DegradationSignal] = []
        if habits.get("dead_habits"):
            out.append(DegradationSignal(
                type=DegradationType.HABIT_DEAD_LOOP,
                severity=DegradationSeverity.WATCH,
                source_module="habit",
                evidence_refs=["dead_habits"],
                metric_snapshot={"dead_habits":
                                 len(habits["dead_habits"])},
                probable_causes=["pathway no longer reinforced"]))
        if habits.get("runaway_habits"):
            out.append(DegradationSignal(
                type=DegradationType.HABIT_RUNAWAY,
                severity=DegradationSeverity.WARNING,
                source_module="habit",
                evidence_refs=["runaway_habits"],
                metric_snapshot={"runaway_habits":
                                 len(habits["runaway_habits"])},
                probable_causes=["positive feedback without bound",
                                 "habit suppressing exploration"]))
        return out

    def scan_checkpoints(self, context: Dict[str, Any],
                        ) -> List[DegradationSignal]:
        cp = context.get("checkpoints") or {}
        out: List[DegradationSignal] = []
        issues = cp.get("issues") or []
        if issues:
            out.append(DegradationSignal(
                type=DegradationType.CHECKPOINT_INCONSISTENCY,
                severity=DegradationSeverity.WARNING,
                source_module="checkpoint",
                evidence_refs=[f"checkpoint_issue:{i}" for i in issues],
                metric_snapshot={"issues": list(issues)},
                probable_causes=["missing parent",
                                 "impossible timestamp order",
                                 "incomplete checkpoint"]))
        identity = context.get("identity") or {}
        score = identity.get("continuity_score")
        if score is not None and float(score) < \
                self.thresholds.identity_continuity_floor:
            out.append(DegradationSignal(
                type=DegradationType.IDENTITY_CONTINUITY_GAP,
                severity=DegradationSeverity.WARNING,
                source_module="ego_identity",
                evidence_refs=["identity_continuity_score"],
                metric_snapshot={"continuity_score": score},
                probable_causes=["anchor mismatch after restart",
                                 "brain-death gap"]))
        return out

    def scan_references(self, context: Dict[str, Any],
                       ) -> List[DegradationSignal]:
        refs = context.get("references") or {}
        out: List[DegradationSignal] = []
        broken = refs.get("broken") or []
        if broken:
            out.append(DegradationSignal(
                type=DegradationType.BROKEN_REFERENCE,
                severity=DegradationSeverity.WATCH,
                source_module="references",
                evidence_refs=[f"broken_ref:{b}" for b in broken[:5]],
                metric_snapshot={"broken": len(broken)},
                probable_causes=["referenced record was archived/removed"]))
        corrupt = (context.get("state_files") or {}).get("corrupt") or []
        if corrupt:
            out.append(DegradationSignal(
                type=DegradationType.STATE_FILE_CORRUPTION,
                severity=DegradationSeverity.WARNING,
                source_module="state_files",
                evidence_refs=[f"corrupt:{c}" for c in corrupt[:5]],
                metric_snapshot={"corrupt": len(corrupt)},
                probable_causes=["partial write", "truncated JSONL"]))
        return out

    def scan_drift(self, context: Dict[str, Any]) -> List[DegradationSignal]:
        drift = context.get("drift") or {}
        out: List[DegradationSignal] = []
        classification = drift.get("classification") or \
            drift.get("latest_classification")
        if classification == "fast_warning":
            out.append(DegradationSignal(
                type=DegradationType.DRIFT_RUNAWAY,
                severity=DegradationSeverity.WARNING,
                source_module="drift_monitor",
                evidence_refs=["drift_classification"],
                metric_snapshot={"classification": classification,
                                 "velocity": drift.get("drift_velocity")},
                probable_causes=["uncontrolled state drift"]))
        elif classification == "inert_warning" \
                or context.get("stagnation_status") in ("stagnating",
                                                        "inert"):
            out.append(DegradationSignal(
                type=DegradationType.DEVELOPMENTAL_STAGNATION,
                severity=DegradationSeverity.WATCH,
                source_module="drift_monitor",
                evidence_refs=["drift_classification"],
                metric_snapshot={"classification": classification},
                probable_causes=["no structural change",
                                 "environment too flat"]))
        return out

    def _scan_runtime(self, context: Dict[str, Any],
                     ) -> List[DegradationSignal]:
        out: List[DegradationSignal] = []
        mysterium = _num(context, "mysterium_pressure")
        if mysterium >= self.thresholds.mysterium_saturation:
            out.append(DegradationSignal(
                type=DegradationType.MYSTERIUM_SATURATION,
                severity=DegradationSeverity.WARNING,
                source_module="latent",
                evidence_refs=["mysterium_pressure"],
                metric_snapshot={"mysterium_pressure": mysterium},
                probable_causes=["unknown pressure pinned at maximum"]))
        executive = context.get("executive") or {}
        if _num(executive, "no_safe_action_count") >= \
                self.thresholds.executive_no_safe_action_warn:
            out.append(DegradationSignal(
                type=DegradationType.EXECUTIVE_LOOP,
                severity=DegradationSeverity.WATCH,
                source_module="executive",
                evidence_refs=["no_safe_action_count"],
                metric_snapshot={"no_safe_action_count":
                                 executive.get("no_safe_action_count")},
                probable_causes=["arbitration finds no safe candidate"]))
        homeostasis = context.get("homeostasis") or {}
        if _num(homeostasis, "conflict_count") >= \
                self.thresholds.homeostasis_conflict_warn:
            out.append(DegradationSignal(
                type=DegradationType.HOMEOSTATIC_INSTABILITY,
                severity=DegradationSeverity.WATCH,
                source_module="homeostasis",
                evidence_refs=["conflict_count"],
                metric_snapshot={"conflict_count":
                                 homeostasis.get("conflict_count")},
                probable_causes=["competing needs not resolving"]))
        hypothesis = context.get("hypothesis") or {}
        if _num(hypothesis, "inconclusive_count") >= \
                self.thresholds.hypothesis_inconclusive_warn:
            out.append(DegradationSignal(
                type=DegradationType.HYPOTHESIS_INCONCLUSIVE_LOOP,
                severity=DegradationSeverity.WATCH,
                source_module="hypothesis",
                evidence_refs=["inconclusive_count"],
                metric_snapshot={"inconclusive_count":
                                 hypothesis.get("inconclusive_count")},
                probable_causes=["experiment designs not discriminating"]))
        ap = context.get("active_perception") or {}
        if _num(ap, "blocked_count") >= self.thresholds.unsafe_sampling_warn:
            out.append(DegradationSignal(
                type=DegradationType.UNSAFE_SAMPLING_REPETITION,
                severity=DegradationSeverity.WATCH,
                source_module="active_perception",
                evidence_refs=["blocked_count"],
                metric_snapshot={"blocked_count": ap.get("blocked_count")},
                probable_causes=["policy keeps proposing refused sampling"]))
        return out

    def _scan_telemetry(self, context: Dict[str, Any],
                       ) -> List[DegradationSignal]:
        telemetry = context.get("telemetry") or {}
        out: List[DegradationSignal] = []
        events = _num(telemetry, "trace_event_count",
                      _num(telemetry, "events"))
        if events > self.thresholds.telemetry_event_warn:
            out.append(DegradationSignal(
                type=DegradationType.TELEMETRY_OVERGROWTH,
                severity=DegradationSeverity.WATCH,
                source_module="telemetry",
                evidence_refs=["trace_event_count"],
                metric_snapshot={"events": events},
                probable_causes=["telemetry/trace not rotated"]))
        return out

    def snapshot(self) -> Dict[str, Any]:
        return {
            "scans_run": self.scans_run,
            "last_state": (self.last_state.to_dict()
                           if self.last_state else None),
        }
