"""Ablation matrix -- which modules matter, tested by removing them.

The :class:`AblationMatrix` enumerates ablation cases (full system, minimal
spine, no-memory, no-proto-language, ..., full-minus-one-each), each a
:class:`SolarisVariantConfig` with exactly the named modules disabled. Hard
safety layers always remain active; a removed module is recorded as *unavailable*
(not silently ignored); and every result carries limitations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .variant_config import COGNITIVE_TOGGLES, SolarisVariantConfig


# (case name, toggles to disable). Hard-safety toggles are never disabled.
_ABLATION_SPECS = {
    "full_system": (),
    "minimal_spine_only": ("enable_memory", "enable_world_model",
                           "enable_proto_language", "enable_active_perception",
                           "enable_hypothesis_engine", "enable_LOGOS",
                           "enable_latent_replay", "enable_auto_regeneration",
                           "enable_homeostasis", "enable_inner_map"),
    "no_memory": ("enable_memory",),
    "no_world_model": ("enable_world_model",),
    "no_proto_language": ("enable_proto_language",),
    "no_active_perception": ("enable_active_perception",),
    "no_hypothesis_engine": ("enable_hypothesis_engine",),
    "no_LOGOS": ("enable_LOGOS",),
    "no_latent_replay": ("enable_latent_replay",),
    "no_auto_regeneration": ("enable_auto_regeneration",),
    "no_homeostasis": ("enable_homeostasis",),
    "no_sensory_membrane": ("enable_sensory_membrane",),
    "no_motor_membrane": ("enable_motor_membrane",),
    "no_synthesis": ("enable_LOGOS",),  # synthesis lives under LOGOS complexity
    "safety_only": ("enable_memory", "enable_world_model",
                    "enable_proto_language", "enable_active_perception",
                    "enable_hypothesis_engine", "enable_LOGOS",
                    "enable_latent_replay", "enable_auto_regeneration",
                    "enable_homeostasis", "enable_inner_map", "enable_ego"),
}


@dataclass
class AblationCase:
    """One ablation: a variant with exactly the named modules disabled."""

    name: str
    variant: SolarisVariantConfig
    disabled: List[str] = field(default_factory=list)
    note: str = ""

    @property
    def unavailable_modules(self) -> List[str]:
        # A disabled module is recorded as unavailable, never silently ignored.
        return list(self.disabled)

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "disabled": list(self.disabled),
                "unavailable_modules": self.unavailable_modules,
                "hard_safety_enabled": self.variant.hard_safety_enabled(),
                "note": self.note}


@dataclass
class AblationResult:
    """The recorded outcome of one ablation case."""

    name: str
    disabled: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    hard_safety_enabled: bool = True
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.limitations:
            self.limitations = [
                "Single bounded run; differences are observed, not causal.",
                "A disabled module is unavailable, not proven worthless.",
                "Hard safety layers remained enabled throughout.",
            ]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class AblationMatrix:
    """Holds the ablation cases; hard safety always remains enabled."""

    base: SolarisVariantConfig = field(default_factory=SolarisVariantConfig.full)
    cases: Dict[str, AblationCase] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.cases:
            for name, toggles in _ABLATION_SPECS.items():
                self._add_case(name, toggles)
            self._add_full_minus_one_each()
            # Membrane-flavoured ablation cases (cognitive removals on a body).
            self._add_membrane_cases()

    def _disable(self, toggles) -> SolarisVariantConfig:
        # Only cognitive/membrane/ego toggles may be disabled; never hard safety.
        cognitive = tuple(t for t in toggles if t in COGNITIVE_TOGGLES
                          or t in ("enable_sensory_membrane",
                                   "enable_motor_membrane", "enable_ego"))
        variant = self.base
        if cognitive:
            variant = variant.disable(*[t for t in cognitive
                                        if t in COGNITIVE_TOGGLES])
            # membrane/ego toggles handled via a fresh copy
            kwargs = variant.to_dict()
            for t in cognitive:
                if t in ("enable_sensory_membrane", "enable_motor_membrane",
                         "enable_ego"):
                    kwargs[t] = False
            variant = SolarisVariantConfig.from_dict(kwargs)
        return variant

    def _add_case(self, name: str, toggles) -> None:
        variant = self._disable(toggles)
        variant.label = name
        self.cases[name] = AblationCase(name=name, variant=variant,
                                        disabled=list(toggles))

    def _add_full_minus_one_each(self) -> None:
        for toggle in COGNITIVE_TOGGLES:
            name = f"full_minus_{toggle.replace('enable_', '')}"
            self._add_case(name, (toggle,))
        # A representative composite case the spec names directly.
        self.cases["full_minus_one_each"] = AblationCase(
            name="full_minus_one_each", variant=self.base,
            disabled=[], note="meta-case: see each full_minus_* case")

    def _add_membrane_cases(self) -> None:
        from dataclasses import replace as _replace

        # nursery_without_sensory / sensory_without_nursery are membrane flavours.
        sensory = SolarisVariantConfig.from_dict(
            {**self.base.to_dict(), "label": "sensory_without_nursery",
             "enable_sensory_membrane": True})
        self.cases["sensory_without_nursery"] = AblationCase(
            name="sensory_without_nursery", variant=sensory,
            disabled=[], note="sensory membrane on, nursery off")
        self.cases["nursery_without_sensory"] = AblationCase(
            name="nursery_without_sensory", variant=self.base,
            disabled=["enable_sensory_membrane"],
            note="nursery on, sensory membrane off")
        # gridworld_without_proto_language / _hypothesis_engine.
        for mod in ("enable_proto_language", "enable_hypothesis_engine"):
            label = f"gridworld_without_{mod.replace('enable_', '')}"
            v = SolarisVariantConfig.from_dict(
                {**self.base.disable(mod).to_dict(), "label": label,
                 "enable_motor_membrane": True})
            self.cases[label] = AblationCase(name=label, variant=v,
                                             disabled=[mod],
                                             note="gridworld body, module off")

    def case_names(self) -> List[str]:
        return sorted(self.cases)

    def get(self, name: str) -> Optional[AblationCase]:
        return self.cases.get(name)

    def all_hard_safety_enabled(self) -> bool:
        return all(c.variant.hard_safety_enabled()
                   for c in self.cases.values())

    def snapshot(self) -> Dict[str, Any]:
        return {"case_count": len(self.cases), "cases": self.case_names(),
                "all_hard_safety_enabled": self.all_hard_safety_enabled()}
