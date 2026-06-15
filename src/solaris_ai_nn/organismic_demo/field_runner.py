"""Minimal field organism runner -- the first observable organismic demo.

:class:`MinimalFieldOrganismRunner` generates fixture feeders, drives the Prompt
41 :class:`PluralSensoriumRuntime` over a bounded continuous-flux scenario, reads
the feeders through the same read-only adapter path, collects an observation
trace, and runs a changed-perception probe. World/feeder generation, Solaris's
perception, and debug evaluation are kept strictly separate. It never loops
unbounded, modifies a source during perception, or touches hardware/network/shell.
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..plural_sensorium import PluralSensoriumRuntime
from ..plural_sensorium.receptors import event_intensity
from ..plural_sensorium.stream_adapters import read_feeder
from .fixture_feeders import FixtureFeederSet, write_fixtures
from .observation_trace import ObservationTrace, TraceEventType
from .perception_change import PerceptionChangeProbe, PerceptionChangeResult
from .safety import OrganismicDemoSafetyValidator
from .scenario import OrganismicDemoConfig, OrganismicDemoScenario


@dataclass
class MinimalFieldOrganismRunner:
    """Runs the bounded minimal-field-organism scenario, end to end."""

    state_dir: str = ".solaris_ai_nn_state/organismic_demo"
    config: OrganismicDemoConfig = field(default_factory=OrganismicDemoConfig)
    enabled_modalities: Optional[List[str]] = None
    governance: Any = None

    run_id: str = field(
        default_factory=lambda: f"OFD_{uuid.uuid4().hex[:10]}")
    runtime: Optional[PluralSensoriumRuntime] = None
    trace: ObservationTrace = field(default_factory=ObservationTrace)
    safety: OrganismicDemoSafetyValidator = field(
        default_factory=OrganismicDemoSafetyValidator)
    fixtures: Optional[FixtureFeederSet] = None
    modality_responses: Dict[str, List[Dict[str, Any]]] = field(
        default_factory=lambda: defaultdict(list), init=False)
    probe_result: Optional[PerceptionChangeResult] = None
    refusal_reasons: List[str] = field(default_factory=list, init=False)
    ticks_run: int = field(default=0, init=False)
    _prepared: bool = field(default=False, init=False)
    _started_at: float = field(default=0.0, init=False)

    # -- preparation ----------------------------------------------------------

    def prepare(self) -> bool:
        """Generate fixtures and build the read-only plural-sensorium runtime."""
        bounded = self.safety.validate_runtime_bounded(
            self.config.ticks, self.config.max_runtime_s,
            self.config.max_events_total)
        if not bounded.safe:
            self.refusal_reasons.extend(bounded.violations)
            return False

        scenario = OrganismicDemoScenario(config=self.config)
        self.fixtures = write_fixtures(scenario, self.state_dir)

        # The debug-truth file must never enter the sensory roots.
        feeder_paths = [f.path for f in self.fixtures.feeders]
        leak = self.safety.validate_no_debug_leakage(feeder_paths)
        if not leak.safe:
            self.refusal_reasons.extend(leak.violations)
            self.trace.record(TraceEventType.SAFETY_BLOCK,
                              detail="debug-truth leakage blocked")
            return False

        self.runtime = PluralSensoriumRuntime(
            state_dir=self.state_dir,
            input_roots=[self.fixtures.fixtures_dir],
            enabled_modalities=self.enabled_modalities,
            max_events_total=self.config.max_events_total,
            max_runtime_s=self.config.max_runtime_s,
            fixture_mode=self.config.fixture_mode,
            real_read_only_mode=self.config.real_read_only_mode,
            governance=self.governance)
        for feeder in self.fixtures.feeders:
            self.runtime.add_feeder(feeder)
        self._prepared = True
        return True

    # -- running --------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        if not self._prepared and not self.prepare():
            return {"refused": True, "reasons": list(self.refusal_reasons)}

        # Read every feeder ONCE through the read-only adapter path, then group
        # the resulting envelopes by tick for a continuous, in-order replay.
        by_tick: Dict[int, List[Any]] = defaultdict(list)
        for feeder in self.runtime.feeders:
            result = read_feeder(feeder, max_lines=self.config.max_events_total)
            for env in result.events:
                by_tick[int(env.timestamp)].append(env)

        self._started_at = time.time()
        total = 0
        for tick in range(self.config.ticks):
            if time.time() - self._started_at > self.config.max_runtime_s:
                break
            if total >= self.config.max_events_total:
                break
            remaining = self.config.max_events_total - total
            consumed = self.run_tick(tick, by_tick.get(tick, [])[:remaining])
            total += consumed
            self.ticks_run += 1

        self.run_changed_perception_probe()
        return {"refused": False, "ticks_run": self.ticks_run,
                "events_ingested": self.runtime.events_ingested,
                "run_id": self.run_id}

    def run_tick(self, tick: int, envelopes: List[Any]) -> int:
        fired: List[str] = []
        for env in envelopes:
            before = self._receptor_snapshot(env)
            self.runtime.observe_envelope(env, now=float(tick))
            fired.append(env.source_id)
            self.trace.record(
                TraceEventType.EXTERNAL_EVENT_SEEN, tick=tick,
                modality=env.modality, source_id=env.source_id,
                event_refs=[env.event_id], provenance=dict(env.provenance))
            rid = f"{env.source_id}:{env.modality}"
            receptor = self.runtime.receptors.get(rid)
            if receptor is not None:
                self.trace.record(
                    TraceEventType.RECEPTOR_UPDATED, tick=tick,
                    modality=env.modality, source_id=env.source_id,
                    before=before, after=receptor.state().to_dict())
                self.modality_responses[env.modality].append({
                    "tick": tick, "novelty": receptor.recent_novelty,
                    "sensitivity": receptor.sensitivity.value,
                    "intensity": receptor.recent_intensity,
                    "baseline": receptor.baseline})

        before_shifts = len(self.runtime.baseline_shifts)
        before_abs = len(self.runtime.absence.events)
        before_inv = len(self.runtime.invariants.candidates)
        before_xm = self.runtime.cross_modal.relation_count()
        before_proto = len(self.runtime.proto_symbol_candidates)

        self.runtime.advance_tick(fired, now=float(tick))

        self._trace_new(tick, TraceEventType.BASELINE_SHIFT_DETECTED,
                        before_shifts, self.runtime.baseline_shifts)
        self._trace_new(tick, TraceEventType.ABSENCE_DETECTED,
                        before_abs, self.runtime.absence.events)
        if len(self.runtime.invariants.candidates) > before_inv:
            self.trace.record(TraceEventType.INVARIANT_CANDIDATE_CREATED,
                              tick=tick)
        if self.runtime.cross_modal.relation_count() > before_xm:
            self.trace.record(TraceEventType.CROSS_MODAL_RELATION_CREATED,
                              tick=tick)
        if len(self.runtime.proto_symbol_candidates) > before_proto:
            self.trace.record(TraceEventType.PROTO_SYMBOL_CANDIDATE_CREATED,
                              tick=tick)
        self.trace.record(TraceEventType.FIELD_PRESSURE_CHANGED, tick=tick,
                          after=self.runtime.sensory_field.to_dict()
                          ["pressures"])
        return len(envelopes)

    def _trace_new(self, tick: int, event_type: str, before_count: int,
                   collection: List[Any]) -> None:
        for item in collection[before_count:]:
            data = item if isinstance(item, dict) else item.to_dict()
            self.trace.record(event_type, tick=tick,
                              modality=data.get("modality"),
                              source_id=data.get("source_id"),
                              provenance=data.get("provenance", {}))

    def _receptor_snapshot(self, env: Any) -> Optional[Dict[str, Any]]:
        receptor = self.runtime.receptors.get(f"{env.source_id}:{env.modality}")
        return receptor.state().to_dict() if receptor is not None else None

    def run_changed_perception_probe(self) -> PerceptionChangeResult:
        self.probe_result = PerceptionChangeProbe().compute(
            dict(self.modality_responses), self.runtime)
        self.trace.record(
            TraceEventType.CHANGED_PERCEPTION_PROBE_RESULT,
            detail=f"changed={self.probe_result.changed} "
                   f"score={self.probe_result.changed_perception_score}",
            limitations=["evidence of changed response structure only; not "
                         "consciousness/understanding/sentience"])
        return self.probe_result

    # -- status / artifacts ---------------------------------------------------

    def demo_status(self) -> Dict[str, Any]:
        rt = self.runtime
        score = (self.probe_result.changed_perception_score
                 if self.probe_result else 0.0)
        negatives = (1 if self.probe_result and not self.probe_result.changed
                     else 0)
        return {
            "organismic_demo_enabled": True,
            "latest_demo_run_id": self.run_id,
            "active_feeder_count": len(rt.feeders) if rt else 0,
            "active_receptor_count": (
                sum(1 for r in rt.receptors.values() if r.event_count > 0)
                if rt else 0),
            "active_modality_count": len(rt.active_modalities()) if rt else 0,
            "changed_perception_score": score,
            "cross_modal_relation_count": (
                rt.cross_modal.relation_count() if rt else 0),
            "proto_symbol_candidate_count": (
                len(rt.proto_symbol_candidates) if rt else 0),
            "baseline_shift_count": len(rt.baseline_shifts) if rt else 0,
            "absence_event_count": len(rt.absence.events) if rt else 0,
            "rhythm_signature_count": (
                len(rt.rhythm.signatures) if rt else 0),
            "invariant_candidate_count": (
                len(rt.invariants.candidates) if rt else 0),
            "attention_shift_count": (
                rt.attention.state.shifts if rt else 0),
            "human_label_contamination_score": (
                rt.human_label_contamination_score() if rt else 0.0),
            "latest_negative_result_count": negatives,
            "safety_block_count": self.safety.rejected_count
            + self.trace.count(TraceEventType.SAFETY_BLOCK),
            "latest_report_path": self.metadata_report_path(),
        }

    def metadata_report_path(self) -> Optional[str]:
        import os

        path = os.path.join(self.state_dir, "MINIMAL_FIELD_ORGANISM_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.demo_status()

    def write_artifacts(self) -> Dict[str, Any]:
        from .demo_report import MinimalFieldOrganismDemoReportBuilder

        return MinimalFieldOrganismDemoReportBuilder(self).write()
