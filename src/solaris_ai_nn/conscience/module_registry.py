"""Module registry -- a typed inventory of the runtime's modules.

The :class:`ConscienceModuleRegistry` knows which packages exist, which are
enabled, what each can do (capabilities), and how they depend on one another.
It detects availability by import probe, registers partial configurations,
exposes missing modules, validates dependencies, and produces a topology --
so the runtime can run a partial config without faking absent modules.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ModuleCapability:
    STIMULUS_SOURCE = "stimulus_source"
    SIGNAL_PROCESSOR = "signal_processor"
    MEMORY = "memory"
    WORLD_MODEL = "world_model"
    HOMEOSTASIS = "homeostasis"
    EXECUTIVE = "executive"
    EGO_BOUNDARY = "ego_boundary"
    LATENT = "latent"
    DEVELOPMENTAL = "developmental"
    PROTO_LANGUAGE = "proto_language"
    ECOLOGY = "ecology"
    ACTIVE_PERCEPTION = "active_perception"
    HYPOTHESIS = "hypothesis"
    LOGOS = "logos"
    AUTOREGENERATION = "autoregeneration"
    GOVERNANCE = "governance"
    OPS = "ops"
    EVALUATION = "evaluation"
    COMMUNICATION = "communication"
    LLM_ADAPTER_OPTIONAL = "llm_adapter_optional"

    ALL = (STIMULUS_SOURCE, SIGNAL_PROCESSOR, MEMORY, WORLD_MODEL,
           HOMEOSTASIS, EXECUTIVE, EGO_BOUNDARY, LATENT, DEVELOPMENTAL,
           PROTO_LANGUAGE, ECOLOGY, ACTIVE_PERCEPTION, HYPOTHESIS, LOGOS,
           AUTOREGENERATION, GOVERNANCE, OPS, EVALUATION, COMMUNICATION,
           LLM_ADAPTER_OPTIONAL)


class ModuleStatus:
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ENABLED = "enabled"
    DISABLED = "disabled"

    ALL = (AVAILABLE, UNAVAILABLE, ENABLED, DISABLED)


# name -> (package path, capability, dependencies, optional deps, critical?).
_MODULE_SPECS = {
    "bridge": ("solaris_ai_nn.bridges.neural_bridge",
               ModuleCapability.SIGNAL_PROCESSOR, [], [], False),
    "signals": ("solaris_ai_nn.signals.canonical",
                ModuleCapability.STIMULUS_SOURCE, [], [], False),
    "memory": ("solaris_ai_nn.memory.trace_memory",
               ModuleCapability.MEMORY, [], [], False),
    "world_model": ("solaris_ai_nn.world_model.builder",
                    ModuleCapability.WORLD_MODEL, [], ["bridge"], False),
    "homeostasis": ("solaris_ai_nn.homeostasis.regulation",
                    ModuleCapability.HOMEOSTASIS, [], [], False),
    "executive": ("solaris_ai_nn.executive.coordinator",
                  ModuleCapability.EXECUTIVE, [], ["homeostasis"], False),
    "ego": ("solaris_ai_nn.ego.boundaries",
            ModuleCapability.EGO_BOUNDARY, [], [], False),
    "latent": ("solaris_ai_nn.latent.mysterium",
               ModuleCapability.LATENT, [], [], False),
    "developmental": ("solaris_ai_nn.developmental.developmental_runtime",
                      ModuleCapability.DEVELOPMENTAL, [], [], False),
    "protolanguage": ("solaris_ai_nn.protolanguage.layer",
                      ModuleCapability.PROTO_LANGUAGE, [], ["world_model"],
                      False),
    "ecology": ("solaris_ai_nn.ecology.nursery",
                ModuleCapability.ECOLOGY, [], [], False),
    "active_perception": ("solaris_ai_nn.active_perception.active_sensing",
                          ModuleCapability.ACTIVE_PERCEPTION, [],
                          ["ecology", "world_model"], False),
    "hypothesis": ("solaris_ai_nn.hypothesis",
                   ModuleCapability.HYPOTHESIS, [],
                   ["world_model", "active_perception"], False),
    "logos": ("solaris_ai_nn.logos_complexity",
              ModuleCapability.LOGOS, [],
              ["world_model", "protolanguage", "hypothesis"], False),
    "autoregeneration": ("solaris_ai_nn.autoregeneration",
                         ModuleCapability.AUTOREGENERATION, [], [], False),
    "governance": ("solaris_ai_nn.governance.policy",
                   ModuleCapability.GOVERNANCE, [], [], True),
    "ops": ("solaris_ai_nn.ops.supervisor",
            ModuleCapability.OPS, [], [], False),
    "evaluation": ("solaris_ai_nn.evaluation.metrics",
                   ModuleCapability.EVALUATION, [], [], False),
    "communication": ("solaris_ai_nn.communication.query_router",
                      ModuleCapability.COMMUNICATION, [], [], False),
    "inner_map": ("solaris_ai_nn.inner_map.observer",
                  ModuleCapability.EGO_BOUNDARY, [], [], False),
    "llm_adapter": ("solaris_ai_nn.llm_adapter.mock_client",
                    ModuleCapability.LLM_ADAPTER_OPTIONAL, [], [], False),
}


@dataclass
class ModuleDescriptor:
    """One module's identity, availability, and wiring."""

    name: str
    package_path: str
    capability: str
    enabled: bool = False
    available: bool = False
    initialized: bool = False
    safe_to_run: bool = True
    governance_required: bool = False
    critical: bool = False
    last_error: str = ""
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)
    last_snapshot: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ConscienceModuleRegistry:
    """Detects, registers, and validates the runtime's modules."""

    modules: Dict[str, ModuleDescriptor] = field(default_factory=dict)

    def detect(self, enabled_modules: Optional[List[str]] = None,
               ) -> "ConscienceModuleRegistry":
        """Probe each known module for import availability and register it."""
        enabled = set(enabled_modules or [])
        for name, (path, cap, deps, opt, critical) in _MODULE_SPECS.items():
            available = self._probe(path)
            self.modules[name] = ModuleDescriptor(
                name=name, package_path=path, capability=cap,
                enabled=(name in enabled), available=available,
                dependencies=list(deps), optional_dependencies=list(opt),
                critical=critical,
                governance_required=(name == "governance"
                                     or "month" in name),
                last_error="" if available else "import failed")
        return self

    @staticmethod
    def _probe(path: str) -> bool:
        try:
            importlib.import_module(path)
            return True
        except Exception:
            return False

    def register(self, name: str, descriptor: ModuleDescriptor) -> None:
        self.modules[name] = descriptor

    def get(self, name: str) -> Optional[ModuleDescriptor]:
        return self.modules.get(name)

    def enabled(self) -> List[str]:
        return sorted(n for n, d in self.modules.items() if d.enabled)

    def available(self) -> List[str]:
        return sorted(n for n, d in self.modules.items() if d.available)

    def missing(self) -> List[str]:
        """Enabled-but-unavailable modules."""
        return sorted(n for n, d in self.modules.items()
                      if d.enabled and not d.available)

    def validate_dependencies(self) -> Dict[str, List[str]]:
        """Return enabled modules -> their unmet (hard) dependencies."""
        unmet: Dict[str, List[str]] = {}
        for name, d in self.modules.items():
            if not d.enabled:
                continue
            missing = [dep for dep in d.dependencies
                       if not (self.modules.get(dep)
                               and self.modules[dep].available)]
            if missing:
                unmet[name] = missing
        return unmet

    def topology(self) -> Dict[str, Any]:
        return {
            "nodes": [{"name": n, "capability": d.capability,
                       "enabled": d.enabled, "available": d.available}
                      for n, d in sorted(self.modules.items())],
            "edges": [{"from": n, "to": dep, "kind": "depends_on"}
                      for n, d in self.modules.items()
                      for dep in d.dependencies]
            + [{"from": n, "to": dep, "kind": "optional"}
               for n, d in self.modules.items()
               for dep in d.optional_dependencies],
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "module_count": len(self.modules),
            "enabled": self.enabled(),
            "available": self.available(),
            "missing": self.missing(),
            "unmet_dependencies": self.validate_dependencies(),
        }
