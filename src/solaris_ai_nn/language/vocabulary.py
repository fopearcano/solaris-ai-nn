"""Controlled internal vocabulary -- the closed label set of the language layer.

Categories name *where* something happened; predicates name *what kind* of
thing happened. Anything outside the controlled sets passes through a safe
fallback (category -> "unknown"; predicate -> "influenced", the weakest
hedged relation) and the original label is preserved in metadata by callers
that care. No free-form labels leak into traces.
"""

from __future__ import annotations

CATEGORIES = frozenset({
    "signal", "substrate", "readout", "habit", "synthesis", "plasticity",
    "memory", "inner_map", "embodiment", "integration", "safety",
    "continuity", "unknown",
})

PREDICATES = frozenset({
    "received", "encoded_as", "updated", "suggested", "reinforced", "pruned",
    "blocked", "persisted", "restored", "drifted", "stabilized", "explored",
    "failed", "succeeded", "caused", "influenced",
})

FALLBACK_CATEGORY = "unknown"
# The weakest relation in the controlled set: safe for unproven claims.
FALLBACK_PREDICATE = "influenced"


def normalize_category(category: str) -> str:
    """Return the category if controlled, else the safe fallback."""
    category = str(category).strip().lower()
    return category if category in CATEGORIES else FALLBACK_CATEGORY


def normalize_predicate(predicate: str) -> str:
    """Return the predicate if controlled, else the hedged fallback."""
    predicate = str(predicate).strip().lower()
    return predicate if predicate in PREDICATES else FALLBACK_PREDICATE


def is_controlled(category: str, predicate: str) -> bool:
    return (str(category).lower() in CATEGORIES
            and str(predicate).lower() in PREDICATES)
