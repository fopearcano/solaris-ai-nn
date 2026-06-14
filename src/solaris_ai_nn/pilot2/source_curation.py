"""Pilot-2 source curation -- select safe, bounded, analyzable read-only sources.

The :class:`CuratedSourceSet` applies curation rules (low privacy risk, clear
provenance, stable format, bounded rate, read-only, non-command content,
useful recurrence/variation, no secrets/credentials/private messages by
default) and records *why* each candidate was included or excluded. Synthetic/
semi-real/public/test streams are preferred first.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Substrings that exclude a source by default (secrets / private data).
_EXCLUDE_HINTS = ("secret", "password", "credential", "token", "api_key",
                  ".env", "private_key", "id_rsa", "ssh", "wallet",
                  "private_message", "dm_", "personal", "medical", "ssn")


@dataclass
class SourceCurationRule:
    """One curation rule with a human-readable rationale."""

    name: str
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


DEFAULT_RULES = (
    SourceCurationRule("low_privacy_risk", "no private/sensitive data"),
    SourceCurationRule("clear_provenance", "origin must be traceable"),
    SourceCurationRule("stable_format", "parseable, stable structure"),
    SourceCurationRule("bounded_event_rate", "events per poll are bounded"),
    SourceCurationRule("read_only_compatible", "never written to"),
    SourceCurationRule("non_command_content", "content is not a command"),
    SourceCurationRule("no_secrets", "no credentials/secrets/keys"),
    SourceCurationRule("prefer_synthetic_public", "synthetic/public first"),
)


@dataclass
class SourceCurationReport:
    """Which sources were included or excluded, and why."""

    included: List[Dict[str, Any]] = field(default_factory=list)
    excluded: List[Dict[str, Any]] = field(default_factory=list)
    rules: List[SourceCurationRule] = field(
        default_factory=lambda: list(DEFAULT_RULES))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "included_count": len(self.included),
            "excluded_count": len(self.excluded),
            "included": self.included,
            "excluded": self.excluded,
            "rules": [r.to_dict() for r in self.rules],
        }


@dataclass
class CuratedSourceSet:
    """Curates candidate sources into safe, analyzable read-only sources."""

    allow_sensitive: bool = False
    report: SourceCurationReport = field(default_factory=SourceCurationReport)

    def curate(self, candidates: List[Any]) -> SourceCurationReport:
        """Sort candidate source configs into included / excluded."""
        for cfg in candidates:
            ok, reason = self._evaluate(cfg)
            entry = {"source_id": getattr(cfg, "source_id", "?"),
                     "source_type": getattr(cfg, "source_type", "?"),
                     "reason": reason}
            if ok:
                self.report.included.append(entry)
            else:
                self.report.excluded.append(entry)
        # Prefer synthetic/public/test first within the included set.
        self.report.included.sort(
            key=lambda e: 0 if any(k in str(e["source_type"])
                                   for k in ("simulated", "synthetic",
                                             "manual")) else 1)
        return self.report

    def _evaluate(self, cfg: Any) -> Tuple[bool, str]:
        path = str(getattr(cfg, "path", "") or "")
        base = os.path.basename(path).lower()
        meta = getattr(cfg, "metadata", {}) or {}
        if not self.allow_sensitive and any(h in base for h in _EXCLUDE_HINTS):
            return False, "excluded: secret/sensitive-looking source"
        if meta.get("private") and not self.allow_sensitive:
            return False, "excluded: private source not approved"
        if meta.get("network"):
            return False, "excluded: network source prohibited"
        if not getattr(cfg, "read_only", True):
            return False, "excluded: not read-only"
        if not getattr(cfg, "provenance_label", ""):
            return False, "excluded: no provenance"
        return True, "included: read-only, provenanced, non-sensitive"

    def to_dict(self) -> Dict[str, Any]:
        return self.report.to_dict()
