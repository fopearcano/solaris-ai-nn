"""Tester live bundle -- a local, human-readable bundle for a live-read-only run.

:class:`TesterLiveBundleBuilder` assembles a local bundle directory under
``.solaris_ai_nn_tester/live/bundles/LIVE_TESTER_BUNDLE_<run_id>/`` with copies or
references to the live tester report, the doctor report, a (redactable) governance and
feeder-registry summary, the safe/unsafe pack validation, the birth/membrane/
integration/observation reports, the quarantine report, the safety report, the
checklist, a README, and a feedback-form placeholder. The bundle is local only: never
zipped automatically, never uploaded, never published. Redactions and missing artifacts
are listed clearly.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TesterLiveBundleManifest:
    """The manifest listing every bundle entry, redactions, and missing items."""

    run_id: str = ""
    bundle_dir: str = ""
    entries: List[Dict[str, Any]] = field(default_factory=list)
    redactions: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "live_tester_bundle_run_id": self.run_id,
            "bundle_dir": self.bundle_dir,
            "entry_count": len(self.entries),
            "redactions": list(self.redactions),
            "missing_artifacts": list(self.missing),
            "entries": list(self.entries),
            "local_only": True, "zipped": False, "uploaded": False,
            "published": False,
            "note": "the live tester bundle is local-only and human-readable; "
                    "nothing is zipped automatically, uploaded, or published",
        }


@dataclass
class TesterLiveBundle:
    """A built tester live bundle (directory + manifest)."""

    manifest: TesterLiveBundleManifest
    readme_path: str = ""
    feedback_form_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"manifest": self.manifest.to_dict(),
                "readme_path": self.readme_path,
                "feedback_form_path": self.feedback_form_path}


_README = """# README for live tester

This is a **live-read-only** tester bundle for Solaris-AI-NN. It records a local
live-read-only run that a trusted tester performed after the fixture demo.

## What this is

A local, human-readable copy of the artifacts from a live-read-only run: the governance
and feeder-registry summary, the safe/unsafe event-pack validation, the live tester
doctor result, and (if run) the Live Birth, Environmental Membrane, Membrane
Integration, and Live Observation reports, plus the quarantine summary.

## The external feeder rule

**Solaris does not run feeders.** Feeders are dumb external scripts or manual files that
the tester/operator runs by hand. Solaris validated the events that appeared in the
local inbox and turned the accepted ones into sensory impressions -- it never started,
stopped, scheduled, or controlled any feeder.

## What this is NOT

- Solaris started/stopped/controlled **no** feeder and controlled **no** hardware.
- Solaris accessed **no** network/Git/GitHub/shell/browser/OS.
- Solaris executed **no** command from sensory text and treated **no** human label or
  debug gloss as ground truth.
- Your tester feedback is **not** used as training.
- A successful live-read-only run is operational evidence; it is **not** evidence of
  consciousness, sentience, biological life, personhood, agency, free will, emotion,
  feeling, understanding, self-awareness, autonomous self-improvement, or subjective
  experience.
"""

_FEEDBACK_FORM = """# Live tester feedback form (placeholder)

Local placeholder. Tester feedback is for human review only; it is NOT training data
and NOT ground truth.

- Did the live-read-only run complete? (yes/no)
- Did governance and the feeder registry validate? (yes/no)
- Were unsafe events quarantined as expected? (yes/no)
- Did the membrane produce sensory impressions? (yes/no)
- Free-form notes:

(Do not include secrets, credentials, or private data in this file.)
"""


@dataclass
class TesterLiveBundleBuilder:
    """Builds the local tester live bundle directory and manifest."""

    def build(self, runtime: Any) -> TesterLiveBundle:
        run_id = runtime.run_id
        bundle_dir = runtime.bundle_dir
        manifest = TesterLiveBundleManifest(run_id=run_id, bundle_dir=bundle_dir)
        if runtime.dry_run:
            return TesterLiveBundle(manifest=manifest)
        os.makedirs(bundle_dir, exist_ok=True)

        privacy = self._privacy_redaction(runtime)

        # Inline documents.
        inline = {
            "LIVE_TESTER_RUN_SUMMARY.json": runtime._run_summary(),
            "LIVE_DOCTOR.json": runtime.doctor_result.to_dict()
            if runtime.doctor_result else {},
            "SAMPLE_VALIDATION.json": runtime.sample_validation,
            "QUARANTINE_SUMMARY.json": runtime.quarantine_summary,
            "GOVERNANCE_SUMMARY.json": self._governance_summary(
                runtime, privacy),
            "FEEDER_REGISTRY_SUMMARY.json": runtime.feeder_status,
            "SAFETY_STATUS.json": runtime.safety.snapshot(),
        }
        for name, obj in inline.items():
            with open(os.path.join(bundle_dir, name), "w",
                      encoding="utf-8") as fh:
                json.dump(obj, fh, indent=2, default=str)
            manifest.entries.append({"name": name, "kind": "inline"})

        # Referenced report artifacts (required + optional).
        live = runtime.state_dir
        m = os.path.join(live, "membrane")
        refs = {
            "live_tester_report": runtime.reports.get("markdown"),
            "live_tester_safety_report": runtime.reports.get("safety_markdown"),
            "membrane_report": _exists(os.path.join(
                m, "reports", "ENVIRONMENTAL_MEMBRANE_REPORT.json")),
            "membrane_integration_report": _exists(os.path.join(
                m, "integration", "MEMBRANE_INTEGRATION_REPORT.json")),
            "observation_report": _exists(os.path.join(
                live, "observation", "reports", "LIVE_OBSERVATION_REPORT.json")),
            "checklist": _exists(os.path.join(
                runtime.tester_state_dir, "checklists",
                "TESTER_LIVE_CHECKLIST.md")),
        }
        for label, src in refs.items():
            if src and os.path.isfile(src):
                dest = f"{label}__{os.path.basename(src)}"
                shutil.copy(src, os.path.join(bundle_dir, dest))
                manifest.entries.append({"name": dest, "kind": "copy",
                                         "label": label})
            else:
                manifest.missing.append(label)

        manifest.redactions.extend(privacy)
        readme_path = os.path.join(bundle_dir, "README_FOR_LIVE_TESTER.md")
        with open(readme_path, "w", encoding="utf-8") as fh:
            fh.write(_README)
        feedback_path = os.path.join(bundle_dir, "LIVE_TESTER_FEEDBACK_FORM.md")
        with open(feedback_path, "w", encoding="utf-8") as fh:
            fh.write(_FEEDBACK_FORM)
        manifest.entries.append({"name": "README_FOR_LIVE_TESTER.md",
                                 "kind": "doc"})
        manifest.entries.append({"name": "LIVE_TESTER_FEEDBACK_FORM.md",
                                 "kind": "doc"})

        with open(os.path.join(bundle_dir, "BUNDLE_MANIFEST.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(manifest.to_dict(), fh, indent=2, default=str)
        return TesterLiveBundle(manifest=manifest, readme_path=readme_path,
                                feedback_form_path=feedback_path)

    @staticmethod
    def _privacy_redaction(runtime: Any) -> List[str]:
        # Governance approver identity is redacted from the bundle summary.
        redactions = []
        gov = runtime.governance_status or {}
        if gov.get("status") == "approved":
            redactions.append("governance approver identity redacted from "
                              "bundle summary")
        return redactions

    @staticmethod
    def _governance_summary(runtime: Any, privacy: List[str]) -> Dict[str, Any]:
        gov = dict(runtime.governance_status or {})
        # Never copy approver identity / raw event payloads into the bundle.
        gov.pop("approved_by", None)
        gov["redacted"] = bool(privacy)
        return gov


def _exists(path: str) -> Optional[str]:
    return path if os.path.isfile(path) else None
