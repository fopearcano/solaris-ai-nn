"""Pilot-1 retention policy -- what to keep hot, compress, fossilize, or drop.

The :class:`RetentionPolicy` classifies pilot artifacts into retention
categories. Safety/emergency/identity/first-milestone/fossil evidence is
always retained; only temporary test files may be deleted, and never without a
summary/archive. Decisions are applied through auto-regeneration / state
hygiene where possible -- this module decides, it does not delete on its own.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class RetentionCategory:
    KEEP_HOT = "keep_hot"
    COMPRESS_TO_WARM = "compress_to_warm"
    CONSOLIDATE_TO_COLD = "consolidate_to_cold"
    FOSSILIZE = "fossilize"
    ARCHIVE = "archive"
    QUARANTINE = "quarantine"
    DELETE_TEMP_ONLY = "delete_temp_only"

    ALL = (KEEP_HOT, COMPRESS_TO_WARM, CONSOLIDATE_TO_COLD, FOSSILIZE,
           ARCHIVE, QUARANTINE, DELETE_TEMP_ONLY)


# Substrings that mark always-retained evidence.
_PROTECTED = ("incident", "emergency", "safety", "governance", "identity",
              "restart", "milestone", "fossil", "failure")
# Substrings that mark deletable temporary files.
_TEMP = (".tmp", ".temp", "tmp_", "scratch", "_cache", ".part")


@dataclass
class RetentionDecision:
    """One retention classification for a path."""

    path: str
    category: str
    protected: bool = False
    deletable: bool = False
    requires_archive: bool = False
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class RetentionPolicy:
    """Classifies artifacts into retention categories (decides, never deletes)."""

    decisions: List[RetentionDecision] = field(default_factory=list, init=False)

    def classify(self, path: str, age_days: float = 0.0,
                 is_evidence: bool = False) -> RetentionDecision:
        name = os.path.basename(path).lower()
        protected = is_evidence or any(p in name for p in _PROTECTED)
        is_temp = any(t in name for t in _TEMP)

        if protected:
            category = RetentionCategory.KEEP_HOT
            if "fossil" in name:
                category = RetentionCategory.FOSSILIZE
            decision = RetentionDecision(
                path=path, category=category, protected=True,
                deletable=False, requires_archive=False,
                reason="protected evidence is always retained")
        elif is_temp:
            decision = RetentionDecision(
                path=path, category=RetentionCategory.DELETE_TEMP_ONLY,
                deletable=True, reason="temporary file; safe to delete")
        elif age_days >= 90:
            decision = RetentionDecision(
                path=path, category=RetentionCategory.ARCHIVE,
                requires_archive=True,
                reason="old artifact; archive before any removal")
        elif age_days >= 30:
            decision = RetentionDecision(
                path=path, category=RetentionCategory.CONSOLIDATE_TO_COLD,
                requires_archive=True,
                reason="aging artifact; consolidate to cold storage")
        elif age_days >= 7:
            decision = RetentionDecision(
                path=path, category=RetentionCategory.COMPRESS_TO_WARM,
                reason="warm artifact; compress to save space")
        else:
            decision = RetentionDecision(
                path=path, category=RetentionCategory.KEEP_HOT,
                reason="recent artifact; keep hot")
        self.decisions.append(decision)
        self.decisions = self.decisions[-1000:]
        return decision

    def can_delete(self, decision: RetentionDecision,
                   archived: bool = False) -> bool:
        """A path may be deleted only if temp-only, or archived non-evidence."""
        if decision.protected:
            return False
        if decision.deletable:
            return True
        if decision.requires_archive:
            return archived
        return False

    def autoregeneration_context(self) -> Dict[str, Any]:
        """A context dict auto-regeneration/state hygiene can apply."""
        compress = [d.path for d in self.decisions
                    if d.category == RetentionCategory.COMPRESS_TO_WARM]
        consolidate = [d.path for d in self.decisions
                       if d.category == RetentionCategory.CONSOLIDATE_TO_COLD]
        delete = [d.path for d in self.decisions if d.deletable]
        return {"compress": compress, "consolidate": consolidate,
                "delete_temp": delete, "memory_bloat": bool(compress
                                                            or consolidate)}

    def snapshot(self) -> Dict[str, Any]:
        by_cat: Dict[str, int] = {}
        for d in self.decisions:
            by_cat[d.category] = by_cat.get(d.category, 0) + 1
        return {"decision_count": len(self.decisions), "by_category": by_cat,
                "recent": [d.to_dict() for d in self.decisions[-8:]]}
