"""Sensory membrane runtime -- poll read-only sources into canonical stimuli.

The :class:`SensoryMembraneRuntime` ties the membrane together: it loads the
source registry, validates read-only contracts, initializes adapters, polls
sources (bounded), normalizes events, buffers them, optionally publishes them
to a ConscienceBus, updates the provenance ledger and grounding engine, and
produces a snapshot for reports and the Inner MAP.

Disabled by default. Real read-only sources require explicit config/governance.
Dry-run validates and reports without publishing stimuli. No unbounded polling.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .adapters import SensoryAdapter
from .event_normalizer import SensoryEventNormalizer
from .folder_watch import FolderPollAdapter
from .grounding import SensoryGroundingEngine
from .jsonl_stream import JSONLStreamAdapter
from .numeric_stream import NumericStreamAdapter
from .provenance import ProvenanceLedger
from .read_only_contract import ReadOnlyContractValidator
from .safety import SensoryMembraneSafetyValidator
from .sensory_buffer import SensoryBuffer
from .source_registry import SensorySourceRegistry
from .sources import SensorySourceConfig, SensorySourceStatus, SensorySourceType
from .text_stream import TextStreamAdapter

_ADAPTERS = {
    SensorySourceType.JSONL_FILE: JSONLStreamAdapter,
    SensorySourceType.EVENT_LOG: JSONLStreamAdapter,
    SensorySourceType.TEXT_FILE: TextStreamAdapter,
    SensorySourceType.NUMERIC_CSV: NumericStreamAdapter,
    SensorySourceType.SYNTHETIC_SENSOR: NumericStreamAdapter,
    SensorySourceType.FOLDER_POLL: FolderPollAdapter,
    SensorySourceType.FOLDER_SNAPSHOT: FolderPollAdapter,
}


@dataclass
class SensoryMembraneRuntime:
    """Bounded, read-only runtime that turns sources into canonical stimuli."""

    state_dir: Optional[str] = None
    allowed_input_roots: List[str] = field(default_factory=list)
    poll_interval_s: float = 5.0
    max_events_per_poll: int = 100
    max_total_events: int = 5000
    dry_run: bool = False
    enabled: bool = False
    simulated_sources_only: bool = True
    real_read_only_sources_enabled: bool = False
    bus: Any = None
    bus_topic: str = "stimulus"

    def __post_init__(self) -> None:
        self.contract = ReadOnlyContractValidator()
        self.safety = SensoryMembraneSafetyValidator()
        self.registry = SensorySourceRegistry(
            state_dir=self.state_dir,
            allowed_roots=self.allowed_input_roots,
            validator=self.contract)
        self.normalizer = SensoryEventNormalizer()
        self.buffer = SensoryBuffer(state_dir=self.state_dir)
        self.grounding = SensoryGroundingEngine()
        self.provenance = ProvenanceLedger(state_dir=self.state_dir)
        self._adapters: Dict[str, SensoryAdapter] = {}
        self.total_events = 0
        self.malformed_events = 0
        self.absence_events = 0
        self.read_only_violation_count = 0
        self.published_events = 0
        self.poll_count = 0
        self._started_at = time.time()

    # -- configuration ----------------------------------------------------------

    def add_source(self, config: SensorySourceConfig,
                   ) -> "tuple[bool, List[str]]":
        """Register a source, enforcing simulated/real gating."""
        if config.is_real_read_only and not self.real_read_only_sources_enabled:
            self.registry.mark_status(config.source_id,
                                      SensorySourceStatus.DISABLED,
                                      "real read-only sources not enabled")
            return False, ["real read-only sources require explicit enablement"]
        source, errors = self.registry.register(config)
        if source is None:
            self.read_only_violation_count += len(errors)
            return False, errors
        if source.status != SensorySourceStatus.DISABLED:
            adapter_cls = _ADAPTERS.get(config.source_type)
            if adapter_cls is not None:
                self._adapters[config.source_id] = adapter_cls(config)
        return True, []

    def initialize(self) -> Dict[str, Any]:
        """Build adapters for enabled, validated sources already registered."""
        for source in self.registry.enabled_sources():
            if source.source_id in self._adapters:
                continue
            adapter_cls = _ADAPTERS.get(source.config.source_type)
            if adapter_cls is not None:
                self._adapters[source.source_id] = adapter_cls(source.config)
        return {"enabled": self.enabled, "dry_run": self.dry_run,
                "source_count": len(self.registry.sources),
                "adapter_count": len(self._adapters)}

    # -- polling ----------------------------------------------------------------

    def poll_once(self) -> Dict[str, Any]:
        """Poll every enabled adapter once (bounded); normalize and buffer."""
        if not self.enabled:
            return {"polled": False, "reason": "membrane disabled"}
        if self.total_events >= self.max_total_events:
            return {"polled": False, "reason": "max_total_events reached"}
        self.poll_count += 1
        admitted = 0
        for source in self.registry.enabled_sources():
            adapter = self._adapters.get(source.source_id)
            if adapter is None:
                continue
            result = adapter.poll()
            source.last_poll_at = time.time()
            source.read_error_count += result.read_errors
            source.malformed_count += result.malformed
            self.malformed_events += result.malformed
            if result.read_errors and not result.events:
                self.registry.mark_status(
                    source.source_id, SensorySourceStatus.DEGRADED,
                    result.note or "read error")
            elif result.events:
                self.registry.mark_status(source.source_id,
                                          SensorySourceStatus.ACTIVE)
            for raw in result.events:
                prov = self.provenance.record_for(
                    event_hash=raw.event_hash, source_id=raw.source_id,
                    source_type=raw.source_type, adapter_name=adapter.name,
                    path=source.config.path, raw_line=raw.raw_line,
                    read_only_validated=source.read_only_validated,
                    is_simulated=raw.is_simulated,
                    trust_level=raw.trust_level,
                    limitations=(["malformed"] if raw.malformed else []))
                normalized = self.normalizer.normalize(
                    raw, provenance_refs=[prov.event_hash])
                if normalized.is_absence:
                    self.absence_events += 1
                source.event_count += 1
                self.total_events += 1
                self.grounding.ground(normalized)
                if not self.dry_run:
                    if self.buffer.admit(normalized):
                        admitted += 1
                if self.total_events >= self.max_total_events:
                    break
        published = 0 if self.dry_run else self._publish()
        return {"polled": True, "admitted": admitted, "published": published,
                "dry_run": self.dry_run}

    def run_bounded(self, max_polls: int = 5) -> Dict[str, Any]:
        """Run a bounded number of polls (never unbounded)."""
        if not self.enabled:
            return {"ran": False, "reason": "membrane disabled"}
        polls = 0
        for _ in range(max(0, int(max_polls))):
            out = self.poll_once()
            if not out.get("polled"):
                break
            polls += 1
        return {"ran": True, "polls": polls,
                "total_events": self.total_events,
                "published": self.published_events, "dry_run": self.dry_run}

    def _publish(self) -> int:
        """Emit a buffered batch to the ConscienceBus (Stimulus topic)."""
        if self.bus is None:
            # Still drain the batch so the buffer does not grow unbounded.
            return len(self.buffer.emit_batch())
        batch = self.buffer.emit_batch()
        for event in batch:
            stim = event.get("event", event)
            try:
                self.bus.publish(self.bus_topic, "sensory_membrane",
                                 {"source_id": stim.get("source_id"),
                                  "modality": stim.get("modality"),
                                  "is_absence": stim.get("is_absence"),
                                  "origin": "read_only_environmental_input"},
                                 step=self.poll_count)
                self.published_events += 1
            except Exception:
                continue
        return len(batch)

    # -- views ------------------------------------------------------------------

    def events_per_minute(self) -> float:
        elapsed = max(1e-9, time.time() - self._started_at)
        return round(self.total_events / (elapsed / 60.0), 4)

    def summary(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "dry_run": self.dry_run,
            "simulated_sources_only": self.simulated_sources_only,
            "real_read_only_sources_enabled":
                self.real_read_only_sources_enabled,
            "source_count": len(self.registry.sources),
            "active_source_count": len(self.registry.enabled_sources()),
            "healthy_source_count": self.registry.healthy_count(),
            "degraded_source_count": self.registry.degraded_count(),
            "total_events": self.total_events,
            "malformed_events": self.malformed_events,
            "absence_events": self.absence_events,
            "dropped_events": self.buffer.dropped_count,
            "published_events": self.published_events,
            "events_per_minute": self.events_per_minute(),
            "read_only_violation_count": self.read_only_violation_count,
            "provenance_completeness": self.provenance.completeness(
                self.total_events),
            "read_only": True,
            "membrane_report_path": getattr(self, "report_path", None),
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "summary": self.summary(),
            "registry": self.registry.snapshot(),
            "buffer": self.buffer.snapshot(),
            "grounding": self.grounding.snapshot(),
            "provenance": self.provenance.snapshot(),
            "safety": self.safety.snapshot(),
            "read_only_contract": self.contract.snapshot(),
        }
