"""Ecology memory -- the record of the world the system actually lived in.

So that later reports can answer "what environment did Solaris-AI-NN
experience, which pressures were present, what changed, and what
responded?", this bounded store tracks regime/cycle/season history, event
counts by type, anomaly/scarcity/novelty/deprivation windows, delayed
consequence groups, and per-episode developmental response summaries.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EcologyEpisode:
    """One bounded slice of ecological history."""

    step_start: int
    step_end: int = 0
    regime: str = ""
    season: str = ""
    event_counts: Dict[str, int] = field(default_factory=dict)
    dominant_pressure: str = ""
    developmental_response: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class EcologyMemory:
    """Bounded history of the lived ecology."""

    max_episodes: int = 500
    max_window_records: int = 500
    event_counts: Dict[str, int] = field(default_factory=dict)
    regime_history: List[Dict[str, Any]] = field(default_factory=list)
    cycle_history: List[Dict[str, Any]] = field(default_factory=list)
    season_history: List[Dict[str, Any]] = field(default_factory=list)
    anomaly_windows: List[Dict[str, Any]] = field(default_factory=list)
    scarcity_windows: List[Dict[str, Any]] = field(default_factory=list)
    novelty_windows: List[Dict[str, Any]] = field(default_factory=list)
    deprivation_windows: List[Dict[str, Any]] = field(
        default_factory=list)
    delayed_groups: List[Dict[str, Any]] = field(default_factory=list)
    episodes: List[EcologyEpisode] = field(default_factory=list)

    # -- recording ----------------------------------------------------------------

    def record_event(self, event_type: str) -> None:
        self.event_counts[event_type] = (
            self.event_counts.get(event_type, 0) + 1)

    def record_regime(self, step: int, regime: str) -> None:
        self.regime_history.append({"step": step, "regime": regime})
        self.regime_history = self.regime_history[
            -self.max_window_records:]

    def record_season(self, step: int, season: str) -> None:
        self.season_history.append({"step": step, "season": season})
        self.season_history = self.season_history[
            -self.max_window_records:]

    def record_window(self, kind: str, record: Dict[str, Any]) -> None:
        bucket = {"anomaly": self.anomaly_windows,
                  "scarcity": self.scarcity_windows,
                  "novelty": self.novelty_windows,
                  "deprivation": self.deprivation_windows,
                  "delayed": self.delayed_groups}.get(kind)
        if bucket is None:
            return
        bucket.append({**record, "timestamp": time.time()})
        del bucket[:-self.max_window_records]

    def record_episode(self, episode: EcologyEpisode) -> None:
        self.episodes.append(episode)
        self.episodes = self.episodes[-self.max_episodes:]

    @property
    def over_budget(self) -> bool:
        return (len(self.episodes) > self.max_episodes
                or len(self.regime_history) > self.max_window_records)

    # -- views --------------------------------------------------------------------

    def total_events(self) -> int:
        return sum(self.event_counts.values())

    def snapshot(self) -> Dict[str, Any]:
        return {
            "total_events": self.total_events(),
            "event_counts": dict(self.event_counts),
            "regime_changes": len(self.regime_history),
            "season_shifts": len(self.season_history),
            "anomaly_windows": len(self.anomaly_windows),
            "scarcity_windows": len(self.scarcity_windows),
            "novelty_windows": len(self.novelty_windows),
            "deprivation_windows": len(self.deprivation_windows),
            "delayed_groups": len(self.delayed_groups),
            "episodes": len(self.episodes),
            "recent_episodes": [e.to_dict() for e in self.episodes[-3:]],
        }
