"""Export bundle -- a local, self-describing review package. Never uploaded.

:class:`ExportBundleBuilder` gathers the relevant local reports for a review
theme (safety / research / architecture / pilot / full), copies them into a
bundle directory, and writes an artifact index, checksums, a README, a
limitations note, a missing-artifact list, a no-secrets notice, and a safety
status summary. It never calls the network, never uploads, and does not copy
huge logs by default.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .console_config import OperatorConsoleConfig
from .report_index import ReportIndexer

# Bundle type -> the report types it should include.
BUNDLE_TYPES = {
    "safety_review_bundle": ("safety_invariant_report", "assurance_case"),
    "research_review_bundle": ("research_report",),
    "architecture_review_bundle": ("architecture_review", "roadmap", "adr"),
    "pilot_review_bundle": ("pilot1_report", "pilot2_report", "pilot3_report",
                            "pilot4_readiness_dossier", "post_pilot_analysis"),
    "full_project_evidence_bundle": None,  # everything
}

# Files larger than this are not copied into a bundle by default (huge logs).
_MAX_COPY_BYTES = 2_000_000

_NO_SECRETS_NOTICE = (
    "This bundle is a LOCAL EXPORT ONLY. It is not uploaded anywhere and makes "
    "no network calls. It contains no secrets, credentials, or private source "
    "code; if you believe a copied artifact contains sensitive data, remove it "
    "before sharing."
)

_LIMITATIONS = (
    "Reports are operational evidence, not proof of consciousness, sentience, "
    "life, personhood, or free will.",
    "Missing artifacts are listed, not silently omitted.",
    "Large log files are not copied by default; see the artifact index for "
    "their location.",
)


@dataclass
class ExportBundle:
    bundle_id: str
    bundle_type: str
    bundle_dir: str
    included_files: List[str] = field(default_factory=list)
    missing_report_types: List[str] = field(default_factory=list)
    checksums: Dict[str, str] = field(default_factory=dict)
    safety_status_summary: Dict[str, Any] = field(default_factory=dict)
    uploaded: bool = False
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "bundle_type": self.bundle_type,
            "bundle_dir": self.bundle_dir,
            "included_files": list(self.included_files),
            "missing_report_types": list(self.missing_report_types),
            "checksums": dict(self.checksums),
            "safety_status_summary": dict(self.safety_status_summary),
            "uploaded": False,
            "local_export_only": True,
            "timestamp": self.timestamp,
        }


@dataclass
class ExportBundleBuilder:
    """Builds local export bundles; never uploads, never calls the network."""

    config: OperatorConsoleConfig = field(default_factory=OperatorConsoleConfig)
    safety_status: Optional[Dict[str, Any]] = None

    def build(self, bundle_type: str) -> ExportBundle:
        if bundle_type not in BUNDLE_TYPES:
            raise ValueError(f"unknown bundle type {bundle_type!r}")
        bundle_id = f"BND_{uuid.uuid4().hex[:10]}"
        bundle_dir = os.path.join(self.config.export_dir or
                                  os.path.join(self.config.state_dir, "exports"),
                                  bundle_id)
        os.makedirs(bundle_dir, exist_ok=True)

        wanted = BUNDLE_TYPES[bundle_type]
        from .artifact_index import DEFAULT_DIRECTORIES

        search_dirs = [self.config.state_dir] + [
            d for d in DEFAULT_DIRECTORIES if os.path.isdir(d)]
        export_root = os.path.abspath(self.config.export_dir or "")
        report_index = ReportIndexer(search_dirs).index()
        included: List[str] = []
        checksums: Dict[str, str] = {}
        present_types = set()
        for record in report_index.records:
            if wanted is not None and record.report_type not in wanted:
                continue
            if record.corrupted or not os.path.isfile(record.path):
                continue
            # Never recurse into prior export bundles.
            if export_root and os.path.abspath(record.path).startswith(
                    export_root + os.sep):
                continue
            try:
                if os.path.getsize(record.path) > _MAX_COPY_BYTES:
                    continue  # do not copy huge logs by default
            except OSError:
                continue
            dest_name = f"{record.report_type}__{os.path.basename(record.path)}"
            dest = os.path.join(bundle_dir, dest_name)
            shutil.copy2(record.path, dest)
            included.append(dest_name)
            checksums[dest_name] = self._checksum(dest)
            present_types.add(record.report_type)

        missing = ([t for t in (wanted or ()) if t not in present_types]
                   if wanted is not None else [])

        bundle = ExportBundle(
            bundle_id=bundle_id, bundle_type=bundle_type, bundle_dir=bundle_dir,
            included_files=included, missing_report_types=missing,
            checksums=checksums,
            safety_status_summary=self._safety_summary())
        self._write_index(bundle, report_index)
        self._write_readme(bundle)
        self._write_checksums(bundle)
        return bundle

    def _safety_summary(self) -> Dict[str, Any]:
        s = self.safety_status or {}
        return {
            "status": s.get("status", "unknown"),
            "unresolved_blocker_count": s.get("unresolved_blocker_count", 0),
            "note": "safety status is informational; the bundle changes nothing",
        }

    @staticmethod
    def _checksum(path: str) -> str:
        digest = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65_536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _write_index(self, bundle: ExportBundle,
                     report_index: Any) -> None:
        path = os.path.join(bundle.bundle_dir, "ARTIFACT_INDEX.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"bundle": bundle.to_dict(),
                       "report_index": report_index.to_dict()},
                      fh, indent=2, default=str)

    def _write_checksums(self, bundle: ExportBundle) -> None:
        path = os.path.join(bundle.bundle_dir, "CHECKSUMS.txt")
        with open(path, "w", encoding="utf-8") as fh:
            for name, digest in sorted(bundle.checksums.items()):
                fh.write(f"{digest}  {name}\n")

    def _write_readme(self, bundle: ExportBundle) -> None:
        lines = [
            f"# Export bundle {bundle.bundle_id} ({bundle.bundle_type})", "",
            "## Local export only", "", _NO_SECRETS_NOTICE, "",
            "## Included files", "",
        ]
        lines += [f"- {name}" for name in bundle.included_files] or ["- (none)"]
        lines += ["", "## Missing report types", ""]
        lines += ([f"- {t}" for t in bundle.missing_report_types]
                  or ["- (none missing)"])
        lines += ["", "## Safety status summary", "",
                  f"- status: {bundle.safety_status_summary.get('status')}",
                  f"- unresolved blockers: "
                  f"{bundle.safety_status_summary.get('unresolved_blocker_count')}",
                  "", "## Limitations", ""]
        lines += [f"- {lim}" for lim in _LIMITATIONS]
        path = os.path.join(bundle.bundle_dir, "README.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
