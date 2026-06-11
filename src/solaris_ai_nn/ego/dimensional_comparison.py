"""Dimensional comparison -- six fixed axes, simple deterministic scoring.

Solaris_Ai's dimensional comparison becomes a small frame algebra: every
event or context is placed on six axes (temporal, scope, authority,
evidence, certainty, risk), frames can be compared with a deterministic
distance, and differences are explained in plain sentences. No embeddings,
no learned representation -- ordered value lists and index arithmetic.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class Dimension:
    TEMPORAL = "temporal"
    SCOPE = "scope"
    AUTHORITY = "authority"
    EVIDENCE = "evidence"
    CERTAINTY = "certainty"
    RISK = "risk"

    ALL = (TEMPORAL, SCOPE, AUTHORITY, EVIDENCE, CERTAINTY, RISK)


# Ordered value lists per dimension (order gives the within-axis distance).
DIMENSION_VALUES: Dict[str, tuple] = {
    Dimension.TEMPORAL: ("immediate", "recent", "session", "lifetime",
                         "replay_offline"),
    Dimension.SCOPE: ("internal", "simulated_body", "grid_world",
                      "stream_input", "sidecar_runtime",
                      "external_operator"),
    Dimension.AUTHORITY: ("observation", "suggestion",
                          "simulation_only_action", "internal_maintenance",
                          "governance_approval", "forbidden"),
    Dimension.EVIDENCE: ("real_observed", "simulated", "counterfactual",
                         "inferred", "unknown"),
    Dimension.CERTAINTY: ("high", "medium", "low", "unknown"),
    Dimension.RISK: ("low", "medium", "high", "prohibited"),
}


@dataclass
class DimensionalFrame:
    """One placement on all six axes."""

    label: str = ""
    temporal: str = "immediate"
    scope: str = "internal"
    authority: str = "observation"
    evidence: str = "unknown"
    certainty: str = "unknown"
    risk: str = "low"
    evidence_refs: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def value(self, dimension: str) -> str:
        return getattr(self, "scope" if dimension == Dimension.SCOPE
                       else dimension)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class DimensionalComparison:
    """Two frames, their distance, and the explained differences."""

    frame_a: DimensionalFrame
    frame_b: DimensionalFrame
    distance: float = 0.0
    differing_dimensions: List[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frame_a": self.frame_a.to_dict(),
            "frame_b": self.frame_b.to_dict(),
            "distance": self.distance,
            "differing_dimensions": list(self.differing_dimensions),
            "explanation": self.explanation,
        }


# Deterministic source/kind keyword -> frame field mappings.
_SCOPE_HINTS = (
    ("operator", "external_operator"), ("approval", "external_operator"),
    ("sidecar", "sidecar_runtime"), ("solaris", "sidecar_runtime"),
    ("stream", "stream_input"), ("pilot", "stream_input"),
    ("grid", "grid_world"), ("world", "grid_world"),
    ("body", "simulated_body"), ("embod", "simulated_body"),
)

_EVIDENCE_HINTS = (
    ("counterfactual", "counterfactual"), ("dream", "counterfactual"),
    ("replay", "simulated"), ("simulat", "simulated"),
    ("sandbox", "simulated"), ("predict", "inferred"),
    ("infer", "inferred"), ("observ", "real_observed"),
    ("stream", "real_observed"), ("operator", "real_observed"),
    ("sensor", "real_observed"),
)

_AUTHORITY_HINTS = (
    ("forbidden", "forbidden"), ("motor", "forbidden"),
    ("approval", "governance_approval"), ("approve", "governance_approval"),
    ("suggest", "suggestion"), ("desire", "suggestion"),
    ("candidate", "suggestion"), ("maintenance", "internal_maintenance"),
    ("checkpoint", "internal_maintenance"),
    ("action", "simulation_only_action"),
)

_TEMPORAL_HINTS = (
    ("replay", "replay_offline"), ("offline", "replay_offline"),
    ("dream", "replay_offline"), ("lifetime", "lifetime"),
    ("session", "session"), ("recent", "recent"),
)


def _hint(text: str, hints: tuple, default: str) -> str:
    lowered = text.lower()
    for needle, value in hints:
        if needle in lowered:
            return value
    return default


@dataclass
class DimensionalComparator:
    """Places events/contexts on the six axes and compares the frames."""

    frames_built: int = field(default=0, init=False)
    comparisons_made: int = field(default=0, init=False)
    recent_frames: List[Dict[str, Any]] = field(default_factory=list,
                                                init=False)

    # -- classification -----------------------------------------------------------

    def classify_event(self, event: Any) -> DimensionalFrame:
        """Deterministic frame for one event (dict or object)."""
        get = (event.get if isinstance(event, dict)
               else lambda k, d=None: getattr(event, k, d))
        source = str(get("source", "") or "")
        kind = str(get("kind", "") or get("type", "")
                   or type(event).__name__)
        label = str(get("label", "") or get("payload", "") or kind)
        text = " ".join([source, kind, label])

        frame = DimensionalFrame(
            label=label[:60],
            temporal=_hint(text, _TEMPORAL_HINTS, "immediate"),
            scope=_hint(text, _SCOPE_HINTS, "internal"),
            authority=_hint(text, _AUTHORITY_HINTS, "observation"),
            evidence=_hint(text, _EVIDENCE_HINTS, "unknown"),
            evidence_refs=[f"source:{source or 'unspecified'}",
                           f"kind:{kind}"])
        frame.certainty = ("high" if frame.evidence == "real_observed"
                           else "medium" if frame.evidence
                           in ("simulated", "counterfactual")
                           else "low" if frame.evidence == "inferred"
                           else "unknown")
        frame.risk = ("prohibited" if frame.authority == "forbidden"
                      else "medium" if frame.authority
                      == "simulation_only_action"
                      else "low")
        self._record(frame)
        return frame

    def classify_context(self, context: Optional[Dict[str, Any]] = None,
                         ) -> DimensionalFrame:
        """Frame for a whole running context (mode flags, not one event)."""
        ctx = dict(context or {})
        latent = str(ctx.get("latent_mode", "awake"))
        offline = latent in ("sleep", "dream", "replay", "consolidation")
        counterfactual = bool(ctx.get("counterfactual_active"))
        frame = DimensionalFrame(
            label=f"context:{ctx.get('perspective', 'runtime')}",
            temporal=("replay_offline" if offline or counterfactual
                      else "session"),
            scope=("grid_world" if ctx.get("embodied")
                   else "stream_input" if ctx.get("stream_active")
                   else "sidecar_runtime" if ctx.get("sidecar_attached")
                   else "internal"),
            authority=("forbidden" if ctx.get("emergency")
                       else "simulation_only_action" if ctx.get("embodied")
                       else "observation"),
            evidence=("counterfactual" if counterfactual
                      else "simulated" if offline or ctx.get("embodied")
                      else "real_observed" if ctx.get("stream_active")
                      or ctx.get("sidecar_attached")
                      else "inferred"),
            certainty=("high" if ctx.get("health_level") == "ok"
                       else "medium" if ctx.get("health_level")
                       else "unknown"),
            risk=("prohibited" if ctx.get("emergency")
                  else "high" if ctx.get("health_level") == "critical"
                  else "medium" if ctx.get("health_level") == "warning"
                  else "low"),
            evidence_refs=[f"latent_mode:{latent}",
                           f"health:{ctx.get('health_level', 'unknown')}"])
        self._record(frame)
        return frame

    # -- comparison ---------------------------------------------------------------

    def distance(self, frame_a: DimensionalFrame,
                 frame_b: DimensionalFrame) -> float:
        """Mean normalized index distance across the six axes, in [0, 1]."""
        total = 0.0
        for dimension in Dimension.ALL:
            values = DIMENSION_VALUES[dimension]
            a = frame_a.value(dimension)
            b = frame_b.value(dimension)
            ia = values.index(a) if a in values else len(values) - 1
            ib = values.index(b) if b in values else len(values) - 1
            total += abs(ia - ib) / (len(values) - 1)
        return round(total / len(Dimension.ALL), 4)

    def explain_difference(self, frame_a: DimensionalFrame,
                           frame_b: DimensionalFrame) -> str:
        parts: List[str] = []
        for dimension in Dimension.ALL:
            a = frame_a.value(dimension)
            b = frame_b.value(dimension)
            if a != b:
                parts.append(f"{dimension}: {a!r} vs {b!r}")
        if not parts:
            return ("The two frames agree on all six dimensions; they "
                    "occupy the same operational position.")
        return ("The frames differ on " + "; ".join(parts)
                + ". These are recorded operational placements, not "
                  "experiential comparisons.")

    def compare(self, a: Any, b: Any) -> DimensionalComparison:
        frame_a = a if isinstance(a, DimensionalFrame) \
            else self.classify_event(a)
        frame_b = b if isinstance(b, DimensionalFrame) \
            else self.classify_event(b)
        comparison = DimensionalComparison(
            frame_a=frame_a, frame_b=frame_b,
            distance=self.distance(frame_a, frame_b),
            differing_dimensions=[d for d in Dimension.ALL
                                  if frame_a.value(d) != frame_b.value(d)],
            explanation=self.explain_difference(frame_a, frame_b))
        self.comparisons_made += 1
        return comparison

    # -- bookkeeping --------------------------------------------------------------

    def _record(self, frame: DimensionalFrame) -> None:
        self.frames_built += 1
        self.recent_frames.append(frame.to_dict())
        self.recent_frames = self.recent_frames[-50:]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "frames_built": self.frames_built,
            "comparisons_made": self.comparisons_made,
            "dimensions": list(Dimension.ALL),
            "recent_frames": self.recent_frames[-5:],
        }
