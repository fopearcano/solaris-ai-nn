"""Operational identity -- anchors and runtime continuity, not personhood.

Solaris_Ai treats Ego as a necessary forced construct created by continuous
I/O and differentiation. Here that becomes a set of concrete *identity
anchors* (run id, session id, substrate identity, state paths, signatures of
the Inner MAP / world model / governance policy, operator and sidecar
references) plus a continuity score over them. Identity in this module means
exactly one thing: **operational runtime continuity**. Anchors that mismatch
produce uncertainty, never a metaphysical claim -- the system may say
"runtime continuity holds" and must never say "same self" without that
qualification.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# The anchor names tracked, in deterministic order.
ANCHOR_NAMES = (
    "run_id",
    "session_id",
    "substrate_identity",
    "state_path",
    "inner_map_signature",
    "world_model_signature",
    "governance_policy_signature",
    "operator_session",
    "continuity_log",
    "body_schema",
    "sidecar_identity",
)

# Anchors that are *expected* to change across sessions/restarts; a change
# here lowers confidence slightly but is not a mismatch warning by itself.
SESSION_SCOPED_ANCHORS = frozenset({"session_id", "operator_session",
                                    "sidecar_identity"})

IDENTITY_NOTE = ("identity here is operational runtime continuity over "
                 "recorded anchors, not personhood or a metaphysical self")


def signature_of(value: Any) -> str:
    """A short deterministic signature for any JSON-able structure."""
    try:
        payload = json.dumps(value, sort_keys=True, default=str)
    except (TypeError, ValueError):
        payload = repr(value)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass
class IdentityAnchor:
    """One concrete fact the running system is anchored to."""

    name: str
    value: str = ""
    source: str = ""
    captured_at: float = field(default_factory=time.time)

    def matches(self, other: Optional["IdentityAnchor"]) -> bool:
        return other is not None and self.value == other.value

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class IdentityContinuityScore:
    """The comparison between current and previous anchors."""

    score: float = 1.0
    matched: List[str] = field(default_factory=list)
    mismatched: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    note: str = IDENTITY_NOTE

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class IdentityState:
    """Current vs previous anchors, with continuity accounting."""

    anchors: Dict[str, IdentityAnchor] = field(default_factory=dict)
    previous_anchors: Dict[str, IdentityAnchor] = field(default_factory=dict)
    continuity_score: float = 1.0
    mismatch_count: int = 0
    restored_from_checkpoint: bool = False
    restart_gap_detected: bool = False
    identity_warnings: List[str] = field(default_factory=list)
    identity_confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    # -- capture ------------------------------------------------------------------

    def capture_anchors(self, context: Optional[Dict[str, Any]] = None,
                        ) -> Dict[str, IdentityAnchor]:
        """Read anchors from a context dict (missing values stay absent)."""
        ctx = dict(context or {})
        new: Dict[str, IdentityAnchor] = {}
        sources = {
            "run_id": "lifecycle", "session_id": "lifecycle",
            "substrate_identity": "substrate", "state_path": "persistence",
            "inner_map_signature": "inner_map",
            "world_model_signature": "world_model",
            "governance_policy_signature": "governance",
            "operator_session": "operator",
            "continuity_log": "persistence", "body_schema": "embodiment",
            "sidecar_identity": "sidecar",
        }
        for name in ANCHOR_NAMES:
            value = ctx.get(name)
            if value is None:
                continue
            if not isinstance(value, str):
                value = signature_of(value)
            new[name] = IdentityAnchor(name=name, value=str(value),
                                       source=sources.get(name, "context"))
        return new

    # -- update -------------------------------------------------------------------

    def update(self, context: Optional[Dict[str, Any]] = None,
               ) -> IdentityContinuityScore:
        """Capture fresh anchors and score continuity against the last set."""
        ctx = dict(context or {})
        new = self.capture_anchors(ctx)
        if self.anchors:
            self.previous_anchors = dict(self.anchors)
        result = self._compare(new, self.previous_anchors)
        self.anchors = new
        self.restored_from_checkpoint = bool(
            ctx.get("restored_from_checkpoint", False))
        self.restart_gap_detected = bool(
            ctx.get("restart_gap_detected", False))
        if self.restart_gap_detected:
            result.warnings.append(
                "a runtime continuity gap was detected between sessions")
            result.score = round(max(0.0, result.score - 0.2), 4)
        if self.restored_from_checkpoint:
            result.warnings.append(
                "state was restored from a checkpoint; continuity is "
                "checkpoint-mediated")
        self.continuity_score = result.score
        self.mismatch_count += len([m for m in result.mismatched
                                    if m not in SESSION_SCOPED_ANCHORS])
        # Only genuine uncertainty persists as an identity warning;
        # informational notes (first capture, checkpoint-mediated
        # continuity) stay in the returned score only.
        for warning in result.warnings:
            if ("mismatch" in warning or "gap" in warning) \
                    and warning not in self.identity_warnings:
                self.identity_warnings.append(warning)
        self.identity_warnings = self.identity_warnings[-20:]
        self.identity_confidence = round(
            max(0.0, min(1.0, result.score
                         - 0.05 * len(result.missing))), 4)
        return result

    def _compare(self, new: Dict[str, IdentityAnchor],
                 old: Dict[str, IdentityAnchor]) -> IdentityContinuityScore:
        if not old:
            return IdentityContinuityScore(
                score=1.0, matched=sorted(new),
                warnings=(["no previous anchors recorded; continuity is "
                           "asserted for this session only"]
                          if new else
                          ["no identity anchors available; identity is "
                           "unknown"]))
        matched: List[str] = []
        mismatched: List[str] = []
        missing: List[str] = []
        warnings: List[str] = []
        weight_total = 0.0
        weight_hit = 0.0
        for name in ANCHOR_NAMES:
            current = new.get(name)
            previous = old.get(name)
            if current is None and previous is None:
                continue
            weight = 0.4 if name in SESSION_SCOPED_ANCHORS else 1.0
            weight_total += weight
            if current is None:
                missing.append(name)
                continue
            if previous is None:
                matched.append(name)  # newly observed anchor, no conflict
                weight_hit += weight
                continue
            if current.matches(previous):
                matched.append(name)
                weight_hit += weight
            else:
                mismatched.append(name)
                if name in SESSION_SCOPED_ANCHORS:
                    weight_hit += weight * 0.5  # expected to rotate
                else:
                    warnings.append(
                        f"identity anchor {name!r} mismatches the previous "
                        f"value; runtime continuity is uncertain")
        score = round(weight_hit / weight_total, 4) if weight_total else 0.0
        return IdentityContinuityScore(score=score, matched=matched,
                                       mismatched=mismatched,
                                       missing=missing, warnings=warnings)

    # -- views --------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        return {
            "anchor_count": len(self.anchors),
            "continuity_score": self.continuity_score,
            "identity_confidence": self.identity_confidence,
            "mismatch_count": self.mismatch_count,
            "restored_from_checkpoint": self.restored_from_checkpoint,
            "restart_gap_detected": self.restart_gap_detected,
            "warnings": list(self.identity_warnings),
            "note": IDENTITY_NOTE,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anchors": {k: v.to_dict() for k, v in self.anchors.items()},
            "previous_anchors": {k: v.to_dict()
                                 for k, v in self.previous_anchors.items()},
            "continuity_score": self.continuity_score,
            "mismatch_count": self.mismatch_count,
            "restored_from_checkpoint": self.restored_from_checkpoint,
            "restart_gap_detected": self.restart_gap_detected,
            "identity_warnings": list(self.identity_warnings),
            "identity_confidence": self.identity_confidence,
            "metadata": dict(self.metadata),
            "note": IDENTITY_NOTE,
        }
