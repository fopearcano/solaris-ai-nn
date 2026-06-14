"""Post-pilot reproducibility packaging -- index + checksums, not a data dump.

The :class:`ReproducibilityPackager` writes a reproducibility package: run
config, scenario profile, seed, module list, governance/safety profiles, a
metrics summary, the artifact index, the missing-artifact list, limitations,
reproduction instructions, and a checksum manifest for the major artifacts. It
indexes large logs rather than copying them, includes no secrets, and clearly
marks simulated vs real time.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Substrings that would mark a file as a secret -- never packaged.
_SECRET_HINTS = ("secret", "token", "password", "credential", "api_key",
                 ".env", "private_key")
# Artifacts small enough to checksum directly (others are indexed by size).
_CHECKSUM_MAX_BYTES = 5 * 1024 * 1024


@dataclass
class ReproducibilityPackage:
    """The assembled reproducibility metadata for a run."""

    run_config: Dict[str, Any] = field(default_factory=dict)
    scenario_profile: Optional[str] = None
    seed: Optional[int] = None
    module_list: List[str] = field(default_factory=list)
    version_metadata: Dict[str, Any] = field(default_factory=dict)
    governance_profile: str = "default"
    safety_profile: str = "default"
    metrics_summary: Dict[str, Any] = field(default_factory=dict)
    artifact_index: Dict[str, Any] = field(default_factory=dict)
    missing_artifacts: List[str] = field(default_factory=list)
    known_limitations: List[str] = field(default_factory=list)
    reproduction_instructions: List[str] = field(default_factory=list)
    checksum_manifest: Dict[str, str] = field(default_factory=dict)
    indexed_only: List[str] = field(default_factory=list)
    is_simulated: bool = False
    time_label: str = "unknown"
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ReproducibilityPackager:
    """Builds and persists a reproducibility package from loaded artifacts."""

    base_dir: str = ".solaris_ai_nn_pilot1"

    def build(self, artifacts: Any, *, config: Optional[Dict[str, Any]] = None,
              metrics_summary: Optional[Dict[str, Any]] = None,
              version_metadata: Optional[Dict[str, Any]] = None,
              ) -> ReproducibilityPackage:
        index = getattr(artifacts, "index", None)
        idx_dict = index.to_dict() if index is not None else {}
        data = getattr(artifacts, "data", {}) or {}
        report = data.get("pilot_report") or {}
        cfg = config or (report.get("sections", {}) or {}).get("config") or {}
        is_sim = bool(cfg.get("is_simulated"))
        pkg = ReproducibilityPackage(
            run_config=cfg,
            scenario_profile=cfg.get("metadata", {}).get("profile_id")
            if isinstance(cfg.get("metadata"), dict) else None,
            seed=cfg.get("seed"),
            module_list=cfg.get("enabled_modules", []) if isinstance(
                cfg.get("enabled_modules"), list) else [],
            version_metadata=version_metadata or {},
            governance_profile=cfg.get("governance_profile", "default"),
            safety_profile=cfg.get("safety_profile", "default"),
            metrics_summary=metrics_summary or {},
            artifact_index=idx_dict,
            missing_artifacts=list(idx_dict.get("missing", [])),
            known_limitations=[
                "Reproducibility depends on the seed and module versions; "
                "exact replay is best-effort.",
                "Large logs are indexed by checksum, not copied.",
            ],
            reproduction_instructions=[
                "1. Restore the run config and seed below.",
                "2. Enable the listed modules at the recorded versions.",
                "3. Re-run the matching scenario profile via the conscience "
                "CLI.",
                "4. Compare new artifacts against the checksum manifest.",
            ],
            is_simulated=is_sim,
            time_label=cfg.get("time_label",
                               "SIMULATED-TIME" if is_sim else "unknown"))
        self._checksums(artifacts, pkg)
        return pkg

    def _checksums(self, artifacts: Any, pkg: ReproducibilityPackage) -> None:
        index = getattr(artifacts, "index", None)
        paths = getattr(index, "paths", {}) if index is not None else {}
        for name, path in paths.items():
            base = os.path.basename(path).lower()
            if any(h in base for h in _SECRET_HINTS):
                continue  # never package secrets
            try:
                if os.path.isdir(path):
                    pkg.indexed_only.append(name)
                    continue
                size = os.path.getsize(path)
                if size > _CHECKSUM_MAX_BYTES:
                    pkg.indexed_only.append(name)
                    pkg.checksum_manifest[name] = f"indexed:size={size}"
                    continue
                pkg.checksum_manifest[name] = self._sha256(path)
            except OSError:
                continue

    @staticmethod
    def _sha256(path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return "sha256:" + h.hexdigest()

    def write(self, pkg: ReproducibilityPackage,
              out_dir: Optional[str] = None) -> Dict[str, str]:
        directory = out_dir or os.path.join(self.base_dir,
                                            "reproducibility_package")
        os.makedirs(directory, exist_ok=True)
        manifest_path = os.path.join(directory, "reproducibility.json")
        checksum_path = os.path.join(directory, "checksum_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(pkg.to_dict(), fh, indent=2, default=str)
        with open(checksum_path, "w", encoding="utf-8") as fh:
            json.dump(pkg.checksum_manifest, fh, indent=2, default=str)
        return {"manifest": manifest_path, "checksums": checksum_path,
                "directory": directory}

    def build_and_write(self, artifacts: Any, **kwargs: Any,
                        ) -> "tuple[ReproducibilityPackage, Dict[str, str]]":
        pkg = self.build(artifacts, **kwargs)
        return pkg, self.write(pkg)
