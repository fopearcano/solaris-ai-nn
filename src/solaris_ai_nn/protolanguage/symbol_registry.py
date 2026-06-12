"""Symbol registry -- every sign on the books, with its history.

Creates, updates, merges, and retires proto-symbols; indexes them by
token, type, and grounding; marks ambiguity and staleness instead of
hiding them; and persists the table as JSON plus an append-only JSONL
event stream.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .pattern_naming import InternalPatternNamer
from .symbols import ProtoSymbol, SymbolGrounding, SymbolType


@dataclass
class SymbolRegistry:
    """The closed book of internally generated signs."""

    state_dir: Optional[Union[str, Path]] = None
    namer: InternalPatternNamer = field(
        default_factory=InternalPatternNamer)

    def __post_init__(self) -> None:
        self.symbols: Dict[str, ProtoSymbol] = {}
        self._by_token: Dict[str, str] = {}
        self._by_grounding: Dict[str, str] = {}
        self.merges: List[Dict[str, Any]] = []
        self.events_written = 0
        self.json_path = (Path(self.state_dir) / "proto_symbols.json"
                          if self.state_dir else None)
        self.jsonl_path = (Path(self.state_dir) / "proto_symbols.jsonl"
                           if self.state_dir else None)

    # -- creation / update ------------------------------------------------------------

    def upsert_symbol(self, symbol_type: str, grounding_summary: str,
                      evidence_refs: List[str],
                      source_module: str = "",
                      evidence_kind: str = "real",
                      dimension: str = "signal_pattern",
                      offline: bool = False,
                      metadata: Optional[Dict[str, Any]] = None,
                      ) -> ProtoSymbol:
        """One symbol per (type, grounding key); observation otherwise."""
        if not evidence_refs:
            raise ValueError("a symbol needs evidence references; signs "
                             "are grounded or they do not exist")
        key = f"{symbol_type}:{grounding_summary}".lower()
        existing_id = self._by_grounding.get(key)
        if existing_id is not None:
            symbol = self.symbols[existing_id]
            for ref in evidence_refs:
                symbol.observe(ref, evidence_kind=evidence_kind,
                               dimension=dimension)
            self._log("reinforced", symbol)
            return symbol
        token = self.namer.make_token(symbol_type, grounding_summary)
        symbol = ProtoSymbol(
            token=token, type=symbol_type,
            debug_label=self.namer.make_debug_label(
                symbol_type, grounding_summary),
            source_modules=[source_module] if source_module else [],
            metadata={**(metadata or {}), "offline": offline,
                      "grounding_key": key})
        for ref in evidence_refs:
            symbol.observe(ref, evidence_kind=evidence_kind,
                           dimension=dimension)
        self.symbols[symbol.symbol_id] = symbol
        self._by_token[token] = symbol.symbol_id
        self._by_grounding[key] = symbol.symbol_id
        self._log("birth", symbol)
        return symbol

    def observe_symbol(self, symbol_id: str, evidence_ref: str,
                       evidence_kind: str = "real") -> None:
        symbol = self.symbols[symbol_id]
        symbol.observe(evidence_ref, evidence_kind=evidence_kind)
        self._log("observed", symbol)

    # -- retrieval ----------------------------------------------------------------

    def find_by_token(self, token: str) -> Optional[ProtoSymbol]:
        symbol_id = self._by_token.get(token)
        return self.symbols.get(symbol_id) if symbol_id else None

    def find_by_type(self, symbol_type: str) -> List[ProtoSymbol]:
        return [s for s in self.symbols.values()
                if s.type == symbol_type]

    def find_by_grounding(self, ref: str) -> List[ProtoSymbol]:
        return [s for s in self.symbols.values()
                if any(ref in g.reference for g in s.grounding_refs)]

    # -- lifecycle ----------------------------------------------------------------

    def merge_symbols(self, symbol_a: ProtoSymbol,
                      symbol_b: ProtoSymbol,
                      reason: str = "") -> ProtoSymbol:
        """The older symbol absorbs the younger; nothing is lost."""
        keep, drop = ((symbol_a, symbol_b)
                      if symbol_a.created_at <= symbol_b.created_at
                      else (symbol_b, symbol_a))
        keep.observation_count += drop.observation_count
        keep.grounding_refs = (keep.grounding_refs
                               + drop.grounding_refs)[-20:]
        keep.source_modules = sorted(set(keep.source_modules
                                         + drop.source_modules))
        drop.status = "merged"
        drop.metadata["merged_into"] = keep.token
        self.merges.append({"kept": keep.token, "dropped": drop.token,
                            "reason": reason, "timestamp": time.time()})
        self._log("merged", drop, detail=f"into {keep.token}: {reason}")
        return keep

    def mark_ambiguous(self, symbol_id: str, reason: str = "") -> None:
        symbol = self.symbols[symbol_id]
        symbol.status = "ambiguous"
        symbol.ambiguity_score = max(symbol.ambiguity_score, 0.7)
        symbol.metadata["ambiguity_reason"] = reason
        symbol.recompute_confidence()
        self._log("ambiguous", symbol, detail=reason)

    def mark_stale(self, symbol_id: str, reason: str = "") -> None:
        symbol = self.symbols[symbol_id]
        symbol.status = "stale"
        symbol.metadata["stale_reason"] = reason
        self._log("stale", symbol, detail=reason)

    def mark_extinct(self, symbol_id: str, reason: str = "") -> None:
        symbol = self.symbols[symbol_id]
        symbol.status = "extinct"
        symbol.metadata["extinction_reason"] = reason
        self._log("extinct", symbol, detail=reason)

    # -- views / persistence ----------------------------------------------------------

    def active(self) -> List[ProtoSymbol]:
        return [s for s in self.symbols.values()
                if s.status in ("active", "ambiguous")]

    def stable(self) -> List[ProtoSymbol]:
        return [s for s in self.symbols.values() if s.stable]

    def ambiguous(self) -> List[ProtoSymbol]:
        return [s for s in self.symbols.values()
                if s.status == "ambiguous" or s.ambiguity_score >= 0.5]

    def export_table(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in
                sorted(self.symbols.values(), key=lambda s: s.token)]

    def save(self) -> Optional[str]:
        if self.json_path is None:
            return None
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.json_path, "w", encoding="utf-8") as fh:
            json.dump({"symbols": self.export_table(),
                       "merges": self.merges[-50:]}, fh, indent=2,
                      default=str)
        return str(self.json_path)

    def _log(self, event: str, symbol: ProtoSymbol,
             detail: str = "") -> None:
        if self.jsonl_path is None:
            return
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.jsonl_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "event": event, "token": symbol.token,
                "type": symbol.type, "status": symbol.status,
                "observation_count": symbol.observation_count,
                "detail": detail, "timestamp": time.time()},
                default=str) + "\n")
        self.events_written += 1

    def snapshot(self) -> Dict[str, Any]:
        by_type = {t: 0 for t in SymbolType.ALL}
        for symbol in self.symbols.values():
            by_type[symbol.type] += 1
        return {
            "symbol_count": len(self.symbols),
            "active_count": len(self.active()),
            "stable_count": len(self.stable()),
            "ambiguous_count": len(self.ambiguous()),
            "merged_count": len(self.merges),
            "by_type": {t: c for t, c in by_type.items() if c},
            "events_written": self.events_written,
            "json_path": str(self.json_path) if self.json_path else None,
            "note": "internally generated signs; not human language and "
                    "never authority",
        }
