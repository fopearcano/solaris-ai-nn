"""Tester feedback bundle -- a local, developer-review bundle (never uploaded).

:class:`FeedbackBundleBuilder` assembles a local bundle directory under
``.solaris_ai_nn_tester/feedback/bundles/FEEDBACK_BUNDLE_<run_id>/`` with the ledger,
index, per-type summaries, the release-blocker and redaction reports, optional related
tester-console/fixture/live references, and a README for the developer. The bundle is
local only: never zipped automatically, never uploaded, never published. Private
payloads are excluded unless explicitly allowed and marked.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class FeedbackBundleManifest:
    """The manifest listing bundle entries, redactions, and privacy warnings."""

    run_id: str = ""
    bundle_dir: str = ""
    entries: List[Dict[str, Any]] = field(default_factory=list)
    redaction_count: int = 0
    missing: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_bundle_run_id": self.run_id,
            "bundle_dir": self.bundle_dir,
            "entry_count": len(self.entries),
            "redaction_count": self.redaction_count,
            "missing_artifacts": list(self.missing),
            "entries": list(self.entries),
            "local_only": True, "zipped": False, "uploaded": False,
            "published": False, "includes_private_payloads": False,
            "privacy_warning": "feedback may reference local artifact paths; "
                               "secrets/private payloads are excluded and obvious "
                               "markers are redacted",
            "note": "local developer-review bundle; nothing is zipped "
                    "automatically, uploaded, or published",
        }


@dataclass
class TesterFeedbackBundle:
    """A built feedback bundle (directory + manifest)."""

    manifest: FeedbackBundleManifest
    readme_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"manifest": self.manifest.to_dict(),
                "readme_path": self.readme_path}


_README = """# README for developer (tester feedback bundle)

This is a **local** tester-feedback bundle for developer review. Everything here is
QA evidence.

## What this is

A local copy of the append-only feedback ledger, its index, per-type summaries (bugs,
safety concerns, confusion, suggestions), the release-blocker classification report, and
the redaction report.

## What this is NOT

- Tester feedback is **not** training data, **not** RLHF, **not** ground truth, and
  **not** a command.
- It did **not** modify Solaris behaviour, create a GitHub issue, upload anything, or
  access the network/shell/Git/GitHub/browser/OS.
- Release blockers and safety concerns are **developer review items**, not automatic
  actions.
- Secrets/private payloads are excluded; obvious markers are redacted (see the
  redaction report).
- Nothing here implies consciousness, sentience, biological life, personhood, agency,
  free will, emotion, feeling, understanding, self-awareness, autonomous
  self-improvement, or subjective experience.

## How to use it

Start with `RELEASE_BLOCKER_REPORT.md` and `SAFETY_CONCERN_SUMMARY.md`, then the ledger
index. Triage each entry; update dispositions/notes in your own tracker (the ledger is
append-only).
"""


@dataclass
class FeedbackBundleBuilder:
    """Builds the local feedback bundle directory and manifest."""

    def build(self, runtime: Any) -> TesterFeedbackBundle:
        run_id = runtime.run_id
        bundle_dir = runtime.bundle_dir
        manifest = FeedbackBundleManifest(run_id=run_id, bundle_dir=bundle_dir)
        if runtime.dry_run:
            return TesterFeedbackBundle(manifest=manifest)
        os.makedirs(bundle_dir, exist_ok=True)

        # Inline run summary + redaction report.
        summary = runtime._run_summary()
        manifest.redaction_count = len(summary.get("redactions", []))
        inline = {
            "FEEDBACK_RUN_SUMMARY.json": summary,
            "REDACTION_REPORT.json": {"redactions": summary.get("redactions",
                                                                []),
                                      "redaction_count": manifest.redaction_count},
        }
        for name, obj in inline.items():
            with open(os.path.join(bundle_dir, name), "w",
                      encoding="utf-8") as fh:
                json.dump(obj, fh, indent=2, default=str)
            manifest.entries.append({"name": name, "kind": "inline"})

        # Copy ledger + reports.
        refs = {
            "ledger_jsonl": runtime.ledger.jsonl_path,
            "ledger_index": runtime.ledger.index_path,
        }
        refs.update(runtime.reports.get("documents", {}))
        # Optional related tester-console status.
        console_status = os.path.join(runtime.tester_state_dir, "console",
                                      "CONSOLE_STATUS.json")
        if os.path.isfile(console_status):
            refs["tester_console_status"] = console_status
        for label, src in refs.items():
            if src and os.path.isfile(src):
                dest = f"{label}__{os.path.basename(src)}"
                shutil.copy(src, os.path.join(bundle_dir, dest))
                manifest.entries.append({"name": dest, "kind": "copy",
                                         "label": label})
            else:
                manifest.missing.append(label)

        readme_path = os.path.join(bundle_dir, "README_FOR_DEVELOPER.md")
        with open(readme_path, "w", encoding="utf-8") as fh:
            fh.write(_README)
        manifest.entries.append({"name": "README_FOR_DEVELOPER.md",
                                 "kind": "doc"})
        with open(os.path.join(bundle_dir, "BUNDLE_MANIFEST.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(manifest.to_dict(), fh, indent=2, default=str)
        return TesterFeedbackBundle(manifest=manifest, readme_path=readme_path)
