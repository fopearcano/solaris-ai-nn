"""LOGOS fracture/synthesis engine and complexity regulation.

LOGOS detects internal *tensions* (known vs unknown, habit vs novelty,
support vs contradiction, ...) and uses them as productive cognitive
pressure. It decides whether a tension should be preserved, split, merged,
synthesized, pruned, stabilized, converted to a hypothesis, or routed to
active perception / latent replay / auto-regeneration / executive
arbitration -- or marked as unresolved Mysterium.

Core principle: **LOGOS is not authority; LOGOS is a tension engine.** It does
not decide truth -- it exposes fracture and proposes bounded resolution paths.
No LLM reasoning, no external APIs, no real-world action, and nothing here can
bypass governance, safety, executive inhibition, ego boundaries, ClaimGuard,
the emergency stop, or auto-regeneration safety.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .complexity_metrics import compute_complexity_metrics
from .complexity_state import (
    ComplexityBand,
    ComplexityPressure,
    ComplexityRegulator,
    ComplexityState,
)
from .dialectical_trace import (
    DialecticalTrace,
    DialecticalTraceEvent,
    TraceEventType,
)
from .esc_process import EscalationState, EscProcess, EscResponse
from .fracture import FractureDetector
from .opposition_memory import OppositionMemory, OppositionRecord
from .reports import (
    LOGOS_LIMITATIONS,
    LogosComplexityQueryInterface,
    LogosComplexityReportBuilder,
)
from .resolution_policy import (
    ResolutionDecision,
    ResolutionMode,
    ResolutionPolicy,
)
from .safety import LogosComplexitySafetyValidator
from .synthesis import (
    SynthesisCandidate,
    SynthesisEngine,
    SynthesisResult,
    SynthesisResultClass,
    SynthesisType,
    synthesis_to_candidate,
)
from .tension import (
    LogosTension,
    TensionPolarity,
    TensionSeverity,
    TensionStatus,
    TensionType,
)

__all__ = [
    "ComplexityBand", "ComplexityPressure", "ComplexityRegulator",
    "ComplexityState", "DialecticalTrace", "DialecticalTraceEvent",
    "EscProcess", "EscResponse", "EscalationState", "FractureDetector",
    "LOGOS_LIMITATIONS", "LogosComplexityEngine",
    "LogosComplexityQueryInterface", "LogosComplexityReportBuilder",
    "LogosComplexitySafetyValidator", "LogosTension", "OppositionMemory",
    "OppositionRecord", "ResolutionDecision", "ResolutionMode",
    "ResolutionPolicy", "SynthesisCandidate", "SynthesisEngine",
    "SynthesisResult", "SynthesisResultClass", "SynthesisType",
    "TensionPolarity", "TensionSeverity", "TensionStatus", "TensionType",
    "TraceEventType", "compute_complexity_metrics", "synthesis_to_candidate",
]

# Synthesis types -> the dialectical trace event they emit when applied.
_TRACE_FOR_SYNTHESIS = {
    SynthesisType.CREATE_HYPOTHESIS: TraceEventType.HYPOTHESIS_SPAWNED,
    SynthesisType.REQUEST_ACTIVE_SAMPLING: TraceEventType.SAMPLING_REQUESTED,
    SynthesisType.REQUEST_LATENT_REPLAY: TraceEventType.REPLAY_REQUESTED,
    SynthesisType.REQUEST_AUTO_REGENERATION: TraceEventType.REPAIR_REQUESTED,
    SynthesisType.REQUEST_MEMORY_CONSOLIDATION:
        TraceEventType.REPAIR_REQUESTED,
}


@dataclass
class LogosComplexityEngine:
    """Coordinator: scan fracture -> propose synthesis -> resolve -> regulate.

    A tension engine, never an authority: it records tensions, proposes
    bounded resolutions, preserves what should stay unresolved, regulates
    complexity, and raises Esc instability signals -- all under the same
    safety/governance gates as the rest of the stack.
    """

    state_dir: Any = None
    fracture: FractureDetector = field(default_factory=FractureDetector)
    synthesis: Optional[SynthesisEngine] = None
    regulator: ComplexityRegulator = field(default_factory=ComplexityRegulator)
    policy: ResolutionPolicy = field(default_factory=ResolutionPolicy)
    esc: EscProcess = field(default_factory=EscProcess)
    safety: LogosComplexitySafetyValidator = field(
        default_factory=LogosComplexitySafetyValidator)
    opposition_memory: Optional[OppositionMemory] = None
    dialectical_trace: Optional[DialecticalTrace] = None
    # Optional safe subsystems.
    hypothesis_engine: Any = None
    active_perception: Any = None
    latent: Any = None
    autoregeneration: Any = None
    world_model: Any = None
    symbol_registry: Any = None
    governance: Any = None
    max_resolutions_per_tick: int = 4
    enabled: bool = True

    _prev_band: Optional[str] = field(default=None, init=False)
    _growth_deltas: List[float] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.opposition_memory is None:
            self.opposition_memory = OppositionMemory(state_dir=self.state_dir)
        if self.dialectical_trace is None:
            self.dialectical_trace = DialecticalTrace(state_dir=self.state_dir)
        if self.synthesis is None:
            self.synthesis = SynthesisEngine(
                safety=self.safety, hypothesis_engine=self.hypothesis_engine,
                active_perception=self.active_perception, latent=self.latent,
                autoregeneration=self.autoregeneration,
                world_model=self.world_model,
                symbol_registry=self.symbol_registry)

    # -- the loop -----------------------------------------------------------------

    def tick(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """One fracture-scan -> synthesis-propose -> resolve -> regulate."""
        if not self.enabled:
            return {"enabled": False}
        ctx = dict(context or {})
        # 1. Detect fractures (non-mutating).
        tensions = self.fracture.scan(ctx)
        ranked = sorted(
            tensions, key=lambda t: TensionSeverity.ORDER.get(t.severity, 0),
            reverse=True)
        for tension in ranked:
            if not self.safety.validate_tension(tension, ctx).safe:
                tension.set_status(TensionStatus.UNRESOLVED)
            self.opposition_memory.record_tension(tension)
            self.dialectical_trace.record(
                TraceEventType.TENSION_DETECTED, tension.tension_id,
                f"{tension.tension_type}: {tension.polarity_a} vs "
                f"{tension.polarity_b}")

        # 2. Complexity regulation.
        ctx["unresolved_tension_count"] = len(
            self.opposition_memory.unresolved())
        complexity = self.regulator.estimate(ctx)
        if self._prev_band is not None and complexity.band != self._prev_band:
            self.dialectical_trace.record(
                TraceEventType.COMPLEXITY_SHIFT, "",
                f"{self._prev_band} -> {complexity.band}")
        self._prev_band = complexity.band

        # 3. Resolve a bounded number of tensions.
        results = []
        for tension in ranked[:self.max_resolutions_per_tick]:
            candidates = self.synthesis.propose(tension, ctx)
            self.dialectical_trace.record(
                TraceEventType.SYNTHESIS_PROPOSED, tension.tension_id,
                f"{len(candidates)} candidate(s)")
            decision = self.policy.decide(tension, candidates, ctx)
            result = self._resolve(tension, decision, ctx)
            if result is not None:
                results.append(result)

        # 4. Esc instability signal.
        ctx["complexity"] = {"band": complexity.band}
        ctx["unresolved_high_severity_count"] = sum(
            1 for t in self.opposition_memory.unresolved()
            if t.severity == TensionSeverity.HIGH)
        esc = self.esc.evaluate(ctx)
        if esc.triggered:
            self.dialectical_trace.record(
                TraceEventType.ESC_TRIGGERED, "",
                f"triggers: {esc.triggers}")

        # 5. Track structural change delta.
        if "structural_change_score" in ctx:
            self._growth_deltas.append(
                float(ctx.get("structural_change_score", 0.0) or 0.0))
            self._growth_deltas = self._growth_deltas[-50:]

        self.opposition_memory.save_state()
        return {"tensions": len(tensions),
                "complexity_band": complexity.band,
                "resolved": len(results),
                "esc_triggered": esc.triggered}

    def _resolve(self, tension: LogosTension, decision: ResolutionDecision,
                 ctx: Dict[str, Any]) -> Optional[SynthesisResult]:
        candidate = decision.candidate
        if decision.preserve and (candidate is None
                                  or not decision.apply_allowed):
            tension.set_status(TensionStatus.PRESERVED)
            self.opposition_memory.record_status(tension, decision.reason)
            self.dialectical_trace.record(
                TraceEventType.TENSION_PRESERVED, tension.tension_id,
                decision.reason)
            return None
        if candidate is None:
            return None
        if not decision.apply_allowed:
            # Proposed but not applied (e.g., needs governance) -> preserved.
            tension.set_status(TensionStatus.PRESERVED)
            self.opposition_memory.record_status(tension, decision.reason)
            return None
        result = self.synthesis.apply_if_allowed(candidate, ctx)
        self.opposition_memory.record_synthesis_result(result)
        if result.refused:
            self.dialectical_trace.record(
                TraceEventType.SYNTHESIS_REFUSED, tension.tension_id,
                result.refused_reason)
            tension.set_status(TensionStatus.UNRESOLVED)
        elif result.applied:
            tension.set_status(result.new_tension_status)
            event = _TRACE_FOR_SYNTHESIS.get(
                candidate.synthesis_type, TraceEventType.SYNTHESIS_APPLIED)
            self.dialectical_trace.record(event, tension.tension_id,
                                         candidate.synthesis_type)
        self.opposition_memory.record_status(tension, result.result_class)
        return result

    # -- views --------------------------------------------------------------------

    def tension_to_growth_delta(self) -> Optional[float]:
        if len(self._growth_deltas) < 2:
            return None
        return round(self._growth_deltas[-1] - self._growth_deltas[0], 4)

    def latest_tension(self) -> Optional[str]:
        if not self.fracture.last_tensions:
            return None
        return self.fracture.last_tensions[0].tension_type

    def summary(self) -> Dict[str, Any]:
        opp = self.opposition_memory.snapshot()
        complexity = self.regulator.snapshot()
        esc = self.esc.snapshot()
        esc_state = esc.get("last_state") or {}
        return {
            "enabled": self.enabled,
            "complexity_band": complexity.get("band"),
            "complexity_pressure": (
                (self.regulator.last_state.pressure.score
                 if self.regulator.last_state else 0.0)),
            "active_tension_count": opp.get("tension_count", 0),
            "unresolved_tension_count": opp.get("unresolved_count", 0),
            "preserved_tension_count": opp.get("preserved_count", 0),
            "latest_tension": self.latest_tension(),
            "latest_synthesis_candidate": (
                self.synthesis.snapshot().get("proposed_total")),
            "applied_synthesis_count": self.synthesis.applied_total,
            "esc_triggered": bool(esc_state.get("triggered")),
            "esc_trigger_count": esc.get("trigger_count", 0),
            "logos_report_path": getattr(self, "report_path", None),
            "tension_to_growth_delta": self.tension_to_growth_delta(),
            "authority": False,
            "note": "LOGOS is a tension engine, not an authority; it "
                    "proposes bounded resolution, it does not decide truth",
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "fracture": self.fracture.snapshot(),
            "synthesis": self.synthesis.snapshot(),
            "complexity": self.regulator.snapshot(),
            "policy": self.policy.snapshot(),
            "opposition_memory": self.opposition_memory.snapshot(),
            "esc": self.esc.snapshot(),
            "dialectical_trace": self.dialectical_trace.snapshot(),
            "safety": self.safety.snapshot(),
            "tension_to_growth_delta": self.tension_to_growth_delta(),
            "summary": self.summary(),
        }
