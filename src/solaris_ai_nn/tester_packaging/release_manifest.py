"""Tester release manifest -- a local, deterministic readiness manifest (no Git).

:class:`ReleaseManifestBuilder` lists the package metadata, required package files/docs/
examples/CLI commands, tester fixture/live/console/feedback artifacts, known optional
modules, and a local readiness assessment. It never calls Git (the commit hash is
``unknown`` unless trivially readable from a local ``.git/HEAD`` file) and it does not
publish a release.
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ReleaseReadinessStatus:
    READY = "ready"
    READY_WITH_WARNINGS = "ready_with_warnings"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"

    ALL = (READY, READY_WITH_WARNINGS, BLOCKED, UNKNOWN)


@dataclass
class ReleaseArtifact:
    """One artifact the tester release expects to be present."""

    name: str
    kind: str  # package_file | docs | example | cli_command | module
    required: bool
    present: bool
    detail: str = ""

    @property
    def blocking(self) -> bool:
        return self.required and not self.present

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "kind": self.kind, "required": self.required,
                "present": self.present, "detail": self.detail,
                "blocking": self.blocking}


@dataclass
class TesterReleaseManifest:
    """The local tester release artifact manifest."""

    package_name: str = "solaris-ai-nn"
    version: str = "unknown"
    commit: str = "unknown"
    python_requirement: str = ">=3.11"
    artifacts: List[ReleaseArtifact] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    generated_utc: str = ""

    @property
    def readiness(self) -> str:
        if any(a.blocking for a in self.artifacts) or self.blockers:
            return ReleaseReadinessStatus.BLOCKED
        if self.warnings or any(not a.present and not a.required
                                for a in self.artifacts):
            return ReleaseReadinessStatus.READY_WITH_WARNINGS
        return ReleaseReadinessStatus.READY

    def to_dict(self) -> Dict[str, Any]:
        kinds: Dict[str, int] = {}
        for a in self.artifacts:
            kinds[a.kind] = kinds.get(a.kind, 0) + 1
        return {
            "package_name": self.package_name, "version": self.version,
            "commit": self.commit, "python_requirement": self.python_requirement,
            "generated_utc": self.generated_utc,
            "readiness": self.readiness,
            "artifact_count": len(self.artifacts),
            "by_kind": kinds,
            "missing_required": [a.name for a in self.artifacts if a.blocking],
            "missing_optional": [a.name for a in self.artifacts
                                 if not a.required and not a.present],
            "artifacts": [a.to_dict() for a in self.artifacts],
            "blockers": list(self.blockers), "warnings": list(self.warnings),
            "calls_git": False, "publishes_release": False,
            "note": "local deterministic readiness manifest; it does not call "
                    "Git and does not publish a release",
        }


_PACKAGE_FILES = ("pyproject.toml", "src/solaris_ai_nn/__init__.py",
                  "src/solaris_ai_nn/__main__.py", "src/solaris_ai_nn/cli.py")
_DOCS = ("README.md", "docs/ARCHITECTURE.md", "docs/EXPERIMENTS.md",
         "docs/RESEARCH_NOTES.md")
_EXAMPLES = (
    "examples/tester_fixture_spine/fixture_tester_v0/events.jsonl",
    "examples/tester_live_readonly/LIVE_READONLY_GOVERNANCE.tester.template.json",
    "examples/tester_live_readonly/FEEDER_REGISTRY.tester.template.json",
    "examples/tester_live_readonly/sample_safe_events/live_safe_events.jsonl",
    "tools/external_feeders/README.md")
_REQUIRED_COMMANDS = ("doctor", "tester-demo", "tester-console",
                      "tester-live-init", "tester-feedback-init",
                      "membrane-run", "membrane-integrate")
_MODULES = (("tester_fixture_spine", True), ("environmental_membrane", True),
            ("membrane_integration", True), ("tester_console", True),
            ("tester_feedback", True), ("tester_live_readonly", True),
            ("live_birth", False), ("live_observation", False))


@dataclass
class ReleaseManifestBuilder:
    """Builds the local tester release manifest (deterministic; no Git calls)."""

    def build(self) -> TesterReleaseManifest:
        manifest = TesterReleaseManifest(
            generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        manifest.version = self._version()
        manifest.commit = self._commit_without_git()
        manifest.python_requirement = ">=3.11"

        for path in _PACKAGE_FILES:
            manifest.artifacts.append(ReleaseArtifact(
                path, "package_file", True, os.path.isfile(path)))
        for path in _DOCS:
            manifest.artifacts.append(ReleaseArtifact(
                path, "docs", True, os.path.isfile(path)))
        for path in _EXAMPLES:
            manifest.artifacts.append(ReleaseArtifact(
                path, "example", True, os.path.isfile(path)))

        from .command_registry_check import CommandRegistryCheck
        registered = CommandRegistryCheck()._registered_commands()
        for cmd in _REQUIRED_COMMANDS:
            manifest.artifacts.append(ReleaseArtifact(
                cmd, "cli_command", True, cmd in registered))
        for module, required in _MODULES:
            manifest.artifacts.append(ReleaseArtifact(
                module, "module", required, self._importable(module)))

        manifest.blockers = [a.name for a in manifest.artifacts if a.blocking]
        manifest.warnings = [a.name for a in manifest.artifacts
                             if not a.required and not a.present]
        return manifest

    def write(self, manifests_dir: str) -> str:
        import json
        os.makedirs(manifests_dir, exist_ok=True)
        path = os.path.join(manifests_dir,
                            "TESTER_RELEASE_ARTIFACT_MANIFEST.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.build().to_dict(), fh, indent=2, default=str)
        return path

    @staticmethod
    def _version() -> str:
        try:
            import tomllib  # py311+
            with open("pyproject.toml", "rb") as fh:
                data = tomllib.load(fh)
            return str(data.get("project", {}).get("version", "unknown"))
        except Exception:
            try:
                from importlib.metadata import version
                return version("solaris-ai-nn")
            except Exception:
                return "unknown"

    @staticmethod
    def _commit_without_git() -> str:
        """Read the commit from .git/HEAD without invoking Git (read-only)."""
        head = os.path.join(".git", "HEAD")
        try:
            if not os.path.isfile(head):
                return "unknown"
            with open(head, encoding="utf-8") as fh:
                ref = fh.read().strip()
            if ref.startswith("ref:"):
                ref_path = os.path.join(".git", ref.split(" ", 1)[1].strip())
                if os.path.isfile(ref_path):
                    with open(ref_path, encoding="utf-8") as fh:
                        return fh.read().strip()[:40] or "unknown"
                return "unknown"
            return ref[:40] or "unknown"
        except Exception:
            return "unknown"

    @staticmethod
    def _importable(module: str) -> bool:
        import importlib
        try:
            importlib.import_module(f"solaris_ai_nn.{module}")
            return True
        except Exception:
            return False
