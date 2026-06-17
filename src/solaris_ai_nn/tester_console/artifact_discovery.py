"""Console artifact discovery -- bounded, read-only scan of local state roots.

:class:`ConsoleArtifactDiscovery` walks the known local state roots (alpha, live,
tester, docs, claims, review, research) and classifies the artifacts it finds (reports,
bundles, governance, feeder registry, membrane/observation/learning artifacts, claim
reports, …). Discovery is strictly read-only: it never executes artifact contents,
never displays raw private payloads, tolerates missing directories (a warning, not a
crash), and reads only bounded summaries of small JSON files.
"""

from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_MAX_JSON_BYTES = 2_000_000
_MAX_PER_KIND = 200


class ArtifactKind:
    ALPHA_REPORT = "alpha_report"
    ALPHA_MODULE_REGISTRY = "alpha_module_registry"
    ALPHA_ARTIFACT_INDEX = "alpha_artifact_index"
    TESTER_FIXTURE_REPORT = "tester_fixture_report"
    TESTER_FIXTURE_BUNDLE = "tester_fixture_bundle"
    TESTER_REPRODUCIBILITY_REPORT = "tester_reproducibility_report"
    TESTER_REGRESSION_REPORT = "tester_regression_report"
    TESTER_LIVE_REPORT = "tester_live_report"
    TESTER_LIVE_BUNDLE = "tester_live_bundle"
    TESTER_FEEDBACK_REPORT = "tester_feedback_report"
    TESTER_FEEDBACK_LEDGER = "tester_feedback_ledger"
    TESTER_FEEDBACK_RELEASE_BLOCKER = "tester_feedback_release_blocker"
    TESTER_FEEDBACK_BUNDLE = "tester_feedback_bundle"
    TESTER_PACKAGING_REPORT = "tester_packaging_report"
    TESTER_INSTALL_GUIDE = "tester_install_guide"
    TESTER_RELEASE_MANIFEST = "tester_release_manifest"
    TESTER_CLEAN_MACHINE_REPORT = "tester_clean_machine_report"
    LIVE_GOVERNANCE = "live_governance"
    FEEDER_REGISTRY = "feeder_registry"
    LIVE_BIRTH_REPORT = "live_birth_report"
    BIRTH_CERTIFICATE = "birth_certificate"
    QUARANTINE_REPORT = "quarantine_report"
    MEMBRANE_REPORT = "membrane_report"
    MEMBRANE_INTEGRATION_REPORT = "membrane_integration_report"
    SENSORY_IMPRESSION_INDEX = "sensory_impression_index"
    MEMBRANE_ANCESTRY_REPORT = "membrane_ancestry_report"
    OBSERVATION_REPORT = "observation_report"
    SOURCE_HEALTH_REPORT = "source_health_report"
    SOURCE_DIET_REPORT = "source_diet_report"
    ONTOGENESIS_REPORT = "ontogenesis_report"
    CONCEPT_MEMORY = "concept_memory"
    SEMIOGENESIS_REPORT = "semiogenesis_report"
    SIGN_MEMORY = "sign_memory"
    COGNITION_REPORT = "cognition_report"
    COGNITION_MEMORY = "cognition_memory"
    SCIENTIFIC_CLAIM_REPORT = "scientific_claim_report"
    SAFETY_REPORT = "safety_report"
    ARCHITECTURE_DOCS = "architecture_docs"
    MISSING_ARTIFACT_MARKER = "missing_artifact_marker"
    UNKNOWN = "unknown"


# (kind, state_root_key, glob_pattern). The glob is relative to the state root.
_DISCOVERY_SPECS = (
    (ArtifactKind.TESTER_FIXTURE_REPORT, "tester",
     "reports/TESTER_DEMO_REPORT_*.json"),
    (ArtifactKind.TESTER_FIXTURE_REPORT, "tester",
     "reports/TESTER_RUN_SUMMARY_*.json"),
    (ArtifactKind.TESTER_REPRODUCIBILITY_REPORT, "tester",
     "reproducibility/*.json"),
    (ArtifactKind.TESTER_REGRESSION_REPORT, "tester", "regression/*.json"),
    (ArtifactKind.TESTER_FIXTURE_BUNDLE, "tester",
     "bundles/TESTER_BUNDLE_*/BUNDLE_MANIFEST.json"),
    (ArtifactKind.TESTER_LIVE_REPORT, "tester",
     "live/reports/TESTER_LIVE_RUN_SUMMARY_*.json"),
    (ArtifactKind.TESTER_LIVE_BUNDLE, "tester",
     "live/bundles/LIVE_TESTER_BUNDLE_*/BUNDLE_MANIFEST.json"),
    (ArtifactKind.TESTER_FEEDBACK_REPORT, "tester",
     "feedback/reports/TESTER_FEEDBACK_REPORT.json"),
    (ArtifactKind.TESTER_FEEDBACK_LEDGER, "tester",
     "feedback/ledger/TESTER_FEEDBACK_LEDGER.json"),
    (ArtifactKind.TESTER_FEEDBACK_BUNDLE, "tester",
     "feedback/bundles/FEEDBACK_BUNDLE_*/BUNDLE_MANIFEST.json"),
    (ArtifactKind.TESTER_PACKAGING_REPORT, "tester",
     "packaging/reports/PACKAGING_REPORT.json"),
    (ArtifactKind.TESTER_INSTALL_GUIDE, "tester",
     "packaging/install_guides/TESTER_INSTALL_GUIDE.md"),
    (ArtifactKind.TESTER_RELEASE_MANIFEST, "tester",
     "packaging/manifests/TESTER_RELEASE_ARTIFACT_MANIFEST.json"),
    (ArtifactKind.TESTER_CLEAN_MACHINE_REPORT, "tester",
     "packaging/reports/CLEAN_MACHINE_READINESS_REPORT.md"),
    (ArtifactKind.LIVE_GOVERNANCE, "live",
     "governance/LIVE_READONLY_GOVERNANCE.json"),
    (ArtifactKind.FEEDER_REGISTRY, "live", "feeders/FEEDER_REGISTRY.json"),
    (ArtifactKind.LIVE_BIRTH_REPORT, "live", "reports/LIVE_BIRTH_REPORT.json"),
    (ArtifactKind.BIRTH_CERTIFICATE, "live", "certificates/*.json"),
    (ArtifactKind.QUARANTINE_REPORT, "live", "quarantine/*.json"),
    (ArtifactKind.MEMBRANE_REPORT, "live",
     "membrane/reports/ENVIRONMENTAL_MEMBRANE_REPORT.json"),
    (ArtifactKind.SENSORY_IMPRESSION_INDEX, "live",
     "membrane/index/*.json"),
    (ArtifactKind.MEMBRANE_INTEGRATION_REPORT, "live",
     "membrane/integration/MEMBRANE_INTEGRATION_REPORT.json"),
    (ArtifactKind.MEMBRANE_ANCESTRY_REPORT, "live",
     "membrane/integration/MEMBRANE_ANCESTRY_REPORT.json"),
    (ArtifactKind.OBSERVATION_REPORT, "live",
     "observation/reports/LIVE_OBSERVATION_REPORT.json"),
    (ArtifactKind.SOURCE_HEALTH_REPORT, "live",
     "observation/source_health/*.json"),
    (ArtifactKind.SOURCE_DIET_REPORT, "live", "observation/source_diet/*.json"),
    (ArtifactKind.ONTOGENESIS_REPORT, "live",
     "ontogenesis/index/*.json"),
    (ArtifactKind.CONCEPT_MEMORY, "live",
     "ontogenesis/concepts/LIVE_CONCEPT_MEMORY.json"),
    (ArtifactKind.SEMIOGENESIS_REPORT, "live", "semiogenesis/index/*.json"),
    (ArtifactKind.SIGN_MEMORY, "live",
     "semiogenesis/signs/LIVE_SIGN_MEMORY.json"),
    (ArtifactKind.COGNITION_REPORT, "live", "cognition/index/*.json"),
    (ArtifactKind.COGNITION_MEMORY, "live",
     "cognition/traces/LIVE_COGNITION_MEMORY.json"),
    (ArtifactKind.ALPHA_REPORT, "alpha", "reports/*.json"),
    (ArtifactKind.ALPHA_MODULE_REGISTRY, "alpha", "MODULE_REGISTRY.json"),
    (ArtifactKind.ALPHA_ARTIFACT_INDEX, "alpha", "ARTIFACT_INDEX.json"),
    (ArtifactKind.SCIENTIFIC_CLAIM_REPORT, "claims", "**/*.json"),
)


@dataclass
class DiscoveredArtifact:
    """One discovered artifact (path + kind + a bounded summary)."""

    kind: str
    path: str
    state_root: str
    exists: bool = True
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "path": self.path,
                "state_root": self.state_root, "exists": self.exists,
                "summary": dict(self.summary)}


@dataclass
class ArtifactDiscoveryResult:
    """The aggregate discovery result."""

    artifacts: List[DiscoveredArtifact] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    roots_scanned: Dict[str, bool] = field(default_factory=dict)

    def by_kind(self, kind: str) -> List[DiscoveredArtifact]:
        return [a for a in self.artifacts if a.kind == kind]

    def latest(self, kind: str) -> Optional[DiscoveredArtifact]:
        items = self.by_kind(kind)
        if not items:
            return None
        return max(items, key=lambda a: a.summary.get("_mtime", 0.0))

    def has(self, kind: str) -> bool:
        return bool(self.by_kind(kind))

    def to_dict(self) -> Dict[str, Any]:
        kinds: Dict[str, int] = {}
        for a in self.artifacts:
            kinds[a.kind] = kinds.get(a.kind, 0) + 1
        return {
            "artifact_count": len(self.artifacts),
            "by_kind": kinds,
            "roots_scanned": dict(self.roots_scanned),
            "warnings": list(self.warnings),
            "artifacts": [a.to_dict() for a in self.artifacts],
            "note": "discovery is read-only and bounded; raw private payloads "
                    "are not displayed",
        }


@dataclass
class ConsoleArtifactDiscovery:
    """Bounded, read-only artifact discovery across local state roots."""

    state_dir: str = ".solaris_ai_nn_live"
    tester_state_dir: str = ".solaris_ai_nn_tester"
    alpha_state_dir: str = ".solaris_ai_nn_alpha"
    docs_dir: str = ".solaris_ai_nn_docs"
    claims_dir: str = ".solaris_ai_nn_claims"

    def _roots(self) -> Dict[str, str]:
        return {"alpha": self.alpha_state_dir, "live": self.state_dir,
                "tester": self.tester_state_dir, "docs": self.docs_dir,
                "claims": self.claims_dir,
                "review": ".solaris_ai_nn_review",
                "review_assimilation": ".solaris_ai_nn_review_assimilation",
                "research_cycle": ".solaris_ai_nn_research_cycle",
                "research_baseline": ".solaris_ai_nn_research_baseline"}

    def discover(self) -> ArtifactDiscoveryResult:
        result = ArtifactDiscoveryResult()
        roots = self._roots()
        for key, root in roots.items():
            present = os.path.isdir(root)
            result.roots_scanned[key] = present
            if not present:
                result.warnings.append(f"state root not present: {root} ({key})")
        for kind, root_key, pattern in _DISCOVERY_SPECS:
            root = roots.get(root_key, "")
            if not root or not os.path.isdir(root):
                continue
            matches = sorted(glob.glob(os.path.join(root, pattern),
                                       recursive=True))[:_MAX_PER_KIND]
            for path in matches:
                if not os.path.isfile(path):
                    continue
                result.artifacts.append(DiscoveredArtifact(
                    kind=kind, path=path, state_root=root_key, exists=True,
                    summary=self._summarize(path)))
        # Local architecture docs (reference only; never executed).
        for doc in ("README.md", "docs/ARCHITECTURE.md", "docs/EXPERIMENTS.md",
                    "docs/RESEARCH_NOTES.md"):
            if os.path.isfile(doc):
                result.artifacts.append(DiscoveredArtifact(
                    kind=ArtifactKind.ARCHITECTURE_DOCS, path=doc,
                    state_root="repo", summary={"_mtime": _mtime(doc)}))
        return result

    @staticmethod
    def _summarize(path: str) -> Dict[str, Any]:
        """Read a small, bounded summary of a JSON artifact (read-only)."""
        summary: Dict[str, Any] = {"_mtime": _mtime(path),
                                   "_size": _size(path)}
        if not path.endswith(".json"):
            return summary
        try:
            if os.path.getsize(path) > _MAX_JSON_BYTES:
                summary["_truncated"] = True
                return summary
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            return summary
        # Only surface non-sensitive scalar keys; never raw payloads.
        if isinstance(data, dict):
            for key in _SAFE_SUMMARY_KEYS:
                if key in data:
                    summary[key] = _scalar(data[key])
            # Common nested status block.
            sections = data.get("sections")
            if isinstance(sections, dict):
                summary["_has_sections"] = True
        return summary


_SAFE_SUMMARY_KEYS = (
    "tester_run_id", "tester_live_run_id", "reproducibility_status",
    "regression_status", "golden_run_status", "membrane_impression_count",
    "fixture_quarantined_count", "quarantined_count", "quarantine_count",
    "pipeline_status", "critical_bypass_count", "bypass_finding_count",
    "membrane_integration_enabled", "live_birth_blocked", "live_birth_enabled",
    "live_observation_enabled", "live_readonly_enabled", "operator_approved",
    "overall_status", "blocked", "entry_count", "local_only", "uploaded",
    "published", "membrane_present", "source_pressure_status",
    "feeder_count", "accepted_event_count", "quarantined_event_count",
    "entry_count", "release_blocker_count", "stop_testing_count",
    "safety_concern_count", "redaction_count",
    "readiness", "version", "missing_required_artifact_count",
)


def _mtime(path: str) -> float:
    try:
        return os.path.getmtime(path)
    except Exception:
        return 0.0


def _size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except Exception:
        return 0


def _scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return len(value)
    if isinstance(value, dict):
        return f"<{len(value)} keys>"
    return str(value)[:120]
