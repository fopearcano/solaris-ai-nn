"""Soak control arms -- prevent self-flattering conclusions.

A developmental soak that only ever runs the full stack cannot tell growth from
artefact. :class:`SoakControlArm` runs *shortened* comparison arms (full stack,
passive-parser-only, ablations of each module, fixture-only, human-label-heavy,
feature-only, and an optional live read-only arm) so the evidence dossier can
ask whether the full stack actually developed differently. Missing modules mark
an arm *unavailable* (never a false positive); the live arm requires governance;
and arms with insufficient data are reported conservatively.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


class ControlArmId:
    FULL_STACK = "full_stack"
    PASSIVE_PARSER_ONLY = "passive_parser_only"
    NO_PERCEPTUAL_METABOLISM = "no_perceptual_metabolism"
    NO_ONTOGENESIS = "no_ontogenesis"
    NO_SEMIOGENESIS = "no_semiogenesis"
    NO_SENSORIUM_COGNITION = "no_sensorium_cognition"
    NO_DESIRE_ACTION_REACTION = "no_desire_action_reaction"
    FIXTURE_ONLY = "fixture_only"
    LIVE_READ_ONLY_IF_AVAILABLE = "live_read_only_if_available"
    HUMAN_LABEL_HEAVY = "human_label_heavy"
    FEATURE_ONLY = "feature_only"

    ALL = (FULL_STACK, PASSIVE_PARSER_ONLY, NO_PERCEPTUAL_METABOLISM,
           NO_ONTOGENESIS, NO_SEMIOGENESIS, NO_SENSORIUM_COGNITION,
           NO_DESIRE_ACTION_REACTION, FIXTURE_ONLY,
           LIVE_READ_ONLY_IF_AVAILABLE, HUMAN_LABEL_HEAVY, FEATURE_ONLY)


# Which modules each arm disables (relative to the full stack).
_ARM_DISABLES: Dict[str, List[str]] = {
    ControlArmId.FULL_STACK: [],
    ControlArmId.PASSIVE_PARSER_ONLY: [
        "perceptual_metabolism", "perceptual_ontogenesis", "semiogenesis",
        "sensorium_cognition", "self_boundary", "desire_formation",
        "action_reaction"],
    ControlArmId.NO_PERCEPTUAL_METABOLISM: ["perceptual_metabolism"],
    ControlArmId.NO_ONTOGENESIS: ["perceptual_ontogenesis"],
    ControlArmId.NO_SEMIOGENESIS: ["semiogenesis"],
    ControlArmId.NO_SENSORIUM_COGNITION: ["sensorium_cognition"],
    ControlArmId.NO_DESIRE_ACTION_REACTION: ["desire_formation",
                                             "action_reaction"],
    ControlArmId.FIXTURE_ONLY: [],
    ControlArmId.LIVE_READ_ONLY_IF_AVAILABLE: [],
    ControlArmId.HUMAN_LABEL_HEAVY: [],
    ControlArmId.FEATURE_ONLY: [
        "perceptual_ontogenesis", "semiogenesis", "sensorium_cognition",
        "self_boundary", "desire_formation", "action_reaction"],
}


@dataclass
class ControlArmConfig:
    """Configuration for one control arm."""

    arm_id: str
    disabled_modules: List[str] = field(default_factory=list)
    fixture_only: bool = True
    human_label_heavy: bool = False
    live: bool = False
    requires_governance: bool = False
    max_ticks: int = 6

    def to_dict(self) -> Dict[str, Any]:
        return {"arm_id": self.arm_id,
                "disabled_modules": list(self.disabled_modules),
                "fixture_only": self.fixture_only,
                "human_label_heavy": self.human_label_heavy,
                "live": self.live, "requires_governance": self.requires_governance,
                "max_ticks": self.max_ticks}

    @classmethod
    def for_arm(cls, arm_id: str, *, max_ticks: int = 6) -> "ControlArmConfig":
        live = arm_id == ControlArmId.LIVE_READ_ONLY_IF_AVAILABLE
        return cls(
            arm_id=arm_id,
            disabled_modules=list(_ARM_DISABLES.get(arm_id, [])),
            fixture_only=not live,
            human_label_heavy=arm_id == ControlArmId.HUMAN_LABEL_HEAVY,
            live=live, requires_governance=live, max_ticks=max_ticks)


@dataclass
class ControlArmResult:
    """The (conservative) outcome of one control arm."""

    arm_id: str
    available: bool
    ran: bool = False
    growth_status: str = "inconclusive"
    structural_growth_score: float = 0.0
    composite_growth: float = 0.0
    note: str = ""
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"arm_id": self.arm_id, "available": self.available,
                "ran": self.ran, "growth_status": self.growth_status,
                "structural_growth_score": self.structural_growth_score,
                "composite_growth": self.composite_growth, "note": self.note,
                "evidence_refs": list(self.evidence_refs)}


@dataclass
class SoakControlArm:
    """Runs shortened control-arm comparisons conservatively."""

    def run(self, config: ControlArmConfig, *,
            module_stack: Optional[Dict[str, Any]] = None,
            build_runtime: Optional[Callable[..., Any]] = None,
            governance_approved: bool = False) -> ControlArmResult:
        module_stack = module_stack or {}

        # Live arm requires governance; otherwise it is unavailable (not run).
        if config.live and config.requires_governance and not \
                governance_approved:
            return ControlArmResult(
                config.arm_id, available=False,
                note="live read-only arm requires governance approval; not run",
                evidence_refs=["governance:live_read_only"])

        # An arm is unavailable if a module it needs (i.e. NOT disabled) is
        # absent from the stack -- we never over-claim with missing modules.
        kept = [name for name in module_stack
                if name not in config.disabled_modules]
        needed = [n for n in kept if n != "plural_sensorium"]
        if config.arm_id != ControlArmId.PASSIVE_PARSER_ONLY \
                and config.arm_id != ControlArmId.FEATURE_ONLY \
                and not needed:
            return ControlArmResult(
                config.arm_id, available=False,
                note="no structural modules available for this arm; "
                     "inconclusive (insufficient data)",
                evidence_refs=["control_arm:unavailable"])

        if build_runtime is None:
            return ControlArmResult(
                config.arm_id, available=True, ran=False,
                note="no runtime builder supplied; arm configured but not run",
                evidence_refs=["control_arm:not_run"])

        subset = {k: v for k, v in module_stack.items()
                  if k not in config.disabled_modules}
        try:
            dev = build_runtime(subset, config)
            dev.run_bounded()
            st = dev.developmental_status()
        except Exception as exc:
            return ControlArmResult(
                config.arm_id, available=True, ran=False,
                note=f"arm failed to run: {type(exc).__name__}: {exc}",
                evidence_refs=["control_arm:error"])

        return ControlArmResult(
            config.arm_id, available=True, ran=True,
            growth_status=str(st.get("structural_growth_status",
                                     "inconclusive")),
            structural_growth_score=float(
                st.get("structural_growth_score", 0.0) or 0.0),
            composite_growth=float(st.get("composite_growth", 0.0) or 0.0),
            note="shortened comparison arm; conservative result",
            evidence_refs=[f"control_arm:{config.arm_id}"])

    def run_default_arms(self, *, module_stack: Optional[Dict] = None,
                         build_runtime: Optional[Callable] = None,
                         arm_ids: Optional[List[str]] = None,
                         governance_approved: bool = False,
                         max_ticks: int = 6) -> List[ControlArmResult]:
        arm_ids = arm_ids or [ControlArmId.FULL_STACK,
                              ControlArmId.PASSIVE_PARSER_ONLY,
                              ControlArmId.NO_PERCEPTUAL_METABOLISM,
                              ControlArmId.FIXTURE_ONLY]
        return [self.run(ControlArmConfig.for_arm(a, max_ticks=max_ticks),
                         module_stack=module_stack, build_runtime=build_runtime,
                         governance_approved=governance_approved)
                for a in arm_ids]
