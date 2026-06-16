"""Alpha module registry -- which Prompt 41-64 modules are present, honestly.

:class:`AlphaModuleRegistry` records, for every major module from Prompts 41-64,
whether it is available locally. It never crashes on a missing module: missing
optional modules warn, missing required-alpha modules block the specific command
(not the whole CLI), and everything is inspectable. Availability is checked by
import-spec lookup only -- no module is executed here.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


class AlphaModuleStatus:
    AVAILABLE = "available"
    MISSING = "missing"
    OPTIONAL_MISSING = "optional_missing"
    STUB_AVAILABLE = "stub_available"
    BLOCKED = "blocked"
    UNSAFE = "unsafe"
    UNKNOWN = "unknown"

    ALL = (AVAILABLE, MISSING, OPTIONAL_MISSING, STUB_AVAILABLE, BLOCKED,
           UNSAFE, UNKNOWN)


# (key, label, import submodule, required_for_alpha)
_MODULES: Tuple[Tuple[str, str, str, bool], ...] = (
    ("plural_sensorium", "Plural Sensorium", "plural_sensorium", False),
    ("organismic_demo", "Minimal Organism Demo", "organismic_demo", False),
    ("live_field", "Live Field", "live_field", False),
    ("feeder_sdk", "Feeder SDK", "feeder_sdk", False),
    ("sensorium_lab", "Sensorium Differentiation", "sensorium_lab", False),
    ("perceptual_metabolism", "Perceptual Metabolism",
     "perceptual_metabolism", False),
    ("perceptual_ontogenesis", "Ontogenesis", "perceptual_ontogenesis", False),
    ("semiogenesis", "Semiogenesis", "semiogenesis", False),
    ("sensorium_cognition", "Cognition", "sensorium_cognition", False),
    ("self_boundary", "Self-Boundary", "self_boundary", False),
    ("desire_formation", "Desire Formation", "desire_formation", False),
    ("action_reaction", "Action-Reaction", "action_reaction", False),
    ("developmental_life", "Developmental Life", "developmental_life", False),
    ("developmental_soak", "Developmental Soak", "developmental_soak", False),
    ("developmental_replication", "Developmental Replication",
     "developmental_replication", False),
    ("architecture_evolution", "Architecture Evolution",
     "architecture_evolution", False),
    ("experiment_compiler", "Experiment Compiler", "experiment_compiler", False),
    ("implementation_intake", "Implementation Intake",
     "implementation_intake", False),
    ("post_merge_assimilation", "Post-Merge Assimilation",
     "post_merge_assimilation", False),
    ("research_baseline", "Research Baseline", "research_baseline", False),
    ("research_cycle", "Research Cycle", "research_cycle", False),
    ("scientific_claims", "Scientific Claims", "scientific_claims", False),
    ("independent_review", "Independent Review", "independent_review", False),
    ("review_assimilation", "Review Assimilation", "review_assimilation", False),
    ("safety_invariants", "Safety Invariants", "safety_invariants", True),
    ("inner_map", "Inner MAP", "inner_map", True),
    ("operator_console", "Operator Console", "operator_console", False),
    ("evaluation", "Evaluation", "evaluation", True),
)

_PACKAGE_ROOT = "solaris_ai_nn"


@dataclass
class AlphaModuleRecord:
    """One module's presence record (never executed during the check)."""

    key: str
    label: str
    import_path: str
    required_for_alpha: bool = False
    status: str = AlphaModuleStatus.UNKNOWN
    detail: str = ""

    def __post_init__(self) -> None:
        if self.status not in AlphaModuleStatus.ALL:
            self.status = AlphaModuleStatus.UNKNOWN

    @property
    def available(self) -> bool:
        return self.status in (AlphaModuleStatus.AVAILABLE,
                               AlphaModuleStatus.STUB_AVAILABLE)

    @property
    def blocks_alpha(self) -> bool:
        return (self.required_for_alpha
                and self.status in (AlphaModuleStatus.MISSING,
                                    AlphaModuleStatus.BLOCKED,
                                    AlphaModuleStatus.UNSAFE))

    def to_dict(self) -> Dict[str, Any]:
        return {"key": self.key, "label": self.label,
                "import_path": self.import_path,
                "required_for_alpha": self.required_for_alpha,
                "status": self.status, "detail": self.detail,
                "available": self.available, "blocks_alpha": self.blocks_alpha}


@dataclass
class AlphaModuleRegistry:
    """Builds and holds the module presence records (import-spec only)."""

    records: List[AlphaModuleRecord] = field(default_factory=list)

    @classmethod
    def build(cls) -> "AlphaModuleRegistry":
        registry = cls()
        for key, label, sub, required in _MODULES:
            status, detail = cls._probe(sub, required)
            registry.records.append(AlphaModuleRecord(
                key=key, label=label,
                import_path=f"{_PACKAGE_ROOT}.{sub}",
                required_for_alpha=required, status=status, detail=detail))
        return registry

    @staticmethod
    def _probe(submodule: str, required: bool) -> Tuple[str, str]:
        full = f"{_PACKAGE_ROOT}.{submodule}"
        try:
            spec = importlib.util.find_spec(full)
        except Exception as exc:  # a broken module must not crash the registry
            return (AlphaModuleStatus.BLOCKED, f"import error: {exc}")
        if spec is None:
            return ((AlphaModuleStatus.MISSING if required
                     else AlphaModuleStatus.OPTIONAL_MISSING),
                    "module not present")
        return (AlphaModuleStatus.AVAILABLE, "")

    def get(self, key: str) -> Optional[AlphaModuleRecord]:
        for r in self.records:
            if r.key == key:
                return r
        return None

    def is_available(self, key: str) -> bool:
        r = self.get(key)
        return bool(r and r.available)

    def available(self) -> List[AlphaModuleRecord]:
        return [r for r in self.records if r.available]

    def missing(self) -> List[AlphaModuleRecord]:
        return [r for r in self.records
                if r.status == AlphaModuleStatus.MISSING]

    def optional_missing(self) -> List[AlphaModuleRecord]:
        return [r for r in self.records
                if r.status == AlphaModuleStatus.OPTIONAL_MISSING]

    def blocked(self) -> List[AlphaModuleRecord]:
        return [r for r in self.records
                if r.status in (AlphaModuleStatus.BLOCKED,
                                AlphaModuleStatus.UNSAFE)]

    def blocking_alpha(self) -> List[AlphaModuleRecord]:
        return [r for r in self.records if r.blocks_alpha]

    def index(self) -> Dict[str, Any]:
        return {
            "alpha_module_count": len(self.records),
            "alpha_available_module_count": len(self.available()),
            "alpha_missing_module_count": len(self.missing()),
            "alpha_optional_missing_count": len(self.optional_missing()),
            "alpha_blocked_module_count": len(self.blocked()),
            "alpha_blocking_alpha_count": len(self.blocking_alpha()),
        }

    def to_dict(self) -> Dict[str, Any]:
        d = self.index()
        d["modules"] = [r.to_dict() for r in self.records]
        d["note"] = ("module presence is checked by import-spec only; no module "
                     "is executed here; missing optional modules warn and are "
                     "never hidden")
        return d
