"""Alpha artifact index -- a per-run index of local artifacts and markers.

:class:`AlphaArtifactIndex` indexes the local artifacts an Alpha run produced (and
the missing-artifact / skipped-module markers it did not). It indexes local
artifacts only, never deletes stale artifacts, and tags every record with a run id.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AlphaArtifactKind:
    STATE_MANIFEST = "state_manifest"
    SYSTEM_CHECK = "system_check"
    MODULE_REGISTRY = "module_registry"
    FIXTURE_INPUT = "fixture_input"
    DEMO_STEP_OUTPUT = "demo_step_output"
    ORGANISM_REPORT = "organism_report"
    METABOLISM_REPORT = "metabolism_report"
    CONCEPT_REPORT = "concept_report"
    SIGN_REPORT = "sign_report"
    COGNITION_REPORT = "cognition_report"
    SELF_BOUNDARY_REPORT = "self_boundary_report"
    DESIRE_ACTION_REPORT = "desire_action_report"
    DEVELOPMENTAL_REPORT = "developmental_report"
    CLAIM_REPORT = "claim_report"
    REVIEW_REPORT = "review_report"
    CYCLE_REPORT = "cycle_report"
    ALPHA_REPORT = "alpha_report"
    RUNBOOK = "runbook"
    MISSING_ARTIFACT_MARKER = "missing_artifact_marker"
    SKIPPED_MODULE_MARKER = "skipped_module_marker"
    SAFETY_REPORT = "safety_report"

    ALL = (STATE_MANIFEST, SYSTEM_CHECK, MODULE_REGISTRY, FIXTURE_INPUT,
           DEMO_STEP_OUTPUT, ORGANISM_REPORT, METABOLISM_REPORT, CONCEPT_REPORT,
           SIGN_REPORT, COGNITION_REPORT, SELF_BOUNDARY_REPORT,
           DESIRE_ACTION_REPORT, DEVELOPMENTAL_REPORT, CLAIM_REPORT,
           REVIEW_REPORT, CYCLE_REPORT, ALPHA_REPORT, RUNBOOK,
           MISSING_ARTIFACT_MARKER, SKIPPED_MODULE_MARKER, SAFETY_REPORT)


@dataclass
class AlphaArtifactRecord:
    """One indexed artifact or marker."""

    kind: str
    ref: str = ""
    present: bool = True
    detail: str = ""

    def __post_init__(self) -> None:
        if self.kind not in AlphaArtifactKind.ALL:
            self.kind = AlphaArtifactKind.MISSING_ARTIFACT_MARKER
        if self.kind in (AlphaArtifactKind.MISSING_ARTIFACT_MARKER,
                         AlphaArtifactKind.SKIPPED_MODULE_MARKER):
            self.present = False

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "ref": self.ref, "present": self.present,
                "detail": self.detail}


@dataclass
class AlphaArtifactIndex:
    """Indexes a single Alpha run's artifacts (local; never deletes)."""

    state_root: str = ".solaris_ai_nn_alpha"
    run_id: str = ""
    records: List[AlphaArtifactRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.run_id:
            self.run_id = f"alpha_run_{int(time.time())}"

    @property
    def _index_dir(self) -> str:
        return os.path.join(self.state_root, "index")

    @property
    def json_path(self) -> str:
        return os.path.join(self._index_dir, "ALPHA_ARTIFACT_INDEX.json")

    @property
    def md_path(self) -> str:
        return os.path.join(self._index_dir, "ALPHA_ARTIFACT_INDEX.md")

    def add(self, kind: str, *, ref: str = "", present: bool = True,
            detail: str = "") -> AlphaArtifactRecord:
        rec = AlphaArtifactRecord(kind=kind, ref=ref, present=present,
                                  detail=detail)
        self.records.append(rec)
        return rec

    def add_missing(self, ref: str, detail: str = "") -> AlphaArtifactRecord:
        return self.add(AlphaArtifactKind.MISSING_ARTIFACT_MARKER, ref=ref,
                        present=False, detail=detail or "artifact not produced")

    def add_skipped_module(self, ref: str, detail: str = "",
                           ) -> AlphaArtifactRecord:
        return self.add(AlphaArtifactKind.SKIPPED_MODULE_MARKER, ref=ref,
                        present=False, detail=detail or "module skipped")

    def present(self) -> List[AlphaArtifactRecord]:
        return [r for r in self.records if r.present]

    def missing(self) -> List[AlphaArtifactRecord]:
        return [r for r in self.records if not r.present]

    def index(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "alpha_artifact_count": len(self.records),
            "present_artifact_count": len(self.present()),
            "missing_artifact_count": len(self.missing()),
        }

    def to_dict(self) -> Dict[str, Any]:
        d = self.index()
        d["state_root"] = self.state_root
        d["records"] = [r.to_dict() for r in self.records]
        d["deletes_stale_artifacts"] = False
        d["note"] = ("indexes local artifacts only for this run id; missing "
                     "artifacts and skipped modules are indexed as markers; "
                     "stale artifacts are never deleted")
        return d

    def write(self) -> Dict[str, str]:
        os.makedirs(self._index_dir, exist_ok=True)
        with open(self.json_path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, default=str)
        with open(self.md_path, "w", encoding="utf-8") as fh:
            fh.write(self._render_md())
        return {"json": self.json_path, "md": self.md_path}

    def _render_md(self) -> str:
        idx = self.index()
        lines = ["# Alpha Artifact Index", "",
                 f"- run id: {idx['run_id']}",
                 f"- artifacts: {idx['alpha_artifact_count']} "
                 f"(present {idx['present_artifact_count']}, missing "
                 f"{idx['missing_artifact_count']})", "",
                 "| kind | present | ref | detail |",
                 "| --- | --- | --- | --- |"]
        for r in self.records:
            lines.append(f"| {r.kind} | {r.present} | {r.ref} | {r.detail} |")
        lines += ["", "_Indexes local artifacts only; missing artifacts and "
                  "skipped modules are shown as markers; stale artifacts are "
                  "never deleted._"]
        return "\n".join(lines)
