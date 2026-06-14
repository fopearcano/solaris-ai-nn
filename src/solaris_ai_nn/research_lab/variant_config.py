"""Solaris variant config -- which modules a variant enables; safety is fixed.

A :class:`SolarisVariantConfig` is a set of module toggles describing one
architecture variant. External authority is always forbidden; governance and
safety invariants cannot be disabled for any profile that touches the sensory or
motor membranes; ablations may disable *cognitive* modules but never the hard
safety boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Dict, List


class VariantAuthority:
    INTERNAL_ONLY = "internal_only"
    SIMULATION_ONLY = "simulation_only"
    READ_ONLY = "read_only"
    SANDBOX_ONLY = "sandbox_only"
    FORBIDDEN_EXTERNAL = "forbidden_external"

    ALL = (INTERNAL_ONLY, SIMULATION_ONLY, READ_ONLY, SANDBOX_ONLY,
           FORBIDDEN_EXTERNAL)
    # Authorities a variant may actually hold (never external).
    RUNNABLE = frozenset({INTERNAL_ONLY, SIMULATION_ONLY, READ_ONLY,
                          SANDBOX_ONLY})


# The cognitive module toggles an ablation may turn off.
COGNITIVE_TOGGLES = (
    "enable_memory", "enable_world_model", "enable_proto_language",
    "enable_active_perception", "enable_hypothesis_engine", "enable_LOGOS",
    "enable_latent_replay", "enable_auto_regeneration", "enable_homeostasis",
    "enable_inner_map",
)
# Hard-safety toggles that cannot be disabled when membranes are active.
HARD_SAFETY_TOGGLES = ("enable_safety_invariants", "enable_governance")
MEMBRANE_TOGGLES = ("enable_sensory_membrane", "enable_motor_membrane")


@dataclass
class VariantModuleToggle:
    """One module on/off flag with whether it is a hard-safety toggle."""

    name: str
    enabled: bool = True
    hard_safety: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SolarisVariantConfig:
    """The module toggles describing one architecture variant."""

    label: str = "full"
    authority: str = VariantAuthority.SIMULATION_ONLY
    enable_memory: bool = True
    enable_world_model: bool = True
    enable_proto_language: bool = True
    enable_active_perception: bool = True
    enable_hypothesis_engine: bool = True
    enable_LOGOS: bool = True
    enable_latent_replay: bool = True
    enable_auto_regeneration: bool = True
    enable_homeostasis: bool = True
    enable_ego: bool = True
    enable_sensory_membrane: bool = False
    enable_motor_membrane: bool = False
    enable_safety_invariants: bool = True
    enable_governance: bool = True
    enable_inner_map: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # External authority is always forbidden.
        if self.authority not in VariantAuthority.RUNNABLE:
            raise ValueError(
                "external authority is forbidden; variant authority must be "
                "internal/simulation/read_only/sandbox only")
        # Governance/safety cannot be disabled for sensory/motor profiles.
        touches_membrane = (self.enable_sensory_membrane
                            or self.enable_motor_membrane)
        if touches_membrane and not (self.enable_safety_invariants
                                     and self.enable_governance):
            raise ValueError(
                "governance and safety invariants cannot be disabled for any "
                "profile that touches the sensory or motor membranes")

    @property
    def disabled_modules(self) -> List[str]:
        return [t for t in COGNITIVE_TOGGLES + MEMBRANE_TOGGLES + ("enable_ego",)
                if not getattr(self, t, True)]

    @property
    def enabled_modules(self) -> List[str]:
        all_toggles = (COGNITIVE_TOGGLES + HARD_SAFETY_TOGGLES
                       + MEMBRANE_TOGGLES + ("enable_ego",))
        return [t for t in all_toggles if getattr(self, t, False)]

    def hard_safety_enabled(self) -> bool:
        return self.enable_safety_invariants and self.enable_governance

    def disable(self, *toggles: str) -> "SolarisVariantConfig":
        """Return a copy with the named cognitive toggles disabled."""
        kwargs = {f.name: getattr(self, f.name) for f in fields(self)}
        for t in toggles:
            if t in HARD_SAFETY_TOGGLES:
                raise ValueError(f"cannot disable hard-safety toggle {t!r}")
            if t in {f.name for f in fields(self)}:
                kwargs[t] = False
        return SolarisVariantConfig(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__),
                "disabled_modules": self.disabled_modules,
                "enabled_modules": self.enabled_modules,
                "hard_safety_enabled": self.hard_safety_enabled()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SolarisVariantConfig":
        valid = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid})

    @classmethod
    def full(cls) -> "SolarisVariantConfig":
        return cls(label="full")

    @classmethod
    def minimal(cls) -> "SolarisVariantConfig":
        return cls(label="minimal", enable_memory=False, enable_world_model=False,
                   enable_proto_language=False, enable_active_perception=False,
                   enable_hypothesis_engine=False, enable_LOGOS=False,
                   enable_latent_replay=False, enable_auto_regeneration=False,
                   enable_homeostasis=False, enable_inner_map=False)
