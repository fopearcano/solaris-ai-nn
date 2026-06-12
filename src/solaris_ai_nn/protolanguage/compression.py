"""Symbol compression -- does naming things make memory smaller?

A trace is symbolized by replacing events whose grounding matches a
registered symbol with that symbol's token. The evaluator measures what
was gained (ratio), what was risked (information loss estimate, ambiguity
introduced), and what was protected: evidence references survive into the
symbolized form, and safety/boundary incidents are never symbolized away
-- they stay verbatim, always.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .symbol_registry import SymbolRegistry

# Event kinds that must never disappear behind a token.
PROTECTED_KINDS = ("boundary_violation", "safety", "emergency",
                   "policy_violation", "unsafe", "incident")


def _event_text(event: Any) -> str:
    if isinstance(event, dict):
        return " ".join(f"{k}={v}" for k, v in sorted(event.items()))
    return str(event)


def _is_protected(event: Any) -> bool:
    text = _event_text(event).lower()
    return any(kind in text for kind in PROTECTED_KINDS)


@dataclass
class SymbolizedTrace:
    """The compressed form, with its provenance intact."""

    entries: List[Dict[str, Any]] = field(default_factory=list)
    raw_length: int = 0
    symbolized_length: int = 0
    protected_kept_verbatim: int = 0

    def tokens(self) -> List[str]:
        return [e["token"] for e in self.entries if e.get("token")]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SymbolCompressionEvaluator:
    """Symbolizes traces and audits what the compression cost."""

    evaluations: int = field(default=0, init=False)
    last_ratio: Optional[float] = None

    @staticmethod
    def _match_symbol(text: str, registry: SymbolRegistry):
        """Deterministic first match: a symbol whose grounding-key
        fragment appears in the event text."""
        lowered = text.lower()
        for symbol in sorted(registry.active(),
                             key=lambda s: s.token):
            key = str(symbol.metadata.get("grounding_key", ""))
            fragment = key.split(":", 1)[-1].strip()
            if fragment and fragment in lowered:
                return symbol
        return None

    def symbolize_trace(self, trace: List[Any],
                        registry: SymbolRegistry) -> SymbolizedTrace:
        """Replace symbol-matching runs with tokens; protect the rest."""
        result = SymbolizedTrace(raw_length=len(trace))
        previous_token: Optional[str] = None
        for event in trace:
            text = _event_text(event)
            if _is_protected(event):
                # Safety/boundary incidents stay verbatim, always.
                result.entries.append({"token": None, "raw": text,
                                       "protected": True})
                result.protected_kept_verbatim += 1
                previous_token = None
                continue
            match = self._match_symbol(text, registry)
            matches = [match] if match is not None else []
            if matches:
                token = matches[0].token
                if token == previous_token:
                    # Run-length fold: repeated symbol collapses.
                    result.entries[-1]["repeat"] = \
                        result.entries[-1].get("repeat", 1) + 1
                else:
                    result.entries.append({
                        "token": token,
                        "evidence_ref": text[:80],
                        "ambiguity": matches[0].ambiguity_score})
                previous_token = token
            else:
                result.entries.append({"token": None, "raw": text[:80]})
                previous_token = None
        result.symbolized_length = len(result.entries)
        return result

    def evaluate_compression(self, raw_trace: List[Any],
                             symbolized: SymbolizedTrace,
                             ) -> Dict[str, Any]:
        raw_length = len(raw_trace)
        ratio = (round(symbolized.symbolized_length
                       / max(1, raw_length), 4))
        symbolized_entries = [e for e in symbolized.entries
                              if e.get("token")]
        evidence_retained = all(e.get("evidence_ref")
                                for e in symbolized_entries)
        ambiguities = [float(e.get("ambiguity", 0.0))
                       for e in symbolized_entries]
        protected_in_raw = sum(1 for event in raw_trace
                               if _is_protected(event))
        self.evaluations += 1
        self.last_ratio = ratio
        return {
            "raw_trace_length": raw_length,
            "symbolized_trace_length": symbolized.symbolized_length,
            "compression_ratio": ratio,
            "information_loss_estimate": round(
                max(0.0, 1.0 - ratio) * (sum(ambiguities)
                                         / len(ambiguities)
                                         if ambiguities else 0.0), 4),
            "evidence_retained": evidence_retained,
            "ambiguity_introduced": (round(max(ambiguities), 4)
                                     if ambiguities else 0.0),
            "safety_events_in_raw": protected_in_raw,
            "safety_events_kept_verbatim":
                symbolized.protected_kept_verbatim,
            "safety_events_hidden": protected_in_raw
            - symbolized.protected_kept_verbatim,
            "fossil_memory_usefulness": (
                "candidate" if ratio < 0.7 and evidence_retained
                else "not demonstrated"),
            "note": "compression never deletes raw evidence on its own; "
                    "the developmental memory layers own retention",
        }

    def update_symbol_scores(self, registry: SymbolRegistry,
                             report: Dict[str, Any],
                             tokens: List[str]) -> None:
        """Feed measured compression value back into the symbols."""
        gain = max(0.0, 1.0 - float(report["compression_ratio"]))
        for token in set(tokens):
            symbol = registry.find_by_token(token)
            if symbol is not None:
                symbol.compression_score = round(
                    max(symbol.compression_score, gain), 4)
                symbol.recompute_confidence()

    def snapshot(self) -> Dict[str, Any]:
        return {"evaluations": self.evaluations,
                "last_compression_ratio": self.last_ratio,
                "protected_kinds": list(PROTECTED_KINDS)}
