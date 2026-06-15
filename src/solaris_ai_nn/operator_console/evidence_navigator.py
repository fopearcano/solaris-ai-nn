"""Evidence navigator -- search local evidence, nothing external.

:class:`EvidenceNavigator` indexes the known JSON/JSONL/Markdown artifacts and
lets the operator search them by keyword, evidence type, module, profile, or
safety status. It returns the path, a title, an excerpt, evidence refs, and a
timestamp. It searches *local artifacts only*: there is no external search, no
vector DB, and no LLM authority, and missing or corrupted artifacts are reported.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class EvidenceType:
    SAFETY_INVARIANT_RESULT = "safety_invariant_result"
    RED_TEAM_RESULT = "red_team_result"
    ASSURANCE_CASE = "assurance_case"
    PILOT_REPORT = "pilot_report"
    POST_PILOT_ANALYSIS = "post_pilot_analysis"
    RESEARCH_RESULT = "research_result"
    ARCHITECTURE_REVIEW = "architecture_review"
    ADR = "adr"
    ROADMAP = "roadmap"
    ACTION_LEDGER = "action_ledger"
    SENSORY_PROVENANCE = "sensory_provenance"
    INNER_MAP_SNAPSHOT = "inner_map_snapshot"
    OPS_INCIDENT = "ops_incident"
    AUTO_REGENERATION_RECORD = "auto_regeneration_record"
    LOGOS_TENSION = "logos_tension"
    HYPOTHESIS_RECORD = "hypothesis_record"
    PROTO_SYMBOL_RECORD = "proto_symbol_record"
    WORLD_MODEL_RECORD = "world_model_record"

    ALL = (SAFETY_INVARIANT_RESULT, RED_TEAM_RESULT, ASSURANCE_CASE,
           PILOT_REPORT, POST_PILOT_ANALYSIS, RESEARCH_RESULT,
           ARCHITECTURE_REVIEW, ADR, ROADMAP, ACTION_LEDGER,
           SENSORY_PROVENANCE, INNER_MAP_SNAPSHOT, OPS_INCIDENT,
           AUTO_REGENERATION_RECORD, LOGOS_TENSION, HYPOTHESIS_RECORD,
           PROTO_SYMBOL_RECORD, WORLD_MODEL_RECORD)


# (evidence type, filename substrings) mapping for classification.
_TYPE_HINTS = (
    (EvidenceType.SAFETY_INVARIANT_RESULT,
     ("safety_invariant", "safety_dashboard")),
    (EvidenceType.RED_TEAM_RESULT, ("red_team",)),
    (EvidenceType.ASSURANCE_CASE, ("assurance_case",)),
    (EvidenceType.POST_PILOT_ANALYSIS, ("post_pilot", "forensic")),
    (EvidenceType.PILOT_REPORT, ("pilot",)),
    (EvidenceType.RESEARCH_RESULT, ("research",)),
    (EvidenceType.ARCHITECTURE_REVIEW, ("architecture_review", "architecture")),
    (EvidenceType.ADR, ("adr_", "decision_record")),
    (EvidenceType.ROADMAP, ("roadmap",)),
    (EvidenceType.ACTION_LEDGER, ("action_ledger", "ledger")),
    (EvidenceType.SENSORY_PROVENANCE, ("sensory", "provenance")),
    (EvidenceType.INNER_MAP_SNAPSHOT, ("inner_map", "innermap")),
    (EvidenceType.OPS_INCIDENT, ("incident",)),
    (EvidenceType.AUTO_REGENERATION_RECORD, ("autoregeneration", "regeneration")),
    (EvidenceType.LOGOS_TENSION, ("logos", "tension")),
    (EvidenceType.HYPOTHESIS_RECORD, ("hypothesis",)),
    (EvidenceType.PROTO_SYMBOL_RECORD, ("proto_symbol", "protolanguage")),
    (EvidenceType.WORLD_MODEL_RECORD, ("world_model",)),
)

_DEFAULT_EXTS = (".json", ".jsonl", ".md", ".txt")


def _evidence_type(name: str) -> Optional[str]:
    low = name.lower()
    for etype, hints in _TYPE_HINTS:
        if any(h in low for h in hints):
            return etype
    return None


@dataclass
class EvidenceQuery:
    keyword: Optional[str] = None
    evidence_type: Optional[str] = None
    module: Optional[str] = None
    profile_id: Optional[str] = None
    safety_status: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class EvidenceSearchResult:
    path: str
    evidence_type: Optional[str]
    title: str
    excerpt: str
    evidence_refs: List[str] = field(default_factory=list)
    timestamp: float = 0.0
    corrupted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class _Entry:
    path: str
    evidence_type: Optional[str]
    text: str
    timestamp: float
    corrupted: bool


@dataclass
class EvidenceNavigator:
    """Indexes and searches local evidence artifacts only."""

    directories: List[str] = field(default_factory=list)
    _entries: List[_Entry] = field(default_factory=list, init=False)
    corrupted_paths: List[str] = field(default_factory=list, init=False)

    def index(self) -> int:
        from .artifact_index import DEFAULT_DIRECTORIES

        dirs = self.directories or list(DEFAULT_DIRECTORIES)
        self._entries = []
        self.corrupted_paths = []
        for directory in dirs:
            if not directory or not os.path.isdir(directory):
                continue
            for root, _dirs, files in os.walk(directory):
                for name in sorted(files):
                    if os.path.splitext(name)[1].lower() not in _DEFAULT_EXTS:
                        continue
                    self._entries.append(self._read(os.path.join(root, name)))
        return len(self._entries)

    def _read(self, path: str) -> _Entry:
        etype = _evidence_type(os.path.basename(path))
        try:
            mtime = os.path.getmtime(path)
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                # Read a bounded prefix; large files are not loaded fully.
                text = fh.read(40_000)
            return _Entry(path=path, evidence_type=etype, text=text,
                          timestamp=mtime, corrupted=False)
        except OSError:
            self.corrupted_paths.append(path)
            return _Entry(path=path, evidence_type=etype, text="",
                          timestamp=0.0, corrupted=True)

    def indexed_count(self) -> int:
        return len(self._entries)

    def search(self, keyword: Optional[str] = None, *,
               evidence_type: Optional[str] = None,
               module: Optional[str] = None,
               profile_id: Optional[str] = None,
               safety_status: Optional[str] = None,
               limit: int = 50) -> List[EvidenceSearchResult]:
        query = EvidenceQuery(keyword=keyword, evidence_type=evidence_type,
                              module=module, profile_id=profile_id,
                              safety_status=safety_status)
        return self.search_query(query, limit=limit)

    def search_query(self, query: EvidenceQuery,
                     limit: int = 50) -> List[EvidenceSearchResult]:
        out: List[EvidenceSearchResult] = []
        needles = [n.lower() for n in (query.keyword, query.module,
                                       query.profile_id, query.safety_status)
                   if n]
        for entry in self._entries:
            if query.evidence_type and entry.evidence_type != query.evidence_type:
                continue
            low = entry.text.lower()
            hay = low + " " + entry.path.lower()
            if needles and not all(n in hay for n in needles):
                continue
            out.append(self._to_result(entry, needles))
            if len(out) >= limit:
                break
        return out

    def _to_result(self, entry: _Entry,
                   needles: List[str]) -> EvidenceSearchResult:
        excerpt = ""
        if needles:
            idx = entry.text.lower().find(needles[0])
            if idx >= 0:
                start = max(0, idx - 60)
                excerpt = entry.text[start:idx + 120].replace("\n", " ").strip()
        if not excerpt:
            excerpt = entry.text[:160].replace("\n", " ").strip()
        return EvidenceSearchResult(
            path=entry.path, evidence_type=entry.evidence_type,
            title=os.path.basename(entry.path), excerpt=excerpt,
            evidence_refs=self._refs(entry), timestamp=entry.timestamp,
            corrupted=entry.corrupted)

    @staticmethod
    def _refs(entry: _Entry) -> List[str]:
        if not entry.path.lower().endswith(".json"):
            return []
        try:
            data = json.loads(entry.text)
        except (json.JSONDecodeError, ValueError):
            return []
        if isinstance(data, dict):
            refs = data.get("evidence_refs") or data.get("evidence")
            if isinstance(refs, list):
                return [str(r) for r in refs][:20]
        return []

    def snapshot(self) -> Dict[str, Any]:
        return {
            "indexed_count": self.indexed_count(),
            "corrupted_count": len(self.corrupted_paths),
            "corrupted_paths": list(self.corrupted_paths),
            "external_search": False,
        }
