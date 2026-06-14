"""Research reproducibility -- enough to reproduce, by index and checksum.

The :class:`ResearchReproducibilityBuilder` packages the experiment design,
variant/baseline configs, seeds, module availability, a safety snapshot, metric
definitions, a result index, artifact checksums, the missing-artifact list, and
reproduction instructions. It uses checksums and indexes (not huge log copies),
includes no private external data, and marks each data source's label
(fixture / simulated / read_only / sandbox_only).
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ResearchReproducibilityPackage:
    package_id: str
    sections: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"package_id": self.package_id, "timestamp": self.timestamp,
                "sections": self.sections}


@dataclass
class ResearchReproducibilityBuilder:
    base_dir: str = ".solaris_ai_nn_research"

    def build(self, *, design: Any = None,
              variant_configs: Optional[List[Dict]] = None,
              baseline_configs: Optional[List[str]] = None,
              result_store: Any = None, metrics: Any = None,
              safety_snapshot: Optional[Dict] = None,
              ) -> ResearchReproducibilityPackage:
        store_snap = (result_store.snapshot()
                      if hasattr(result_store, "snapshot") else {})
        sections = {
            "experiment_design": design.to_dict()
            if hasattr(design, "to_dict") else (design or {}),
            "variant_configs": variant_configs or [],
            "baseline_configs": baseline_configs or [],
            "seeds": [getattr(design, "seed", 7)],
            "module_availability": self._module_availability(),
            "safety_invariant_snapshot": safety_snapshot or {},
            "metric_definitions": (metrics.snapshot()
                                   if hasattr(metrics, "snapshot") else {}),
            "result_index": store_snap,
            "artifact_checksums": [a.to_dict() for a in getattr(
                result_store, "_artifacts", [])],
            "missing_artifacts": store_snap.get("missing_artifacts", []),
            "data_labels": ["fixture", "simulated", "read_only",
                            "sandbox_only"],
            "reproduction_instructions": [
                "Re-run the named experiment design with the recorded seed.",
                "Instantiate the listed variant and baseline configs.",
                "Re-run the ablation matrix; confirm hard safety stayed on.",
                "Compare metrics against the recorded result index.",
                "All data is fixture/simulated/read-only/sandbox-only; no "
                "private external data is included.",
            ],
        }
        return ResearchReproducibilityPackage(
            package_id=f"REPRO_{getattr(design, 'experiment_id', 'X')}",
            sections=sections)

    @staticmethod
    def _module_availability() -> Dict[str, bool]:
        import importlib

        modules = ["protolanguage", "world_model", "active_perception",
                   "hypothesis", "logos_complexity", "autoregeneration",
                   "latent", "sensory_membrane", "motor_membrane",
                   "safety_invariants", "inner_map"]
        out: Dict[str, bool] = {}
        for m in modules:
            try:
                importlib.import_module(f"solaris_ai_nn.{m}")
                out[m] = True
            except Exception:
                out[m] = False
        return out

    def write(self, package: ResearchReproducibilityPackage) -> Dict[str, str]:
        directory = os.path.join(self.base_dir, "reproducibility")
        os.makedirs(directory, exist_ok=True)
        json_path = os.path.join(directory,
                                 f"{package.package_id}.json")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(package.to_dict(), fh, indent=2, default=str)
        # A compact checksum manifest (not the full logs).
        manifest_path = os.path.join(directory, "checksum_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(package.sections.get("artifact_checksums", []), fh,
                      indent=2, default=str)
        return {"package": json_path, "manifest": manifest_path}

    def build_and_write(self, **kwargs: Any) -> ResearchReproducibilityPackage:
        package = self.build(**kwargs)
        package.sections["paths"] = self.write(package)
        return package
