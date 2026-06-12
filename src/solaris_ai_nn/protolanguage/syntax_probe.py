"""Syntax probe -- do recurring sequences behave like primitive grammar?

Type-level patterns (stimulus -> need -> action -> reaction; unknown ->
replay -> reduced unknown; boundary -> inhibition -> safe alternative)
are inferred from repeated sequences and then *tested* against later
traces. The vocabulary is deliberate: these are **proto-syntactic
regularities**, never human grammar, and a rule that fails held-out
validation is marked uncertain, not excused.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .pattern_naming import InternalPatternNamer


@dataclass
class ProtoSyntaxRule:
    """One type-level regularity with its support and its test record."""

    pattern: Tuple[str, ...]  # symbol types, in order
    rule_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    support: int = 0
    violations: int = 0
    confidence: float = 0.0
    validated: bool = False
    status: str = "candidate"  # candidate | validated | uncertain
    description: str = "proto-syntactic regularity"
    created_at: float = field(default_factory=time.time)

    def recompute(self) -> float:
        total = self.support + self.violations
        self.confidence = (round(min(0.9, self.support / total), 4)
                           if total else 0.0)
        return self.confidence

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "pattern": list(self.pattern),
                "note": "a proto-syntactic regularity over internal "
                        "symbols, not human grammar"}


def _types_of(tokens: List[str]) -> Tuple[str, ...]:
    """Token stream -> symbol-type stream via the deterministic parser."""
    types: List[str] = []
    for token in tokens:
        parsed = InternalPatternNamer.parse_token(token)
        types.append(parsed["symbol_type"] if parsed else "unknown")
    return tuple(types)


@dataclass
class SyntaxProbe:
    """Infers and tests type-level regularities."""

    min_support: int = 3
    rules: Dict[str, ProtoSyntaxRule] = field(default_factory=dict)
    rules_inferred: int = field(default=0, init=False)
    rules_failed: int = field(default=0, init=False)

    def infer_rules(self, sequences: List[Any],
                    ) -> List[ProtoSyntaxRule]:
        """Repeated token sequences -> candidate type-level rules."""
        pattern_counts: Dict[Tuple[str, ...], int] = {}
        for sequence in sequences:
            tokens = list(getattr(sequence, "tokens", sequence))
            count = int(getattr(sequence, "count", 1))
            if len(tokens) < 2:
                continue
            pattern = _types_of(tokens)
            pattern_counts[pattern] = (pattern_counts.get(pattern, 0)
                                       + count)
        new: List[ProtoSyntaxRule] = []
        for pattern, count in sorted(pattern_counts.items()):
            if count < self.min_support:
                continue
            key = ">".join(pattern)
            rule = self.rules.get(key)
            if rule is None:
                rule = ProtoSyntaxRule(pattern=pattern)
                self.rules[key] = rule
                self.rules_inferred += 1
                new.append(rule)
            rule.support += count
            rule.recompute()
        return new

    def score_rule(self, rule: ProtoSyntaxRule,
                   context: Optional[Dict[str, Any]] = None) -> float:
        del context  # scoring is support-based; context reserved
        return rule.recompute()

    def validate_rule(self, rule: ProtoSyntaxRule,
                      heldout_trace: List[List[str]]) -> bool:
        """Test the pattern against later traces; failure stays visible."""
        hits = 0
        misses = 0
        n = len(rule.pattern)
        for tokens in heldout_trace:
            types = _types_of(list(tokens))
            if len(types) < n:
                continue
            prefix_found = False
            for i in range(len(types) - n + 1):
                if types[i:i + n - 1] == rule.pattern[:-1]:
                    prefix_found = True
                    if types[i + n - 1] == rule.pattern[-1]:
                        hits += 1
                    else:
                        misses += 1
            del prefix_found
        rule.support += hits
        rule.violations += misses
        rule.recompute()
        if hits > 0 and rule.confidence >= 0.6:
            rule.validated = True
            rule.status = "validated"
            return True
        rule.validated = False
        rule.status = "uncertain"
        self.rules_failed += 1
        return False

    def validated_rules(self) -> List[ProtoSyntaxRule]:
        return [r for r in self.rules.values() if r.validated]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rule_count": len(self.rules),
            "validated_count": len(self.validated_rules()),
            "uncertain_count": sum(1 for r in self.rules.values()
                                   if r.status == "uncertain"),
            "rules_failed": self.rules_failed,
            "top_rules": [r.to_dict() for r in sorted(
                self.rules.values(), key=lambda r: -r.confidence)[:5]],
            "note": "proto-syntactic regularities tested against later "
                    "traces; not human grammar",
        }
