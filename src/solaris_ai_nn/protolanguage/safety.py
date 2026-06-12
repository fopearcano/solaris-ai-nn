"""Proto-language safety -- signs name things; they command nothing.

Hard rules: proto-symbols cannot execute actions, approve governance
requests, override safety, weaken boundary rules, treat counterfactuals
as real, or claim human-level language; translations pass ClaimGuard;
symbols born from pilot-stream text never become operator commands; and
symbolic compression cannot hide safety incidents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

HARD_RULES = (
    "proto-symbols cannot execute actions",
    "proto-symbols cannot approve governance requests",
    "proto-symbols cannot override safety",
    "proto-symbols cannot weaken boundary rules",
    "proto-symbols cannot treat counterfactuals as real",
    "proto-symbols cannot create human-level language claims",
    "generated translations must pass ClaimGuard",
    "symbols from pilot stream text cannot become operator commands",
    "symbols cannot hide safety incidents through compression",
)

_HUMAN_LANGUAGE_CLAIMS = ("speaks human language", "understands language",
                          "speaks english", "has language like a human",
                          "human-level language")

_COMMAND_SHAPES = ("execute", "approve request", "shutdown", "rm -",
                   "sudo", "disable", "commit action")


@dataclass
class ProtoLanguageSafetyReport:
    safe: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "violations": list(self.violations)}


@dataclass
class ProtoLanguageSafetyValidator:
    """Validates symbols, compression, translations, and utterances."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list,
                                            init=False)

    def _finish(self, check: str,
                violations: List[str]) -> ProtoLanguageSafetyReport:
        report = ProtoLanguageSafetyReport(safe=not violations,
                                           violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append({"check": check, **report.to_dict()})
        self.decisions = self.decisions[-100:]
        return report

    # -- structural negatives -----------------------------------------------------------

    @staticmethod
    def symbols_can_execute() -> bool:
        return False

    @staticmethod
    def symbols_can_approve() -> bool:
        return False

    @staticmethod
    def symbols_have_authority() -> bool:
        return False

    # -- validations ----------------------------------------------------------------

    def validate_symbol(self, symbol: Any,
                        context: Optional[Dict[str, Any]] = None,
                        ) -> ProtoLanguageSafetyReport:
        ctx = dict(context or {})
        violations: List[str] = []
        metadata = getattr(symbol, "metadata", {}) or {}
        evidence_kinds = {g.evidence_kind for g in
                          getattr(symbol, "grounding_refs", [])}
        if "counterfactual" in evidence_kinds \
                and not metadata.get("offline"):
            violations.append(
                "a symbol grounded in counterfactual evidence must be "
                "marked offline; counterfactuals never become real "
                "grounding")
        if ctx.get("treat_as_command") \
                or metadata.get("treat_as_command"):
            violations.append("proto-symbols cannot become commands; "
                              "they name structure, they execute "
                              "nothing")
        if metadata.get("source") == "pilot_stream" \
                and ctx.get("as_operator_command"):
            violations.append(
                "symbols from pilot stream text cannot become operator "
                "commands")
        token = str(getattr(symbol, "token", ""))
        if any(shape in token.lower() for shape in _COMMAND_SHAPES):
            violations.append(f"token {token!r} is command-shaped")
        return self._finish("symbol", violations)

    def validate_compression(self, report: Dict[str, Any],
                             ) -> ProtoLanguageSafetyReport:
        violations: List[str] = []
        hidden = int(report.get("safety_events_hidden", 0) or 0)
        if hidden > 0:
            violations.append(
                f"{hidden} safety/boundary event(s) disappeared behind "
                "symbols; compression cannot hide safety incidents")
        return self._finish("compression", violations)

    def validate_translation(self, text: str,
                             ) -> ProtoLanguageSafetyReport:
        from ..governance.compliance import ClaimGuard

        violations: List[str] = []
        lowered = str(text).lower()
        for claim in _HUMAN_LANGUAGE_CLAIMS:
            if claim in lowered:
                violations.append(
                    f"translation claims human-level language "
                    f"({claim!r}); it is an internal proto-symbolic "
                    "system")
        for fragment in ("i want", "i feel", "i am conscious"):
            if fragment in lowered:
                violations.append(f"translation contains forbidden "
                                  f"first-person claim {fragment!r}")
        if not ClaimGuard().is_safe(str(text)):
            violations.append("translation contains claims ClaimGuard "
                              "flags as unsupported")
        return self._finish("translation", violations)

    def validate_utterance(self, utterance: Any,
                           context: Optional[Dict[str, Any]] = None,
                           ) -> ProtoLanguageSafetyReport:
        ctx = dict(context or {})
        violations: List[str] = []
        if ctx.get("execute") or ctx.get("as_command"):
            violations.append("a proto-utterance is internal structure; "
                              "it cannot execute or become a command")
        translation = getattr(utterance, "human_debug_translation",
                              None)
        if translation:
            inner = self.validate_translation(translation)
            violations.extend(inner.violations)
        return self._finish("utterance", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "symbols_can_execute": self.symbols_can_execute(),
            "symbols_can_approve": self.symbols_can_approve(),
            "symbols_have_authority": self.symbols_have_authority(),
            "recent_decisions": self.decisions[-8:],
        }
