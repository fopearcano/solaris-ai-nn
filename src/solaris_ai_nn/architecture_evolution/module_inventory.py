"""Module inventory -- a catalogue of every package and its evidence links.

The :class:`ModuleInventory` enumerates the known packages, marks each one's
availability and lifecycle status, and records its dependencies, integrations,
safety/governance relevance, and evidence references. A missing package is marked
*unavailable*, never silently ignored; safety-critical modules are clearly
flagged so no later step can prune them on performance evidence alone.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# The known Solaris-AI-NN packages and their safety/governance relevance.
# (package, safety_critical, governance_relevant).
_KNOWN_PACKAGES = (
    ("reservoir", False, False),
    ("signals", False, False),
    ("memory", False, False),
    ("plasticity", False, True),
    ("inner_map", False, False),
    ("homeostasis", False, False),
    ("executive", False, True),
    ("ego", True, True),
    ("governance", True, True),
    ("ops", True, True),
    ("latent", False, True),
    ("world_model", False, False),
    ("developmental", False, True),
    ("protolanguage", False, False),
    ("active_perception", False, True),
    ("hypothesis", False, True),
    ("autoregeneration", True, True),
    ("logos_complexity", False, False),
    ("conscience", True, True),
    ("evaluation", False, True),
    ("sensory_membrane", True, True),
    ("motor_membrane", True, True),
    ("pilot1", False, True),
    ("pilot2", True, True),
    ("pilot3", True, True),
    ("pilot4_planning", True, True),
    ("post_pilot", False, True),
    ("safety_invariants", True, True),
    ("research_lab", False, True),
    ("architecture_evolution", False, True),
    ("communication", True, True),
    ("bridges", False, False),
)


@dataclass
class ModuleDependencyRecord:
    """One module's declared dependency links."""

    direct: List[str] = field(default_factory=list)
    optional: List[str] = field(default_factory=list)
    inbound_integrations: List[str] = field(default_factory=list)
    outbound_integrations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ModuleInventoryEntry:
    """One module's inventory record."""

    module_name: str
    package_path: str
    available: bool = True
    lifecycle_status: str = "unknown"
    dependencies: ModuleDependencyRecord = field(
        default_factory=ModuleDependencyRecord)
    safety_relevant: bool = False
    governance_relevant: bool = False
    research_evidence_refs: List[str] = field(default_factory=list)
    benchmark_result_refs: List[str] = field(default_factory=list)
    safety_invariant_refs: List[str] = field(default_factory=list)
    known_issues: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def safety_critical(self) -> bool:
        return self.safety_relevant

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__),
                "dependencies": self.dependencies.to_dict(),
                "safety_critical": self.safety_critical}


@dataclass
class ModuleInventory:
    """Holds the catalogue of modules; missing packages are marked unavailable."""

    entries: Dict[str, ModuleInventoryEntry] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.entries:
            self._build_from_known_packages()

    def _build_from_known_packages(self) -> None:
        for name, safety, gov in _KNOWN_PACKAGES:
            available = self._is_available(name)
            self.entries[name] = ModuleInventoryEntry(
                module_name=name, package_path=f"solaris_ai_nn.{name}",
                available=available,
                lifecycle_status="unknown" if available else "unavailable",
                safety_relevant=safety, governance_relevant=gov,
                known_issues=([] if available else ["package not importable"]))

    @staticmethod
    def _is_available(name: str) -> bool:
        try:
            importlib.import_module(f"solaris_ai_nn.{name}")
            return True
        except Exception:
            return False

    def register(self, entry: ModuleInventoryEntry) -> None:
        self.entries[entry.module_name] = entry

    def get(self, name: str) -> Optional[ModuleInventoryEntry]:
        return self.entries.get(name)

    def attach_evidence(self, name: str, *, research: Optional[List[str]] = None,
                        benchmark: Optional[List[str]] = None,
                        safety: Optional[List[str]] = None) -> None:
        entry = self.entries.get(name)
        if entry is None:
            return
        if research:
            entry.research_evidence_refs.extend(research)
        if benchmark:
            entry.benchmark_result_refs.extend(benchmark)
        if safety:
            entry.safety_invariant_refs.extend(safety)

    def available_modules(self) -> List[str]:
        return sorted(n for n, e in self.entries.items() if e.available)

    def unavailable_modules(self) -> List[str]:
        return sorted(n for n, e in self.entries.items() if not e.available)

    def safety_critical_modules(self) -> List[str]:
        return sorted(n for n, e in self.entries.items() if e.safety_critical)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "module_count": len(self.entries),
            "available_count": len(self.available_modules()),
            "unavailable": self.unavailable_modules(),
            "safety_critical": self.safety_critical_modules(),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {"entries": {n: e.to_dict() for n, e in self.entries.items()}}
