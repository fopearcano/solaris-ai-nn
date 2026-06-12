"""Translation -- cautious debug text over internal symbols, nothing more.

``[ABS_0001] [NEED_SIGNAL_0002] [ACT_LOOK_0003]`` becomes "An absence
pattern was followed by a need pressure and an action suggestion." The
translation is for inspection only: it creates no facts, marks its own
uncertainty, passes ClaimGuard, and never says the system speaks human
language -- because it does not.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .pattern_naming import InternalPatternNamer
from .symbol_registry import SymbolRegistry
from .symbols import SymbolType

# type -> cautious noun phrase fragment.
_TYPE_PHRASES = {
    SymbolType.STIMULUS: "a repeated stimulus pattern",
    SymbolType.ABSENCE: "an absence pattern",
    SymbolType.ACTION: "an action suggestion",
    SymbolType.REACTION: "a reaction record",
    SymbolType.HABIT: "a stable habit loop",
    SymbolType.NEED: "a need pressure",
    SymbolType.BOUNDARY: "a boundary event",
    SymbolType.UNKNOWN: "an unknown-pressure marker",
    SymbolType.ENTITY: "a recurring observed entity",
    SymbolType.CONTEXT: "a recurring context",
    SymbolType.LATENT_SCHEMA: "an offline-consolidated schema",
    SymbolType.MILESTONE: "a developmental milestone marker",
    SymbolType.SELF_BOUNDARY: "a self-boundary marker",
    SymbolType.EXECUTIVE_DECISION: "an executive decision record",
}

TRANSLATION_SUFFIX = (" (debug translation of internal proto-symbols; "
                      "approximate; this is not human language)")


@dataclass
class ProtoLanguageTranslator:
    """Deterministic, ClaimGuard-gated debug rendering."""

    registry: Optional[SymbolRegistry] = None
    translations_made: int = field(default=0, init=False)
    translations_refused: int = field(default=0, init=False)

    def _phrase(self, token: str) -> str:
        parsed = InternalPatternNamer.parse_token(token)
        if parsed is None:
            return f"an unparsed internal token ({token})"
        phrase = _TYPE_PHRASES.get(parsed["symbol_type"],
                                   "an internal sign")
        qualifier = parsed.get("qualifier", "")
        if qualifier:
            phrase += f" ({qualifier.lower().replace('_', ' ')})"
        if self.registry is not None:
            symbol = self.registry.find_by_token(token)
            if symbol is not None and symbol.ambiguity_score >= 0.5:
                phrase += " [ambiguous]"
        return phrase

    def translate_tokens(self, tokens: List[str]) -> str:
        """One cautious sentence; refusal if ClaimGuard objects."""
        from ..governance.compliance import ClaimGuard

        phrases = [self._phrase(str(token)) for token in tokens if token]
        if not phrases:
            return ("No symbols to translate."
                    + TRANSLATION_SUFFIX)
        if len(phrases) == 1:
            text = f"{phrases[0].capitalize()} was recorded."
        else:
            text = (f"{phrases[0].capitalize()} was followed by "
                    + " and ".join(phrases[1:]) + ".")
        text += TRANSLATION_SUFFIX
        guard = ClaimGuard()
        if not guard.is_safe(text):
            rewritten = guard.rewrite(text)
            if guard.is_safe(rewritten):
                self.translations_made += 1
                return rewritten
            self.translations_refused += 1
            return ("Translation withheld: the rendering tripped "
                    "ClaimGuard." + TRANSLATION_SUFFIX)
        self.translations_made += 1
        return text

    def translate_utterance(self, utterance: Any) -> str:
        text = self.translate_tokens(list(utterance.symbols))
        utterance.human_debug_translation = text
        return text

    def snapshot(self) -> Dict[str, Any]:
        return {
            "translations_made": self.translations_made,
            "translations_refused": self.translations_refused,
            "note": "translations are inspection-only renderings; they "
                    "create no facts and claim no human language",
        }
