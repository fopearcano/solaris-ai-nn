"""Internal pattern naming -- deterministic tokens, no anthropomorphism.

Tokens are built from a fixed per-type prefix, an optional sanitized
qualifier from the grounding summary, a zero-padded counter, and (on
collision) a short hash suffix. No mystical names, no human-semantic
claims -- the cautious human-readable label is a separate, clearly
secondary debug artifact.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .symbols import SymbolType

TYPE_PREFIXES: Dict[str, str] = {
    SymbolType.STIMULUS: "SIG",
    SymbolType.ABSENCE: "ABS",
    SymbolType.ACTION: "ACT",
    SymbolType.REACTION: "RCT",
    SymbolType.HABIT: "HAB",
    SymbolType.NEED: "NEED",
    SymbolType.BOUNDARY: "BND",
    SymbolType.UNKNOWN: "UNK",
    SymbolType.ENTITY: "ENT",
    SymbolType.CONTEXT: "CTX",
    SymbolType.LATENT_SCHEMA: "LAT",
    SymbolType.MILESTONE: "MILE",
    SymbolType.SELF_BOUNDARY: "SELF",
    SymbolType.EXECUTIVE_DECISION: "EXEC",
}

_PREFIX_TO_TYPE = {prefix: t for t, prefix in TYPE_PREFIXES.items()}

# Qualifier fragments that would smuggle anthropomorphic or mystical
# meaning into a token name.
FORBIDDEN_NAME_FRAGMENTS = ("SOUL", "SPIRIT", "MIND", "FEEL", "WANT",
                            "AWARE", "ALIVE", "DREAMS", "WISH", "LOVE")

_QUALIFIER_RE = re.compile(r"[^A-Z0-9]+")


@dataclass
class InternalPatternNamer:
    """Deterministic token factory with per-prefix counters."""

    counters: Dict[str, int] = field(default_factory=dict)
    issued: Dict[str, str] = field(default_factory=dict)  # token -> type

    def _qualifier(self, grounding_summary: str) -> str:
        cleaned = _QUALIFIER_RE.sub("_",
                                    str(grounding_summary).upper())
        parts = [p for p in cleaned.split("_") if p][:1]
        qualifier = (parts[0][:8] if parts else "")
        if qualifier in FORBIDDEN_NAME_FRAGMENTS:
            return ""  # the counter alone is name enough
        return qualifier

    def make_token(self, symbol_type: str,
                   grounding_summary: str = "") -> str:
        prefix = TYPE_PREFIXES.get(symbol_type)
        if prefix is None:
            raise ValueError(f"unknown symbol type {symbol_type!r}")
        qualifier = self._qualifier(grounding_summary)
        stem = f"{prefix}_{qualifier}" if qualifier else prefix
        self.counters[stem] = self.counters.get(stem, 0) + 1
        token = f"{stem}_{self.counters[stem]:04d}"
        if token in self.issued:  # collision resistance, deterministic
            suffix = hashlib.sha256(
                f"{token}:{grounding_summary}".encode()).hexdigest()[:4]
            token = f"{token}_{suffix}"
        self.issued[token] = symbol_type
        return token

    @staticmethod
    def make_debug_label(symbol_type: str, evidence: str) -> str:
        """A cautious, clearly-secondary human-readable label."""
        kind = symbol_type.replace("_symbol", "").replace("_", " ")
        return (f"[debug label] internal sign for a repeated {kind} "
                f"pattern (evidence: {str(evidence)[:60]})")

    @staticmethod
    def parse_token(token: str) -> Optional[Dict[str, Any]]:
        match = re.match(
            r"^([A-Z]+)(?:_([A-Z0-9]+(?:_[A-Z0-9]+)*?))?_(\d{3,6})"
            r"(?:_([0-9a-f]{4}))?$", str(token))
        if not match:
            return None
        prefix, qualifier, counter, suffix = match.groups()
        if prefix not in _PREFIX_TO_TYPE:
            return None
        return {"prefix": prefix,
                "symbol_type": _PREFIX_TO_TYPE[prefix],
                "qualifier": qualifier or "",
                "counter": int(counter),
                "hash_suffix": suffix or ""}

    def snapshot(self) -> Dict[str, Any]:
        return {"tokens_issued": len(self.issued),
                "stems": dict(self.counters),
                "note": "deterministic prefixes and counters; no "
                        "anthropomorphic or mystical naming"}
