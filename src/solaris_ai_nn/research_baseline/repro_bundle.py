"""Reproducibility bundle -- a local index of how to reproduce a baseline.

:class:`ReproBundleBuilder` writes a reproducibility-bundle manifest + README
that *reference* (not run) everything needed to reproduce a research baseline: the
version record, Python/dependency requirements, expected state directories,
fixtures, optional live feeder manifests, and the required commands. The bundle is
local documentation/index only -- it installs nothing, runs nothing, and fetches
nothing, and it distinguishes fixture / replay / live read-only / operator-provided
evidence.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class EvidenceProvenance:
    FIXTURE = "fixture"
    REPLAY = "replay"
    LIVE_READ_ONLY = "live_read_only"
    OPERATOR_PROVIDED = "operator_provided"
    UNKNOWN = "unknown"

    ALL = (FIXTURE, REPLAY, LIVE_READ_ONLY, OPERATOR_PROVIDED, UNKNOWN)


@dataclass
class ReproBundleIntegrityResult:
    """The integrity check of an indexed bundle (no remote verification)."""

    ok: bool
    missing_artifacts: List[str] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "missing_artifacts": list(self.missing_artifacts),
                "detail": self.detail}


@dataclass
class ReproducibilityBundle:
    """A local index of the inputs + commands to reproduce a baseline."""

    baseline_version_id: str = ""
    python_requirement: str = ">=3.9"
    dependencies: List[str] = field(default_factory=list)
    expected_state_dirs: List[str] = field(default_factory=list)
    required_fixtures: List[str] = field(default_factory=list)
    optional_live_feeder_manifests: List[str] = field(default_factory=list)
    required_commands: List[str] = field(default_factory=list)
    example_commands: List[str] = field(default_factory=list)
    test_commands: List[str] = field(default_factory=list)
    known_missing_artifacts: List[str] = field(default_factory=list)
    known_warnings: List[str] = field(default_factory=list)
    checksum_manifest: Dict[str, str] = field(default_factory=dict)
    evidence_provenance: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_version_id": self.baseline_version_id,
            "python_requirement": self.python_requirement,
            "dependencies": list(self.dependencies),
            "expected_state_dirs": list(self.expected_state_dirs),
            "required_fixtures": list(self.required_fixtures),
            "optional_live_feeder_manifests":
                list(self.optional_live_feeder_manifests),
            "required_commands": list(self.required_commands),
            "example_commands": list(self.example_commands),
            "test_commands": list(self.test_commands),
            "known_missing_artifacts": list(self.known_missing_artifacts),
            "known_warnings": list(self.known_warnings),
            "checksum_manifest": dict(self.checksum_manifest),
            "evidence_provenance": dict(self.evidence_provenance),
            "installs_dependencies": False, "runs_commands": False,
            "fetches_remote": False,
            "note": "local documentation/index only; it installs nothing, runs "
                    "nothing, and fetches nothing",
        }

    def integrity(self) -> ReproBundleIntegrityResult:
        missing = list(self.known_missing_artifacts)
        return ReproBundleIntegrityResult(
            ok=not missing, missing_artifacts=missing,
            detail="bundle indexes local artifacts; missing artifacts are "
                   "listed, not fetched")

    def render_readme(self) -> str:
        lines = [f"# Reproducibility Bundle -- {self.baseline_version_id}", "",
                 "_A local index of how to reproduce this research baseline. It "
                 "installs nothing, runs nothing, and fetches no remote "
                 "resource. This is not a product release._", "",
                 f"- Python requirement: `{self.python_requirement}`",
                 f"- dependencies: {len(self.dependencies)} declared",
                 "", "## Required commands (run manually)", ""]
        lines += [f"- `{c}`" for c in self.required_commands]
        lines += ["", "## Example commands", ""]
        lines += [f"- `{c}`" for c in self.example_commands]
        lines += ["", "## Test commands", ""]
        lines += [f"- `{c}`" for c in self.test_commands]
        lines += ["", "## Evidence provenance", ""]
        lines += [f"- {k}: {v}" for k, v in self.evidence_provenance.items()]
        if self.known_missing_artifacts:
            lines += ["", "## Known missing artifacts", ""]
            lines += [f"- {m}" for m in self.known_missing_artifacts]
        return "\n".join(lines)


@dataclass
class ReproBundleBuilder:
    """Builds the reproducibility-bundle manifest + README (index only)."""

    repo: str = "fopearcano/solaris-ai-nn"

    def build(self, *, baseline_version_id: str,
              snapshot: Optional[Dict[str, Any]] = None,
              known_warnings: Optional[List[str]] = None,
              state_dir: str = ".solaris_ai_nn_research_baseline",
              ) -> ReproducibilityBundle:
        snapshot = snapshot or {}
        missing = list(snapshot.get("missing", []))
        deps = self._read_dependencies()
        provenance = {
            "fixture_demos": EvidenceProvenance.FIXTURE,
            "replay_runs": EvidenceProvenance.REPLAY,
            "live_field_runs": EvidenceProvenance.LIVE_READ_ONLY,
            "operator_validation": EvidenceProvenance.OPERATOR_PROVIDED,
        }
        # Carry through checksums for indexed artifacts where available.
        checksums = {t: a.get("checksum")
                     for t, a in snapshot.get("artifacts", {}).items()
                     if a.get("checksum")}
        return ReproducibilityBundle(
            baseline_version_id=baseline_version_id,
            python_requirement=">=3.9",
            dependencies=deps,
            expected_state_dirs=[state_dir, ".solaris_ai_nn_post_merge",
                                ".solaris_ai_nn_development",
                                ".solaris_ai_nn_soak"],
            required_fixtures=["bounded fixture feeders (no live sources "
                               "required)"],
            optional_live_feeder_manifests=["live feeder manifests are optional "
                                            "and require governance"],
            required_commands=["python -m pytest"],
            example_commands=[
                "python examples/run_research_baseline_demo.py "
                "--state-dir .solaris_ai_nn_research_baseline/test_baseline",
                "python examples/run_repro_bundle_demo.py "
                "--state-dir .solaris_ai_nn_research_baseline/test_repro_bundle"],
            test_commands=["python -m pytest tests/"],
            known_missing_artifacts=missing,
            known_warnings=list(known_warnings or []),
            checksum_manifest=checksums, evidence_provenance=provenance)

    def _read_dependencies(self) -> List[str]:
        # Read declared dependencies from pyproject.toml if present (read-only).
        for root in (os.getcwd(),):
            path = os.path.join(root, "pyproject.toml")
            if os.path.isfile(path):
                try:
                    with open(path, encoding="utf-8") as fh:
                        text = fh.read()
                    return ["see pyproject.toml (stdlib-only project)"] if \
                        "dependencies" not in text else \
                        ["declared in pyproject.toml"]
                except Exception:
                    return []
        return ["stdlib-only (no third-party dependencies indexed)"]

    def write(self, bundle: ReproducibilityBundle, state_dir: str) -> Dict:
        os.makedirs(state_dir, exist_ok=True)
        manifest_path = os.path.join(state_dir, "REPRO_BUNDLE_MANIFEST.json")
        readme_path = os.path.join(state_dir, "REPRO_BUNDLE_README.md")
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(bundle.to_dict(), fh, indent=2, default=str)
        readme = bundle.render_readme()
        try:
            from ..governance.compliance import ClaimGuard

            guard = ClaimGuard()
            if not guard.scan_text(readme).safe:
                readme = guard.rewrite(readme)
        except Exception:
            pass
        with open(readme_path, "w", encoding="utf-8") as fh:
            fh.write(readme)
        return {"manifest": manifest_path, "readme": readme_path}
