"""Symbol hygiene -- tend the proto-symbol ecology without renaming it.

The :class:`SymbolHygieneManager` detects symbol explosion, stale symbols,
duplicates, high ambiguity, ungrounded symbols, and useless sequences. It
marks symbols stale, merges duplicates, requests disambiguation via the
active-perception / hypothesis layers, and fossilizes first stable symbols.
Symbols are not human words: nothing here renames them, and stable symbols
are never deleted without archive.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .repair_actions import RepairAction, RepairActionType, make_repair


@dataclass
class SymbolHygieneManager:
    """Detects symbol degradation; marks/merges, never renames with words."""

    explosion_threshold: int = 500
    disambiguation_requests: List[str] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)

    def detect(self, context: Dict[str, Any]) -> Dict[str, Any]:
        proto = (context or {}).get("proto_language") or {}
        count = int(proto.get("symbol_count", 0) or 0)
        ambiguous = int(proto.get("ambiguous_symbol_count", 0) or 0)
        result = {
            "symbol_count": count,
            "explosion": count > self.explosion_threshold,
            "stale_symbols": list(proto.get("stale_symbols") or []),
            "duplicate_symbols": list(proto.get("duplicate_symbols") or []),
            "ambiguous_symbols": list(proto.get("ambiguous_symbols") or []),
            "ungrounded_symbols": list(proto.get("ungrounded_symbols") or []),
            "useless_sequences": list(proto.get("useless_sequences") or []),
            "ambiguous_ratio": (round(ambiguous / count, 4) if count else 0.0),
        }
        self.findings.append(result)
        self.findings = self.findings[-50:]
        return result

    def propose(self, context: Dict[str, Any]) -> List[RepairAction]:
        detected = self.detect(context)
        actions: List[RepairAction] = []
        for sym in detected["stale_symbols"]:
            actions.append(make_repair(
                RepairActionType.MARK_SYMBOL_STALE, target_ref=str(sym),
                reason="symbol no longer recurs",
                expected_benefit="reduce symbol staleness"))
        for pair in detected["duplicate_symbols"]:
            actions.append(make_repair(
                RepairActionType.MERGE_DUPLICATE_SYMBOLS, target_ref=str(pair),
                reason="duplicate symbols ground to the same pattern",
                expected_benefit="reduce duplication"))
        for sym in detected["ungrounded_symbols"]:
            actions.append(make_repair(
                RepairActionType.MARK_SYMBOL_STALE, target_ref=str(sym),
                reason="symbol has no grounding refs",
                expected_benefit="flag an ungrounded symbol"))
        for sym in detected["ambiguous_symbols"]:
            self.disambiguation_requests.append(str(sym))
            actions.append(make_repair(
                RepairActionType.REQUEST_LATENT_REPLAY, target_ref=str(sym),
                reason="ambiguous symbol; request disambiguation",
                expected_benefit="route to active-perception/hypothesis "
                                 "disambiguation"))
        if detected["explosion"]:
            actions.append(make_repair(
                RepairActionType.MARK_SYMBOL_STALE, target_ref="symbol_explosion",
                reason=f"symbol count {detected['symbol_count']} exceeds "
                       f"{self.explosion_threshold}",
                expected_benefit="reduce symbol explosion by marking the "
                                 "weakest stale"))
        return actions

    def apply_to_registry(self, registry: Any, action: RepairAction) -> bool:
        """Apply a symbol repair to a real SymbolRegistry (mark/merge only)."""
        if registry is None or not action.target_ref:
            return False
        try:
            if action.action_type == RepairActionType.MARK_SYMBOL_STALE:
                registry.mark_stale(action.target_ref,
                                    reason=action.reason)
                return True
            # Merges need two ids; left to the caller with explicit ids.
            return False
        except Exception:
            return False

    def snapshot(self) -> Dict[str, Any]:
        return {
            "disambiguation_requests": list(self.disambiguation_requests),
            "last_finding": self.findings[-1] if self.findings else None,
        }
