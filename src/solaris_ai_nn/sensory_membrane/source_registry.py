"""Sensory source registry -- register, validate, and track read-only sources.

The :class:`SensorySourceRegistry` registers sources, validates their
read-only contracts and paths, tracks status and health, exposes a topology,
and persists the registry and a health log. A source that fails read-only
validation is never marked active.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .read_only_contract import ReadOnlyContractValidator
from .sources import (
    SensorySource,
    SensorySourceConfig,
    SensorySourceStatus,
)


@dataclass
class SensorySourceRegistry:
    """Holds and persists the membrane's read-only sources."""

    state_dir: Optional[str] = None
    allowed_roots: List[str] = field(default_factory=list)
    validator: ReadOnlyContractValidator = field(
        default_factory=ReadOnlyContractValidator)
    sources: Dict[str, SensorySource] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.registry_path = (
            os.path.join(self.state_dir, "sensory_sources.json")
            if self.state_dir else None)
        self.health_path = (
            os.path.join(self.state_dir, "sensory_source_health.jsonl")
            if self.state_dir else None)

    # -- registration -----------------------------------------------------------

    def register(self, config: SensorySourceConfig,
                 ) -> "tuple[Optional[SensorySource], List[str]]":
        """Register a source after read-only validation; returns (source, errs)."""
        errors: List[str] = []
        cfg_violations = self.validator.validate_source_config(config)
        errors += [v.rule for v in cfg_violations]
        if config.path:
            path_violations = self.validator.validate_path(
                config.path, self.allowed_roots)
            errors += [v.rule for v in path_violations]
        if errors:
            self._log_health(config.source_id, "rejected", errors)
            return None, errors
        source = SensorySource(config=config, read_only_validated=True,
                               status=(SensorySourceStatus.REGISTERED
                                       if config.enabled
                                       else SensorySourceStatus.DISABLED))
        self.sources[config.source_id] = source
        self._log_health(config.source_id, source.status, [])
        self._persist()
        return source, []

    def disable(self, source_id: str) -> None:
        source = self.sources.get(source_id)
        if source is not None:
            source.status = SensorySourceStatus.DISABLED
            self._log_health(source_id, source.status, [])
            self._persist()

    def mark_status(self, source_id: str, status: str,
                    detail: str = "") -> None:
        source = self.sources.get(source_id)
        if source is not None and status in SensorySourceStatus.ALL:
            source.status = status
            if detail:
                source.last_error = detail
            self._log_health(source_id, status, [detail] if detail else [])

    def get(self, source_id: str) -> Optional[SensorySource]:
        return self.sources.get(source_id)

    def enabled_sources(self) -> List[SensorySource]:
        return [s for s in self.sources.values()
                if s.config.enabled
                and s.status != SensorySourceStatus.DISABLED]

    def healthy_count(self) -> int:
        return sum(1 for s in self.sources.values() if s.healthy)

    def degraded_count(self) -> int:
        return sum(1 for s in self.sources.values()
                   if s.status in (SensorySourceStatus.DEGRADED,
                                   SensorySourceStatus.QUARANTINED,
                                   SensorySourceStatus.MISSING))

    # -- topology / persistence -------------------------------------------------

    def topology(self) -> Dict[str, Any]:
        return {
            "nodes": [{"source_id": s.source_id,
                       "type": s.config.source_type,
                       "status": s.status,
                       "simulated": s.config.is_simulated}
                      for s in self.sources.values()],
            "allowed_roots": list(self.allowed_roots),
        }

    def _persist(self) -> None:
        if not self.registry_path:
            return
        os.makedirs(os.path.dirname(self.registry_path) or ".", exist_ok=True)
        data = {"allowed_roots": list(self.allowed_roots),
                "sources": {sid: s.to_dict()
                            for sid, s in self.sources.items()}}
        with open(self.registry_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)

    def _log_health(self, source_id: str, status: str,
                    errors: List[str]) -> None:
        if not self.health_path:
            return
        os.makedirs(os.path.dirname(self.health_path) or ".", exist_ok=True)
        with open(self.health_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"source_id": source_id, "status": status,
                                 "errors": errors, "timestamp": time.time()},
                                default=str) + "\n")

    def snapshot(self) -> Dict[str, Any]:
        return {
            "source_count": len(self.sources),
            "enabled_count": len(self.enabled_sources()),
            "healthy_count": self.healthy_count(),
            "degraded_count": self.degraded_count(),
            "sources": {sid: s.to_dict() for sid, s in self.sources.items()},
        }
