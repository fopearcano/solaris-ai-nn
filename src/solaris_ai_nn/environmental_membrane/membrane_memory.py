"""Membrane memory -- boundary memory of sources; append-only; never forgives silently.

:class:`MembraneMemory` tracks, per source, reliability / toxicity / silence /
dominance / rhythm and counts of malformed payloads, quarantine triggers, useful
patterns, operator contamination, debug-gloss dependence, overload, and deprivation.
It is boundary memory, not cognition: history is append-only, toxic history is never
deleted, a bad source is never silently forgiven, and permanent blocks come only from
governance/safety -- the memory just reports recommendations.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

MEMORY_FILENAME = "MEMBRANE_MEMORY.json"
HISTORY_FILENAME = "MEMBRANE_MEMORY_HISTORY.jsonl"
INDEX_FILENAME = "MEMBRANE_MEMORY_INDEX.md"


@dataclass
class MembraneSourceMemory:
    """Accumulated boundary memory for one source."""

    source_id: str
    reliability: float = 0.7
    toxicity: float = 0.0
    silence_count: int = 0
    dominance_count: int = 0
    rhythm: str = "irregular"
    malformed_count: int = 0
    quarantine_count: int = 0
    useful_count: int = 0
    operator_contamination_count: int = 0
    debug_gloss_dependence_count: int = 0
    overload_count: int = 0
    deprivation_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "reliability": round(self.reliability, 3),
            "toxicity": round(self.toxicity, 3),
            "silence_count": self.silence_count,
            "dominance_count": self.dominance_count, "rhythm": self.rhythm,
            "malformed_count": self.malformed_count,
            "quarantine_count": self.quarantine_count,
            "useful_count": self.useful_count,
            "operator_contamination_count": self.operator_contamination_count,
            "debug_gloss_dependence_count": self.debug_gloss_dependence_count,
            "overload_count": self.overload_count,
            "deprivation_count": self.deprivation_count,
            "recommend_review": self.toxicity >= 0.5
            or self.quarantine_count >= 3,
        }


@dataclass
class MembraneMemoryRecord:
    """One append-only membrane-memory snapshot entry."""

    run_id: str
    source_id: str
    delta: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"run_id": self.run_id, "source_id": self.source_id,
                "delta": dict(self.delta), "created_at": self.created_at}


@dataclass
class MembraneMemory:
    """Append-only boundary memory; never silently forgives a bad source."""

    state_dir: str = ".solaris_ai_nn_live"
    sources: Dict[str, MembraneSourceMemory] = field(default_factory=dict)
    history: List[MembraneMemoryRecord] = field(default_factory=list)

    @property
    def _dir(self) -> str:
        return os.path.join(self.state_dir, "membrane", "memory")

    @property
    def memory_path(self) -> str:
        return os.path.join(self._dir, MEMORY_FILENAME)

    @property
    def history_path(self) -> str:
        return os.path.join(self._dir, HISTORY_FILENAME)

    @property
    def index_path(self) -> str:
        return os.path.join(self._dir, INDEX_FILENAME)

    def load(self) -> "MembraneMemory":
        if os.path.isfile(self.memory_path):
            try:
                with open(self.memory_path, encoding="utf-8") as fh:
                    data = json.load(fh)
                for sid, d in (data.get("sources", {}) or {}).items():
                    self.sources[sid] = MembraneSourceMemory(
                        source_id=sid,
                        reliability=float(d.get("reliability", 0.7) or 0.7),
                        toxicity=float(d.get("toxicity", 0.0) or 0.0),
                        silence_count=int(d.get("silence_count", 0) or 0),
                        dominance_count=int(d.get("dominance_count", 0) or 0),
                        rhythm=d.get("rhythm", "irregular"),
                        malformed_count=int(d.get("malformed_count", 0) or 0),
                        quarantine_count=int(d.get("quarantine_count", 0) or 0),
                        useful_count=int(d.get("useful_count", 0) or 0),
                        operator_contamination_count=int(
                            d.get("operator_contamination_count", 0) or 0),
                        debug_gloss_dependence_count=int(
                            d.get("debug_gloss_dependence_count", 0) or 0),
                        overload_count=int(d.get("overload_count", 0) or 0),
                        deprivation_count=int(d.get("deprivation_count", 0)
                                              or 0))
            except Exception:
                pass
        return self

    def _source(self, sid: str) -> MembraneSourceMemory:
        if sid not in self.sources:
            self.sources[sid] = MembraneSourceMemory(source_id=sid)
        return self.sources[sid]

    def update_source(self, run_id: str, sid: str, *, quarantined: int = 0,
                      useful: int = 0, operator_contamination: int = 0,
                      debug_gloss: int = 0, overload: int = 0,
                      deprivation: int = 0, silent: bool = False,
                      dominant: bool = False) -> None:
        m = self._source(sid)
        m.quarantine_count += quarantined
        m.useful_count += useful
        m.operator_contamination_count += operator_contamination
        m.debug_gloss_dependence_count += debug_gloss
        m.overload_count += overload
        m.deprivation_count += deprivation
        if silent:
            m.silence_count += 1
        if dominant:
            m.dominance_count += 1
        # Toxicity rises with quarantine/contamination; never silently forgiven.
        m.toxicity = min(1.0, m.toxicity + 0.2 * quarantined
                         + 0.1 * operator_contamination)
        # Reliability rises slowly with useful patterns, falls with quarantine.
        m.reliability = max(0.0, min(1.0, m.reliability + 0.02 * useful
                                     - 0.1 * quarantined))
        self.history.append(MembraneMemoryRecord(
            run_id=run_id, source_id=sid,
            delta={"quarantined": quarantined, "useful": useful,
                   "operator_contamination": operator_contamination,
                   "debug_gloss": debug_gloss, "overload": overload,
                   "deprivation": deprivation, "silent": silent,
                   "dominant": dominant}))

    def index(self) -> Dict[str, Any]:
        return {
            "membrane_memory_source_count": len(self.sources),
            "toxic_source_count": sum(1 for m in self.sources.values()
                                      if m.toxicity >= 0.5),
            "sources": {sid: m.to_dict() for sid, m in self.sources.items()},
            "note": "boundary memory, not cognition; append-only; toxic history "
                    "is never deleted; a bad source is never silently forgiven; "
                    "permanent blocks come only from governance/safety",
        }

    def write(self) -> Dict[str, str]:
        os.makedirs(self._dir, exist_ok=True)
        with open(self.memory_path, "w", encoding="utf-8") as fh:
            json.dump(self.index(), fh, indent=2, default=str)
        with open(self.history_path, "a", encoding="utf-8") as fh:
            for r in self.history:
                fh.write(json.dumps(r.to_dict(), default=str) + "\n")
        with open(self.index_path, "w", encoding="utf-8") as fh:
            fh.write(self._render_md())
        return {"memory": self.memory_path, "history": self.history_path,
                "index": self.index_path}

    def _render_md(self) -> str:
        idx = self.index()
        lines = ["# Membrane Memory Index", "",
                 f"- sources: {idx['membrane_memory_source_count']}",
                 f"- toxic sources: {idx['toxic_source_count']}", "",
                 "| source | reliability | toxicity | quarantine | review? |",
                 "| --- | --- | --- | --- | --- |"]
        for sid, m in self.sources.items():
            d = m.to_dict()
            lines.append(f"| {sid} | {d['reliability']:.2f} | "
                         f"{d['toxicity']:.2f} | {d['quarantine_count']} | "
                         f"{d['recommend_review']} |")
        lines += ["", "_Boundary memory, not cognition. Append-only; toxic "
                  "history is never deleted; a bad source is never silently "
                  "forgiven; permanent blocks come only from governance/safety._"]
        return "\n".join(lines) + "\n"
