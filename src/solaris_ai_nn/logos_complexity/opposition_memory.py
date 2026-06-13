"""Opposition memory -- the record of tensions and how they resolved.

Tracks detected / preserved / resolved / recurring tensions, failed and
successful synthesis, unresolved Mysterium-linked tensions, and tensions that
became hypotheses, proto-symbols, or fossil milestones. Persists to JSON
(current set) and JSONL (append-only history). Bounded in memory.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .tension import LogosTension, TensionStatus


@dataclass
class OppositionRecord:
    """One append-only entry about a tension's life."""

    tension_id: str
    tension_type: str
    event: str  # detected | preserved | resolved | synthesis | promoted
    status: str = ""
    detail: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


RECURRENCE_THRESHOLD = 3


@dataclass
class OppositionMemory:
    """Bounded, persisted memory of tensions and synthesis outcomes."""

    state_dir: Optional[Union[str, Path]] = None
    write_log: bool = True
    max_tensions: int = 2000
    tensions: Dict[str, LogosTension] = field(default_factory=dict)
    history: List[OppositionRecord] = field(default_factory=list)
    synthesis_results: List[Dict[str, Any]] = field(default_factory=list)
    became_hypotheses: List[str] = field(default_factory=list)
    became_symbols: List[str] = field(default_factory=list)
    became_fossils: List[str] = field(default_factory=list)
    _dedup_counts: Dict[str, int] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.tensions_path = (Path(self.state_dir) / "logos_tensions.jsonl"
                              if self.state_dir else None)
        self.memory_path = (Path(self.state_dir) / "opposition_memory.json"
                            if self.state_dir else None)
        self.results_path = (Path(self.state_dir) / "synthesis_results.jsonl"
                            if self.state_dir else None)

    # -- recording ----------------------------------------------------------------

    def record_tension(self, tension: LogosTension) -> LogosTension:
        new = tension.tension_id not in self.tensions
        self.tensions[tension.tension_id] = tension
        self._dedup_counts[tension.dedup_key] = (
            self._dedup_counts.get(tension.dedup_key, 0) + (1 if new else 0))
        if new:
            self._log(tension, "detected", tension.status)
            if self.tensions_path is not None and self.write_log:
                self.tensions_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.tensions_path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(tension.to_dict(), default=str)
                             + "\n")
        self.tensions = dict(list(self.tensions.items())[-self.max_tensions:])
        return tension

    def record_status(self, tension: LogosTension, detail: str = "") -> None:
        self.tensions[tension.tension_id] = tension
        event = ("preserved" if tension.status == TensionStatus.PRESERVED
                 else "resolved")
        self._log(tension, event, tension.status, detail)
        if tension.status == TensionStatus.HYPOTHESIS_CREATED:
            self.became_hypotheses.append(tension.tension_id)
        elif tension.status in (TensionStatus.SPLIT, TensionStatus.MERGED):
            self.became_symbols.append(tension.tension_id)

    def record_synthesis_result(self, result: Any) -> None:
        data = result.to_dict() if hasattr(result, "to_dict") else dict(result)
        self.synthesis_results.append(data)
        self.synthesis_results = self.synthesis_results[-1000:]
        if self.write_log and self.results_path is not None:
            self.results_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.results_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(data, default=str) + "\n")

    def record_fossil(self, tension_id: str) -> None:
        self.became_fossils.append(tension_id)

    def _log(self, tension: LogosTension, event: str, status: str,
             detail: str = "") -> None:
        self.history.append(OppositionRecord(
            tension_id=tension.tension_id, tension_type=tension.tension_type,
            event=event, status=status, detail=detail))
        self.history = self.history[-5000:]

    # -- views --------------------------------------------------------------------

    def preserved(self) -> List[LogosTension]:
        return [t for t in self.tensions.values()
                if t.status == TensionStatus.PRESERVED]

    def unresolved(self) -> List[LogosTension]:
        return [t for t in self.tensions.values()
                if t.status in (TensionStatus.DETECTED,
                                TensionStatus.UNRESOLVED)]

    def recurring(self) -> List[str]:
        return [k for k, c in self._dedup_counts.items()
                if c >= RECURRENCE_THRESHOLD]

    def counts_by_status(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for t in self.tensions.values():
            counts[t.status] = counts.get(t.status, 0) + 1
        return counts

    def successful_synthesis(self) -> int:
        return sum(1 for r in self.synthesis_results if r.get("applied"))

    def failed_synthesis(self) -> int:
        return sum(1 for r in self.synthesis_results if r.get("refused"))

    def save_state(self) -> None:
        if self.memory_path is None:
            return
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory_path.write_text(json.dumps({
            "counts_by_status": self.counts_by_status(),
            "recurring": self.recurring(),
            "became_hypotheses": self.became_hypotheses,
            "became_symbols": self.became_symbols,
            "became_fossils": self.became_fossils,
        }, indent=2, default=str), encoding="utf-8")

    def snapshot(self) -> Dict[str, Any]:
        return {
            "tension_count": len(self.tensions),
            "counts_by_status": self.counts_by_status(),
            "preserved_count": len(self.preserved()),
            "unresolved_count": len(self.unresolved()),
            "recurring_count": len(self.recurring()),
            "successful_synthesis": self.successful_synthesis(),
            "failed_synthesis": self.failed_synthesis(),
            "became_hypotheses": len(self.became_hypotheses),
            "became_symbols": len(self.became_symbols),
            "became_fossils": len(self.became_fossils),
        }
