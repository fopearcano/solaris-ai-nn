"""Tester RC manifest -- the aggregate local record of the release candidate.

:class:`TesterRCManifestBuilder` aggregates the RC id, profile, package metadata, command
and doc/example lists, the collected artifacts, and the readiness/blocker counts into a
single manifest. The manifest is local only and never implies publication. The commit
hash is read from ``.git/HEAD`` if present (a file read, never a Git call); otherwise it
is ``unknown``.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class TesterRCStatus:
    READY = "ready_for_first_tester"
    READY_WITH_WARNINGS = "ready_with_warnings"
    BLOCKED = "blocked"
    CRITICAL_BLOCKED = "critical_blocked"
    UNKNOWN = "unknown"

    ALL = (READY, READY_WITH_WARNINGS, BLOCKED, CRITICAL_BLOCKED, UNKNOWN)


_REQUIRED_COMMANDS = (
    "doctor", "tester-demo", "tester-console", "tester-live-init",
    "tester-live-doctor", "tester-feedback-init", "tester-packaging",
    "tester-safety-freeze", "tester-rc")
_OPTIONAL_COMMANDS = (
    "tester-live-run", "tester-feedback-bundle", "tester-install-guide",
    "tester-clean-machine", "tester-redteam", "tester-rc-bundle")
_OPTIONAL_MODULES = (
    ("ontogenesis_report", "ontogenesis report"),
    ("semiogenesis_report", "semiogenesis report"),
    ("cognition_report", "cognition report"),
    ("scientific_claims_report", "scientific claims report"),
    ("technical_whitepaper", "technical whitepaper"),
    ("static_html_console", "static HTML console"))


@dataclass
class TesterRCArtifact:
    key: str
    label: str
    tier: str
    present: bool
    path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"key": self.key, "label": self.label, "tier": self.tier,
                "present": self.present, "path": self.path}


@dataclass
class TesterRCManifest:
    """The aggregate local release-candidate manifest."""

    rc_id: str = ""
    rc_profile: str = "tester_rc_v0"
    generated_utc: str = ""
    package_name: str = "solaris-ai-nn"
    package_version: Optional[str] = None
    python_requirement: str = ">=3.9"
    repository_name: Optional[str] = None
    commit_hash: str = "unknown"
    required_commands: List[str] = field(default_factory=list)
    optional_commands: List[str] = field(default_factory=list)
    required_docs: List[str] = field(default_factory=list)
    required_examples: List[str] = field(default_factory=list)
    fixture_artifacts: List[str] = field(default_factory=list)
    live_artifacts: List[str] = field(default_factory=list)
    console_artifacts: List[str] = field(default_factory=list)
    feedback_artifacts: List[str] = field(default_factory=list)
    packaging_artifacts: List[str] = field(default_factory=list)
    safety_freeze_artifacts: List[str] = field(default_factory=list)
    known_optional_modules: List[str] = field(default_factory=list)
    known_missing_optional_modules: List[str] = field(default_factory=list)
    artifacts: List[TesterRCArtifact] = field(default_factory=list)
    readiness: str = TesterRCStatus.UNKNOWN
    blocker_count: int = 0
    warning_count: int = 0
    missing_required_artifact_count: int = 0
    safety_freeze_status: str = "unknown"
    packaging_status: str = "unknown"
    tester_console_status: str = "unknown"
    feedback_readiness_status: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_version": "tester_rc_v0",
            "rc_id": self.rc_id,
            "rc_profile": self.rc_profile,
            "generated_utc": self.generated_utc,
            "package_name": self.package_name,
            "package_version": self.package_version,
            "python_requirement": self.python_requirement,
            "repository_name": self.repository_name,
            "commit_hash": self.commit_hash,
            "required_commands": list(self.required_commands),
            "optional_commands": list(self.optional_commands),
            "required_docs": list(self.required_docs),
            "required_examples": list(self.required_examples),
            "fixture_artifacts": list(self.fixture_artifacts),
            "live_artifacts": list(self.live_artifacts),
            "console_artifacts": list(self.console_artifacts),
            "feedback_artifacts": list(self.feedback_artifacts),
            "packaging_artifacts": list(self.packaging_artifacts),
            "safety_freeze_artifacts": list(self.safety_freeze_artifacts),
            "known_optional_modules": list(self.known_optional_modules),
            "known_missing_optional_modules": list(
                self.known_missing_optional_modules),
            "artifacts": [a.to_dict() for a in self.artifacts],
            "readiness": self.readiness,
            "blocker_count": self.blocker_count,
            "warning_count": self.warning_count,
            "missing_required_artifact_count":
                self.missing_required_artifact_count,
            "safety_freeze_status": self.safety_freeze_status,
            "packaging_status": self.packaging_status,
            "tester_console_status": self.tester_console_status,
            "feedback_readiness_status": self.feedback_readiness_status,
            "local_only": True, "published": False, "uploaded": False,
            "implies_publication": False,
            "note": "local tester release-candidate manifest; it does not imply "
                    "publication and no artifact was uploaded or released",
        }

    def to_markdown(self) -> str:
        d = self.to_dict()
        lines = ["# Tester RC Manifest", "",
                 f"- RC id: `{d['rc_id']}`",
                 f"- profile: {d['rc_profile']}",
                 f"- package: {d['package_name']} "
                 f"{d['package_version'] or '(version unknown)'}",
                 f"- python: {d['python_requirement']}",
                 f"- repository: {d['repository_name'] or 'unknown'}",
                 f"- commit: {d['commit_hash']}",
                 f"- readiness: **{d['readiness']}**",
                 f"- blockers: {d['blocker_count']}; warnings: "
                 f"{d['warning_count']}; missing required artifacts: "
                 f"{d['missing_required_artifact_count']}",
                 f"- packaging: {d['packaging_status']}; safety freeze: "
                 f"{d['safety_freeze_status']}; console: "
                 f"{d['tester_console_status']}; feedback: "
                 f"{d['feedback_readiness_status']}", "",
                 "## Required commands", ""]
        lines += [f"- `{c}`" for c in d["required_commands"]]
        lines += ["", "## Known missing optional modules (warning only)", ""]
        lines += [f"- {m}" for m in d["known_missing_optional_modules"]] \
            or ["- none"]
        lines += ["", "_Local tester release-candidate manifest. It does not "
                  "imply publication; nothing was uploaded or released, and no "
                  "claim of consciousness/life/agency is made._"]
        return "\n".join(lines)


@dataclass
class TesterRCManifestBuilder:
    """Builds the RC manifest from collected evidence."""

    def build(self, *, rc_id: str, profile_id: str,
              collection, readiness, ctx: Dict[str, Any]) -> TesterRCManifest:
        m = TesterRCManifest(
            rc_id=rc_id, rc_profile=profile_id,
            generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            required_commands=list(_REQUIRED_COMMANDS),
            optional_commands=list(_OPTIONAL_COMMANDS))
        self._fill_package_metadata(m)
        m.commit_hash = _read_commit_hash()

        for a in collection.artifacts:
            m.artifacts.append(TesterRCArtifact(
                key=a.key, label=a.label, tier=a.tier, present=a.present,
                path=a.path))

        def keys(prefix_keys: List[str]) -> List[str]:
            return [a.key for a in collection.artifacts
                    if a.key in prefix_keys and a.present]

        m.required_docs = [a.key for a in collection.artifacts
                           if a.tier == "required" and a.key.endswith("doc")
                           or a.key in ("readme", "quickstart",
                                        "install_guide")]
        m.fixture_artifacts = keys(["fixture_demo_report",
                                    "reproducibility_report",
                                    "regression_report", "fixture_instructions"])
        m.live_artifacts = keys(["live_readonly_instructions",
                                "external_feeder_policy", "live_doctor_report"])
        m.console_artifacts = keys(["console_instructions", "console_index"])
        m.feedback_artifacts = keys(["feedback_form", "feedback_report"])
        m.packaging_artifacts = keys(["packaging_report",
                                     "environment_doctor_report",
                                     "command_registry_report",
                                     "clean_machine_report", "install_guide"])
        m.safety_freeze_artifacts = keys(["safety_freeze_report",
                                         "release_blocker_report",
                                         "forbidden_claims_doc",
                                         "allowed_language_doc",
                                         "safety_boundaries_doc"])

        for key, label in _OPTIONAL_MODULES:
            m.known_optional_modules.append(label)
            if not collection.present(key):
                m.known_missing_optional_modules.append(label)

        m.missing_required_artifact_count = len(collection.missing_required)
        rd = readiness.to_dict() if readiness else {}
        m.blocker_count = rd.get("blocker_count", 0)
        m.warning_count = rd.get("warning_count", 0)
        m.readiness = _map_readiness(rd.get("status",
                                            TesterRCStatus.UNKNOWN),
                                     collection)
        m.safety_freeze_status = (ctx.get("safety_freeze", {}) or {}).get(
            "readiness", "unknown")
        m.packaging_status = (ctx.get("packaging", {}) or {}).get(
            "readiness", "unknown")
        m.tester_console_status = "read_only" if (
            ctx.get("console", {}) or {}).get("read_only", True) else "unsafe"
        m.feedback_readiness_status = "non_training" if (
            ctx.get("feedback", {}) or {}).get("non_training", True) else \
            "training_risk"
        return m

    def _fill_package_metadata(self, m: TesterRCManifest) -> None:
        data = _read_pyproject()
        proj = data.get("project", {}) if isinstance(data, dict) else {}
        if proj.get("name"):
            m.package_name = proj["name"]
        if proj.get("version"):
            m.package_version = proj["version"]
        if proj.get("requires-python"):
            m.python_requirement = proj["requires-python"]
        urls = proj.get("urls", {}) if isinstance(proj, dict) else {}
        for url in (urls or {}).values():
            if "github.com/" in str(url):
                m.repository_name = str(url).rstrip("/").split(
                    "github.com/")[-1]
                break

    def write(self, manifest: TesterRCManifest,
              manifests_dir: str) -> Dict[str, str]:
        os.makedirs(manifests_dir, exist_ok=True)
        json_path = os.path.join(manifests_dir, "TESTER_RC_MANIFEST.json")
        md_path = os.path.join(manifests_dir, "TESTER_RC_MANIFEST.md")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(manifest.to_dict(), fh, indent=2, default=str)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(manifest.to_markdown())
        return {"json": json_path, "markdown": md_path}


def _map_readiness(gate_status: str, collection) -> str:
    if gate_status == "critical_blocked":
        return TesterRCStatus.CRITICAL_BLOCKED
    if gate_status == "blocked" or collection.missing_required:
        return TesterRCStatus.BLOCKED
    if gate_status == "ready_with_warnings":
        return TesterRCStatus.READY_WITH_WARNINGS
    if gate_status == "ready":
        return TesterRCStatus.READY
    return TesterRCStatus.UNKNOWN


def _read_pyproject() -> Dict[str, Any]:
    path = "pyproject.toml"
    if not os.path.isfile(path):
        return {}
    try:
        try:
            import tomllib  # py311+
            with open(path, "rb") as fh:
                return tomllib.load(fh)
        except Exception:
            pass
        # Minimal fallback parse for name/version/requires-python.
        proj: Dict[str, Any] = {}
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                s = line.strip()
                for key, dest in (("name", "name"), ("version", "version"),
                                  ("requires-python", "requires-python")):
                    if s.startswith(f"{key} ") and "=" in s:
                        val = s.split("=", 1)[1].strip().strip('"').strip("'")
                        proj.setdefault(dest, val)
        return {"project": proj}
    except Exception:
        return {}


def _read_commit_hash() -> str:
    """Read the commit hash from .git/HEAD as a file read (never a Git call)."""
    head = os.path.join(".git", "HEAD")
    if not os.path.isfile(head):
        return "unknown"
    try:
        with open(head, encoding="utf-8") as fh:
            content = fh.read().strip()
        if content.startswith("ref:"):
            ref = content.split(":", 1)[1].strip()
            ref_path = os.path.join(".git", *ref.split("/"))
            if os.path.isfile(ref_path):
                with open(ref_path, encoding="utf-8") as fh:
                    return fh.read().strip()[:40] or "unknown"
            return "unknown"
        return content[:40] or "unknown"
    except Exception:
        return "unknown"
