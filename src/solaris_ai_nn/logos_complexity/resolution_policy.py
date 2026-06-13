"""Resolution policy -- which resolution path to take for a tension, by mode.

The :class:`ResolutionPolicy` chooses, per mode, whether a tension is
preserved, synthesized, stabilized, or routed elsewhere. Safety/boundary
tensions dominate curiosity tensions, an emergency blocks synthesis except
stabilization/shutdown, and some tensions are deliberately preserved.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .synthesis import SynthesisCandidate, SynthesisType
from .tension import LogosTension, TensionType


class ResolutionMode:
    OBSERVE_ONLY = "observe_only"
    PRESERVE_TENSION = "preserve_tension"
    BALANCED_RESOLUTION = "balanced_resolution"
    SYNTHESIS_PREFERRED = "synthesis_preferred"
    STABILIZATION_PREFERRED = "stabilization_preferred"
    EMERGENCY_STABILIZATION = "emergency_stabilization"

    ALL = (OBSERVE_ONLY, PRESERVE_TENSION, BALANCED_RESOLUTION,
           SYNTHESIS_PREFERRED, STABILIZATION_PREFERRED,
           EMERGENCY_STABILIZATION)


# Synthesis types allowed under emergency stabilization.
_EMERGENCY_ALLOWED = frozenset({
    SynthesisType.STABILIZE_EXECUTIVE_POLICY,
    SynthesisType.REQUEST_AUTO_REGENERATION,
    SynthesisType.REQUEST_MEMORY_CONSOLIDATION,
    SynthesisType.PRESERVE_TENSION, SynthesisType.NO_SYNTHESIS,
})


@dataclass
class ResolutionDecision:
    """The chosen candidate (or preservation) for a tension."""

    tension_id: str
    mode: str
    candidate: Optional[SynthesisCandidate] = None
    apply_allowed: bool = False
    preserve: bool = False
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"tension_id": self.tension_id, "mode": self.mode,
                "candidate": (self.candidate.to_dict()
                              if self.candidate else None),
                "apply_allowed": self.apply_allowed,
                "preserve": self.preserve, "reason": self.reason}


@dataclass
class ResolutionPolicy:
    """Decides a bounded resolution path for a tension."""

    mode: str = ResolutionMode.BALANCED_RESOLUTION

    def __post_init__(self) -> None:
        if self.mode not in ResolutionMode.ALL:
            raise ValueError(f"unknown resolution mode {self.mode!r}")

    def _effective_mode(self, context: Dict[str, Any]) -> str:
        ctx = dict(context or {})
        if ctx.get("emergency") or ctx.get("emergency_stop_requested") \
                or ctx.get("health_level") == "critical":
            return ResolutionMode.EMERGENCY_STABILIZATION
        return self.mode

    def decide(self, tension: LogosTension,
               candidates: List[SynthesisCandidate],
               context: Optional[Dict[str, Any]] = None) -> ResolutionDecision:
        ctx = dict(context or {})
        mode = self._effective_mode(ctx)
        decision = ResolutionDecision(tension_id=tension.tension_id,
                                      mode=mode)

        if mode == ResolutionMode.OBSERVE_ONLY:
            decision.preserve = True
            decision.reason = "observe-only: tension recorded, not resolved"
            return decision

        # Safety/boundary tensions are preserved, not synthesized away.
        if tension.is_safety_dominant and mode != \
                ResolutionMode.EMERGENCY_STABILIZATION:
            preserve = self._find(candidates, SynthesisType.PRESERVE_TENSION)
            decision.candidate = preserve
            decision.preserve = True
            decision.reason = ("safety/boundary tension dominates; preserved "
                               "rather than synthesized")
            return decision

        if mode == ResolutionMode.PRESERVE_TENSION:
            decision.candidate = self._find(
                candidates, SynthesisType.PRESERVE_TENSION)
            decision.preserve = True
            decision.reason = "preserve-tension mode"
            return decision

        if mode == ResolutionMode.EMERGENCY_STABILIZATION:
            allowed = [c for c in candidates
                       if c.synthesis_type in _EMERGENCY_ALLOWED]
            if allowed:
                decision.candidate = sorted(
                    allowed, key=lambda c: c.expected_risk)[0]
                decision.apply_allowed = True
                decision.reason = ("emergency: only stabilization/"
                                   "preservation is applied")
            else:
                decision.preserve = True
                decision.reason = ("emergency: speculative synthesis blocked; "
                                   "tension preserved")
            return decision

        # Balanced / synthesis-preferred / stabilization-preferred.
        candidate = self._pick(tension, candidates, mode, ctx)
        decision.candidate = candidate
        if candidate is None:
            decision.preserve = True
            decision.reason = "no candidate; tension preserved"
        elif candidate.synthesis_type == SynthesisType.PRESERVE_TENSION:
            decision.preserve = True
            decision.apply_allowed = True
            decision.reason = "tension preserved as productive"
        else:
            decision.apply_allowed = not (
                candidate.requires_governance
                and not ctx.get("governance_approved"))
            decision.reason = (
                f"{mode}: {candidate.synthesis_type}"
                + ("" if decision.apply_allowed
                   else " (needs governance approval)"))
        return decision

    def _pick(self, tension: LogosTension,
              candidates: List[SynthesisCandidate], mode: str,
              ctx: Dict[str, Any]) -> Optional[SynthesisCandidate]:
        if not candidates:
            return None
        if mode == ResolutionMode.STABILIZATION_PREFERRED:
            stab = self._find(candidates,
                              SynthesisType.STABILIZE_EXECUTIVE_POLICY) \
                or self._find(candidates, SynthesisType.PRESERVE_TENSION)
            if stab is not None:
                return stab
        # High ambiguity -> active sampling; repeated contradiction ->
        # hypothesis; memory pressure -> consolidation (data-driven hints).
        if tension.tension_type == TensionType.SYMBOL_AMBIGUITY:
            sampling = self._find(candidates,
                                  SynthesisType.REQUEST_ACTIVE_SAMPLING)
            if sampling is not None:
                return sampling
        if tension.tension_type in (TensionType.WORLD_MODEL_CONTRADICTION,
                                    TensionType.PREDICTION_FAILURE):
            hyp = self._find(candidates, SynthesisType.CREATE_HYPOTHESIS)
            if hyp is not None and mode != ResolutionMode.PRESERVE_TENSION:
                return hyp
        # Default: lowest-risk reversible candidate.
        return sorted(candidates, key=lambda c: (c.expected_risk,
                                                 0 if c.reversible else 1))[0]

    @staticmethod
    def _find(candidates: List[SynthesisCandidate],
              synthesis_type: str) -> Optional[SynthesisCandidate]:
        for c in candidates:
            if c.synthesis_type == synthesis_type:
                return c
        return None

    def set_mode(self, mode: str) -> None:
        if mode not in ResolutionMode.ALL:
            raise ValueError(f"unknown resolution mode {mode!r}")
        self.mode = mode

    def snapshot(self) -> Dict[str, Any]:
        return {"mode": self.mode}
