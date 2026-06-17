"""Golden run manifest -- the expected artifact structure of a known-good run.

The golden manifest records which artifacts a known-good fixture run should produce,
which are required vs optional, and the semantic expectations (structure + safety
invariants) -- never fragile timestamps or run ids. Missing optional modules are
expected only when declared optional; missing required artifacts fail reproducibility.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .expected_outputs import ExpectedOutputSpec, default_expected_outputs


class GoldenArtifactStatus:
    PRESENT = "present"
    MISSING_REQUIRED = "missing_required"
    SKIPPED_OPTIONAL = "skipped_optional"
    OPTIONAL_MISSING = "optional_missing"
    UNKNOWN = "unknown"

    ALL = (PRESENT, MISSING_REQUIRED, SKIPPED_OPTIONAL, OPTIONAL_MISSING,
           UNKNOWN)


# The canonical golden artifact types and whether they are required.
_GOLDEN_ARTIFACT_TYPES = (
    ("fixture_input", True),
    ("validation_report", True),
    ("quarantine_report", True),
    ("membrane_impression_index", True),
    ("membrane_report", True),
    ("observation_report", True),
    ("source_health_report", True),
    ("source_diet_report", True),
    ("ontogenesis_candidate_summary", False),
    ("semiogenesis_sign_summary", False),
    ("cognition_trace_summary", False),
    ("claim_safety_summary", True),
    ("tester_report", True),
    ("artifact_bundle_manifest", True),
    ("missing_optional_module_marker", False),
    ("skipped_optional_stage_marker", False),
)


@dataclass
class GoldenExpectation:
    """One semantic expectation (structure or safety), not a fragile value."""

    key: str
    expected: Any
    kind: str = "structural"  # structural | safety | range
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"key": self.key, "expected": self.expected, "kind": self.kind,
                "detail": self.detail}


@dataclass
class GoldenArtifact:
    """One expected golden artifact and its observed status."""

    artifact_type: str
    required: bool = True
    present: bool = False
    status: str = GoldenArtifactStatus.UNKNOWN
    detail: str = ""

    def resolve_status(self) -> str:
        if self.present:
            self.status = GoldenArtifactStatus.PRESENT
        elif self.required:
            self.status = GoldenArtifactStatus.MISSING_REQUIRED
        else:
            self.status = GoldenArtifactStatus.OPTIONAL_MISSING
        return self.status

    def to_dict(self) -> Dict[str, Any]:
        return {"artifact_type": self.artifact_type, "required": self.required,
                "present": self.present, "status": self.status,
                "detail": self.detail}


@dataclass
class GoldenRunManifest:
    """The expected artifact structure + expectations for a known-good run."""

    profile_id: str = "fixture_tester_v0"
    fixture_hash: str = ""
    artifacts: List[GoldenArtifact] = field(default_factory=list)
    expectations: List[GoldenExpectation] = field(default_factory=list)
    optional_skipped: List[str] = field(default_factory=list)
    expected_spec: ExpectedOutputSpec = field(
        default_factory=default_expected_outputs)

    @property
    def required_artifacts(self) -> List[GoldenArtifact]:
        return [a for a in self.artifacts if a.required]

    @property
    def missing_required(self) -> List[GoldenArtifact]:
        return [a for a in self.artifacts
                if a.required and not a.present]

    def artifact(self, artifact_type: str) -> Optional[GoldenArtifact]:
        for a in self.artifacts:
            if a.artifact_type == artifact_type:
                return a
        return None

    def to_dict(self) -> Dict[str, Any]:
        for a in self.artifacts:
            a.resolve_status()
        return {
            "golden_manifest_version": "tester_fixture_spine_v0",
            "profile_id": self.profile_id,
            "fixture_hash": self.fixture_hash,
            "artifact_count": len(self.artifacts),
            "required_artifact_count": len(self.required_artifacts),
            "missing_required_artifact_count": len(self.missing_required),
            "artifacts": [a.to_dict() for a in self.artifacts],
            "expectations": [e.to_dict() for e in self.expectations],
            "optional_skipped": list(self.optional_skipped),
            "expected_outputs": self.expected_spec.to_dict(),
            "ignores_timestamps_and_run_ids": True,
            "note": "the golden manifest records expected artifact structure and "
                    "safety invariants; it tolerates changing run ids and "
                    "timestamps and checks semantics, not fragile values",
        }

    def to_markdown(self) -> str:
        d = self.to_dict()
        lines = ["# Golden Run Manifest", "",
                 f"- profile: {d['profile_id']}",
                 f"- fixture hash: {d['fixture_hash']}",
                 f"- artifacts: {d['artifact_count']} "
                 f"(required {d['required_artifact_count']}, missing required "
                 f"{d['missing_required_artifact_count']})", "",
                 "| artifact | required | status |",
                 "| --- | --- | --- |"]
        for a in d["artifacts"]:
            lines.append(f"| {a['artifact_type']} | {a['required']} | "
                         f"{a['status']} |")
        lines += ["", "_The golden manifest checks semantic structure and safety "
                  "invariants, tolerating changing run ids and timestamps. "
                  "Missing required artifacts fail reproducibility; missing "
                  "optional modules are expected only when declared optional._"]
        return "\n".join(lines)

    def write(self, state_dir: str) -> Dict[str, str]:
        base = os.path.join(state_dir, "golden")
        os.makedirs(base, exist_ok=True)
        json_path = os.path.join(base, "GOLDEN_RUN_MANIFEST.json")
        md_path = os.path.join(base, "GOLDEN_RUN_MANIFEST.md")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, default=str)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(self.to_markdown())
        return {"json": json_path, "markdown": md_path}

    @classmethod
    def load(cls, state_dir: str) -> Optional["GoldenRunManifest"]:
        path = os.path.join(state_dir, "golden", "GOLDEN_RUN_MANIFEST.json")
        if not os.path.isfile(path):
            return None
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            return None
        m = cls(profile_id=data.get("profile_id", "fixture_tester_v0"),
                fixture_hash=data.get("fixture_hash", ""),
                optional_skipped=list(data.get("optional_skipped", [])))
        for a in data.get("artifacts", []):
            art = GoldenArtifact(
                artifact_type=a.get("artifact_type", ""),
                required=bool(a.get("required", True)),
                present=bool(a.get("present", False)),
                status=a.get("status", GoldenArtifactStatus.UNKNOWN),
                detail=a.get("detail", ""))
            m.artifacts.append(art)
        for e in data.get("expectations", []):
            m.expectations.append(GoldenExpectation(
                key=e.get("key", ""), expected=e.get("expected"),
                kind=e.get("kind", "structural"), detail=e.get("detail", "")))
        return m


@dataclass
class GoldenManifestBuilder:
    """Builds a golden manifest from the observed artifacts of a tester run."""

    def build(self, *, profile_id: str, fixture_hash: str,
              present_artifacts: Dict[str, bool],
              optional_skipped: Optional[List[str]] = None,
              expectations: Optional[List[GoldenExpectation]] = None,
              ) -> GoldenRunManifest:
        manifest = GoldenRunManifest(
            profile_id=profile_id, fixture_hash=fixture_hash,
            optional_skipped=list(optional_skipped or []),
            expectations=list(expectations or []))
        for artifact_type, required in _GOLDEN_ARTIFACT_TYPES:
            present = bool(present_artifacts.get(artifact_type, False))
            art = GoldenArtifact(artifact_type=artifact_type, required=required,
                                 present=present)
            art.resolve_status()
            manifest.artifacts.append(art)
        return manifest
