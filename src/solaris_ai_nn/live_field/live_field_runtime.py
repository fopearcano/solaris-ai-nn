"""Live field runtime -- the real read-only feeder integration layer.

:class:`LiveFieldRuntime` loads the feeder registry, validates feeder outputs,
polls the external dropbox, reads event envelopes, and passes them into the
Prompt-41 :class:`PluralSensoriumRuntime` tick by tick. It tracks source health
(silence becomes perceptual absence; corruption becomes an evidence issue),
collects a trace, and stays bounded. Live mode requires governance approval; the
runtime starts no feeders, accesses no hardware/network, runs no shell, and never
mutates a source.
"""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..plural_sensorium import PluralSensoriumRuntime
from ..plural_sensorium.receptors import event_intensity
from .external_dropbox import FeatureDropbox, FeatureDropboxIngestor
from .feeder_contract import LiveFeederContract, LiveFeederEnvelope
from .feeder_registry import LiveFeederRegistry
from .live_field_trace import LiveFieldTrace, LiveFieldTraceEventType
from .safety import LiveFieldSafetyValidator
from .source_health import SourceHealthMonitor


@dataclass
class LiveFieldRuntime:
    """Bounded, read-only ingestion of live feeder envelopes (disabled default)."""

    state_dir: str = ".solaris_ai_nn_live"
    live_root: str = ".solaris_ai_nn_live"
    registry_path: Optional[str] = None
    max_runtime_s: float = 60.0
    max_ticks: int = 120
    poll_interval_s: float = 0.0
    max_events_per_tick: int = 200
    max_events_total: int = 2000
    enabled_feeders: Optional[List[str]] = None
    fixture_fallback: bool = True
    dry_run: bool = False
    require_governance_for_live: bool = True
    governance: Any = None

    registry: Optional[LiveFeederRegistry] = None
    sensorium: Optional[PluralSensoriumRuntime] = None
    health: SourceHealthMonitor = field(default_factory=SourceHealthMonitor)
    trace: LiveFieldTrace = field(default_factory=LiveFieldTrace)
    safety: LiveFieldSafetyValidator = field(
        default_factory=LiveFieldSafetyValidator)
    contract: LiveFeederContract = field(default_factory=LiveFeederContract)
    modality_responses: Dict[str, List[Dict[str, Any]]] = field(
        default_factory=lambda: defaultdict(list), init=False)
    refusal_reasons: List[str] = field(default_factory=list, init=False)
    ticks_run: int = field(default=0, init=False)
    live_mode: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.registry is None:
            self.registry = LiveFeederRegistry.load(self.live_root)
        self.sensorium = PluralSensoriumRuntime(
            state_dir=self.state_dir,
            max_events_total=self.max_events_total,
            max_runtime_s=self.max_runtime_s)

    # -- preflight ------------------------------------------------------------

    def preflight(self) -> Dict[str, Any]:
        """Validate registry/feeders and report what is present (no run)."""
        from .local_feeders import (
            FeatureDropboxFeederValidator,
            ManualLogFeederValidator,
        )

        feeders = self.registry.enabled_feeders()
        present = []
        missing = []
        for feeder in feeders:
            if feeder.output_path and os.path.isfile(feeder.output_path):
                present.append(feeder.feeder_id)
                self.trace.record(LiveFieldTraceEventType.FEEDER_SEEN,
                                  feeder_id=feeder.feeder_id,
                                  source_id=feeder.source_id,
                                  modality=feeder.modality)
            else:
                missing.append(feeder.feeder_id)
                self.trace.record(LiveFieldTraceEventType.FEEDER_MISSING,
                                  feeder_id=feeder.feeder_id,
                                  detail=f"missing output: {feeder.output_path}")
        return {
            "feeder_count": len(feeders),
            "present": present, "missing": missing,
            "requires_governance": self.registry.requires_governance(),
            "fixture_fallback_available": self.fixture_fallback,
            "live_mode_allowed": self._governance_ok(),
        }

    # -- running --------------------------------------------------------------

    def run(self, *, live: bool = False,
            governance_approved: bool = False) -> Dict[str, Any]:
        """Run a bounded read-only ingestion. Live mode needs governance."""
        bounded = self.safety.validate_polling_bounded(
            self.max_runtime_s, self.max_ticks, self.max_events_total)
        if not bounded.safe:
            return self._refuse(bounded.violations)

        live_report = self.safety.validate_live_mode(
            live_requested=live,
            governance_approved=governance_approved or self._governance_ok())
        if not live_report.safe:
            self.trace.record(LiveFieldTraceEventType.SAFETY_BLOCK,
                              detail="live mode requires governance approval")
            return self._refuse(live_report.violations)
        self.live_mode = bool(live)

        envelopes = self._collect_envelopes()
        if not envelopes and not self.fixture_fallback:
            return {"refused": False, "ticks_run": 0, "events_ingested": 0,
                    "note": "no feeder envelopes and fixture fallback disabled"}

        by_tick: Dict[int, List[LiveFeederEnvelope]] = defaultdict(list)
        for env in envelopes:
            by_tick[int(env.timestamp)].append(env)
        ticks = sorted(by_tick) or [0]

        started = time.time()
        total = 0
        for n, tick in enumerate(ticks):
            if n >= self.max_ticks:
                break
            if time.time() - started > self.max_runtime_s:
                break
            if total >= self.max_events_total:
                break
            total += self._run_tick(tick, by_tick.get(tick, [])[
                :self.max_events_per_tick])
            self.ticks_run += 1
        # Final silence sweep.
        for ev in self.health.check_silence(time.time()):
            self.trace.record(LiveFieldTraceEventType.SOURCE_HEALTH_CHANGED,
                              source_id=ev.source_id, source_health=ev.new_state)
        return {"refused": False, "ticks_run": self.ticks_run,
                "events_ingested": self.sensorium.events_ingested,
                "live_mode": self.live_mode}

    def _run_tick(self, tick: int, envelopes: List[LiveFeederEnvelope]) -> int:
        fired: List[str] = []
        for live_env in envelopes:
            self.health.observe_event(live_env.source_id, float(tick))
            env = live_env.to_sensory_envelope()
            self.trace.record(LiveFieldTraceEventType.EXTERNAL_EVENT_INGESTED,
                              tick=tick, source_id=env.source_id,
                              feeder_id=live_env.feeder_id,
                              modality=env.modality,
                              provenance=dict(env.provenance),
                              source_health=self.health.state_of(
                                  env.source_id))
            if not self.dry_run:
                self.sensorium.observe_envelope(env, now=float(tick))
            fired.append(env.source_id)
            rid = f"{env.source_id}:{env.modality}"
            receptor = self.sensorium.receptors.get(rid)
            if receptor is not None:
                self.trace.record(LiveFieldTraceEventType.RECEPTOR_UPDATED,
                                  tick=tick, source_id=env.source_id,
                                  modality=env.modality)
                self.modality_responses[env.modality].append({
                    "novelty": receptor.recent_novelty,
                    "sensitivity": receptor.sensitivity.value,
                    "baseline": receptor.baseline})
        before_abs = len(self.sensorium.absence.events)
        self.sensorium.advance_tick(fired, now=float(tick))
        self.trace.record(LiveFieldTraceEventType.SENSORY_FIELD_UPDATED,
                          tick=tick)
        for ev in self.health.check_silence(float(tick)):
            self.trace.record(LiveFieldTraceEventType.SOURCE_ABSENCE_DETECTED,
                              tick=tick, source_id=ev.source_id,
                              source_health=ev.new_state)
        if len(self.sensorium.absence.events) > before_abs:
            self.trace.record(LiveFieldTraceEventType.SOURCE_ABSENCE_DETECTED,
                              tick=tick)
        return len(envelopes)

    # -- envelope collection (read-only) --------------------------------------

    def _collect_envelopes(self) -> List[LiveFeederEnvelope]:
        envelopes: List[LiveFeederEnvelope] = []
        for feeder in self.registry.enabled_feeders():
            if self.enabled_feeders and feeder.feeder_id not in \
                    self.enabled_feeders:
                continue
            self.health.register(
                feeder.source_id,
                expected_silence_window_s=feeder.expected_silence_window_s,
                expected_rate=feeder.expected_event_rate)
            envelopes.extend(self._read_feeder_output(feeder))
        # External dropbox.
        ingestor = FeatureDropboxIngestor(
            dropbox=FeatureDropbox(live_root=self.live_root))
        poll = ingestor.poll(max_records=self.max_events_total)
        for path in poll.corrupt_files:
            self.trace.record(LiveFieldTraceEventType.ENVELOPE_INVALID,
                              detail=f"corrupt dropbox file: {path}")
        envelopes.extend(poll.envelopes)
        for env in envelopes:
            self.health.register(env.source_id)
        return sorted(envelopes, key=lambda e: e.timestamp)

    def _read_feeder_output(self, feeder: Any) -> List[LiveFeederEnvelope]:
        path = feeder.output_path
        out: List[LiveFeederEnvelope] = []
        if not path or not os.path.isfile(path):
            return out
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i >= self.max_events_total:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    self.health.observe_event(feeder.source_id, time.time(),
                                              corrupt=True)
                    self.trace.record(LiveFieldTraceEventType.ENVELOPE_INVALID,
                                      feeder_id=feeder.feeder_id,
                                      detail=f"bad json line {i}")
                    continue
                ok, _why = self.contract.validate_record(record)
                if not ok:
                    self.trace.record(LiveFieldTraceEventType.ENVELOPE_INVALID,
                                      feeder_id=feeder.feeder_id)
                    continue
                out.append(self.contract.build_envelope(
                    record, feeder_id=feeder.feeder_id, feeder_mode=feeder.mode,
                    source_id=feeder.source_id,
                    modality_hint=feeder.modality, trust_level=feeder.trust_level,
                    raw_ref=f"{path}:{i}"))
        return out

    # -- helpers --------------------------------------------------------------

    def _governance_ok(self) -> bool:
        if self.governance is None:
            return False
        try:
            return bool(self.governance.is_enabled(
                "enable_live_field_read_only_pilot"))
        except Exception:
            return False

    def _refuse(self, reasons: List[str]) -> Dict[str, Any]:
        self.refusal_reasons.extend(reasons)
        return {"refused": True, "reasons": list(self.refusal_reasons)}

    def live_field_status(self) -> Dict[str, Any]:
        rt = self.sensorium
        return {
            "live_field_enabled": True,
            "live_mode": self.live_mode,
            "live_mode_allowed": self._governance_ok(),
            "feeder_count": len(self.registry.feeders),
            "active_source_count": len(self.health.active_sources()),
            "silent_source_count": len(self.health.silent_sources()),
            "corrupt_source_count": len(self.health.corrupt_sources()),
            "active_modality_count": len(rt.active_modalities()),
            "live_field_pressure": rt.sensory_field.state().field_pressure,
            "live_absence_pressure": rt.sensory_field.state().absence_pressure,
            "live_baseline_shift_count": len(rt.baseline_shifts),
            "absence_event_count": len(rt.absence.events),
            "rhythm_signature_count": len(rt.rhythm.signatures),
            "invariant_candidate_count": len(rt.invariants.candidates),
            "cross_modal_relation_count": rt.cross_modal.relation_count(),
            "human_label_contamination_score":
                rt.human_label_contamination_score(),
            "safety_block_count": self.safety.rejected_count
            + self.trace.count(LiveFieldTraceEventType.SAFETY_BLOCK),
            "latest_live_field_report_path": self._report_path(),
        }

    def _report_path(self) -> Optional[str]:
        path = os.path.join(self.state_dir, "LIVE_FIELD_REPORT.md")
        return path if os.path.isfile(path) else None

    # -- feeder SDK integration (Prompt 45) -----------------------------------

    def feeder_sdk_output_validation(self, path: str) -> Dict[str, Any]:
        """Validate a feeder-SDK output JSONL file (read-only)."""
        from ..feeder_sdk import FeederOutputValidator

        return FeederOutputValidator().validate_file(path)

    def feeder_sdk_manifest(self) -> Dict[str, Any]:
        """Build the feeder pack manifest (starts no feeder)."""
        from ..feeder_sdk import FeederPackBuilder

        return FeederPackBuilder(state_dir=self.live_root).build().to_dict()

    def feeder_sdk_monitor_snapshot(self, paths: List[str]) -> Dict[str, Any]:
        """Monitor feeder-SDK output files (read-only)."""
        from ..feeder_sdk import FeederMonitor

        return FeederMonitor().monitor(paths).to_dict()

    def snapshot(self) -> Dict[str, Any]:
        return self.live_field_status()
