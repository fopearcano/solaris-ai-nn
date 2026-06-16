"""Architecture source collector -- read-only structural summary of local sources.

:class:`ArchitectureSourceCollector` collects, read-only, a structural summary of
the local documentation and artifact sources (README, docs/, examples/, the alpha/
claims/baseline/cycle/review/soak/replication/arch-evolution state dirs, and the
source package module names). It executes no code, imports no unsafe runtime
module, treats missing directories as warnings, and summarizes content structurally
rather than copying it blindly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# (label, relative path under repo root, is a state dir)
_DOC_ROOTS = (
    ("readme", "README.md", False),
    ("docs", "docs", False),
    ("examples", "examples", False),
)
_STATE_ROOTS = (
    ("alpha", ".solaris_ai_nn_alpha"),
    ("claims", ".solaris_ai_nn_claims"),
    ("research_baseline", ".solaris_ai_nn_research_baseline"),
    ("research_cycle", ".solaris_ai_nn_research_cycle"),
    ("review", ".solaris_ai_nn_review"),
    ("review_assimilation", ".solaris_ai_nn_review_assimilation"),
    ("soak", ".solaris_ai_nn_soak"),
    ("replication", ".solaris_ai_nn_replication"),
    ("arch_evolution", ".solaris_ai_nn_arch_evolution"),
)

_MAX_FILES_PER_ROOT = 200


@dataclass
class CollectedSource:
    """One collected source location, summarized structurally."""

    label: str
    path: str
    present: bool = True
    file_count: int = 0
    sample_files: List[str] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"label": self.label, "path": self.path, "present": self.present,
                "file_count": self.file_count,
                "sample_files": list(self.sample_files), "detail": self.detail}


@dataclass
class SourceCollectionResult:
    """The aggregate read-only collection result."""

    repo_root: str
    sources: List[CollectedSource] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    package_modules: List[str] = field(default_factory=list)

    def present(self) -> List[CollectedSource]:
        return [s for s in self.sources if s.present]

    def missing(self) -> List[CollectedSource]:
        return [s for s in self.sources if not s.present]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "collected_source_count": len(self.sources),
            "present_source_count": len(self.present()),
            "missing_source_count": len(self.missing()),
            "warning_count": len(self.warnings),
            "package_module_count": len(self.package_modules),
            "sources": [s.to_dict() for s in self.sources],
            "warnings": list(self.warnings),
            "package_modules": list(self.package_modules),
            "note": "read-only structural summary; executes no code; missing "
                    "directories are warnings, not failures",
        }


@dataclass
class ArchitectureSourceCollector:
    """Read-only collector of local documentation/artifact sources."""

    repo_root: Optional[str] = None
    source_roots: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.repo_root:
            self.repo_root = self._guess_repo_root()

    @staticmethod
    def _guess_repo_root() -> str:
        here = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(here, "..", "..", ".."))

    def collect(self) -> SourceCollectionResult:
        result = SourceCollectionResult(repo_root=self.repo_root)
        for label, rel, _ in _DOC_ROOTS:
            self._collect_root(result, label, os.path.join(self.repo_root, rel))
        for label, rel in _STATE_ROOTS:
            self._collect_root(result, f"state:{label}",
                               os.path.join(self.repo_root, rel),
                               warn_if_missing=True)
        for extra in self.source_roots:
            self._collect_root(result, f"extra:{os.path.basename(extra)}",
                               extra, warn_if_missing=True)
        result.package_modules = self._collect_package_modules()
        return result

    def _collect_root(self, result: SourceCollectionResult, label: str,
                      path: str, warn_if_missing: bool = False) -> None:
        if os.path.isfile(path):
            result.sources.append(CollectedSource(
                label=label, path=path, present=True, file_count=1,
                sample_files=[os.path.basename(path)]))
            return
        if not os.path.isdir(path):
            result.sources.append(CollectedSource(
                label=label, path=path, present=False,
                detail="not present locally"))
            if warn_if_missing:
                result.warnings.append(f"{label}: {path} not present")
            return
        files: List[str] = []
        for dirpath, _dirnames, filenames in os.walk(path):
            for fn in filenames:
                files.append(os.path.relpath(os.path.join(dirpath, fn), path))
                if len(files) >= _MAX_FILES_PER_ROOT:
                    break
            if len(files) >= _MAX_FILES_PER_ROOT:
                break
        result.sources.append(CollectedSource(
            label=label, path=path, present=True, file_count=len(files),
            sample_files=sorted(files)[:12]))

    def _collect_package_modules(self) -> List[str]:
        pkg = os.path.join(self.repo_root, "src", "solaris_ai_nn")
        if not os.path.isdir(pkg):
            return []
        mods = []
        for name in sorted(os.listdir(pkg)):
            full = os.path.join(pkg, name)
            if os.path.isdir(full) and not name.startswith("__"):
                mods.append(name)
        return mods
