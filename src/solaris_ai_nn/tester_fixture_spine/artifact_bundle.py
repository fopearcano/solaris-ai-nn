"""Tester artifact bundle -- a local, human-readable bundle for trusted testers.

:class:`TesterBundleBuilder` assembles a local bundle directory under
``.solaris_ai_nn_tester/bundles/TESTER_BUNDLE_<run_id>/`` containing copies (or
references) of the tester run summary, fixture pack, golden manifest, validation/
quarantine/membrane/integration/observation reports, optional ontogenesis/semiogenesis/
cognition summaries, safety and claim-safety reports, reproducibility/regression
checks, the list of known skipped stages, a tester feedback form placeholder, and a
README_FOR_TESTER.md. The bundle is local only: it is never zipped automatically,
never uploaded, never published, and contains no secrets or private data.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TesterBundleManifest:
    """The manifest listing every bundle entry and any missing optional ones."""

    run_id: str = ""
    bundle_dir: str = ""
    entries: List[Dict[str, Any]] = field(default_factory=list)
    missing_optional: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tester_bundle_run_id": self.run_id,
            "bundle_dir": self.bundle_dir,
            "entry_count": len(self.entries),
            "missing_optional_artifacts": list(self.missing_optional),
            "entries": list(self.entries),
            "local_only": True, "zipped": False, "uploaded": False,
            "published": False, "contains_secrets": False,
            "note": "the tester bundle is local-only and human-readable; nothing "
                    "is zipped automatically, uploaded, or published",
        }


@dataclass
class TesterArtifactBundle:
    """A built tester artifact bundle (directory + manifest)."""

    manifest: TesterBundleManifest
    readme_path: str = ""
    feedback_form_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"manifest": self.manifest.to_dict(),
                "readme_path": self.readme_path,
                "feedback_form_path": self.feedback_form_path}


_README = """# README for tester

This is a **fixture-only** tester bundle for Solaris-AI-NN. It is a known-good
organismic rehearsal that runs before any real birth/live testing.

## What this bundle is

A local, human-readable copy of the artifacts produced by a deterministic fixture
tester demo: the fixture pack, validation/quarantine results, environmental-membrane
sensory impressions, the membrane-integration audit, the observation summary, optional
ontogenesis/semiogenesis/cognition summaries, the claim/safety scan, and the
reproducibility/regression checks.

## How to read it

- Start with `TESTER_RUN_SUMMARY.json` and `TESTER_DEMO_REPORT.md`.
- `BUNDLE_MANIFEST.json` lists every entry and any missing optional artifacts.
- `SKIPPED_STAGES.json` lists optional stages that were skipped honestly.
- `REPRODUCIBILITY.json` / `REGRESSION.json` summarise the checks.

## What this bundle is NOT

- It did **not** require live data and started/stopped/controlled **no** feeder.
- It controlled **no** hardware and accessed **no** network/Git/GitHub/shell/browser/OS.
- It executed **no** command from fixture text and treated **no** human label or debug
  gloss as ground truth.
- Your tester feedback is **not** used as training and is **not** treated as ground
  truth.
- Fixture success is a reproducibility signal; it is **not** evidence of consciousness,
  sentience, biological life, personhood, agency, free will, emotion, feeling,
  understanding, self-awareness, autonomous self-improvement, or subjective experience.
"""

_FEEDBACK_FORM = """# Tester feedback form (placeholder)

This is a local placeholder. Tester feedback is collected for human review only; it is
NOT used as training data and NOT treated as ground truth.

- Did the tester demo run to completion? (yes/no)
- Were any stages unexpectedly skipped? (notes)
- Did the reproducibility check pass? (yes/no)
- Did the regression check pass? (yes/no)
- Free-form notes:

(Do not include secrets, credentials, or private data in this file.)
"""


@dataclass
class TesterBundleBuilder:
    """Builds the local tester artifact bundle directory and manifest."""

    def build(self, *, state_dir: str, run_id: str,
              run_summary: Dict[str, Any],
              artifacts: Dict[str, Optional[str]],
              optional_artifacts: Optional[Dict[str, Optional[str]]] = None,
              skipped_stages: Optional[List[str]] = None,
              inline: Optional[Dict[str, Any]] = None,
              dry_run: bool = False) -> TesterArtifactBundle:
        bundle_dir = os.path.join(state_dir, "bundles",
                                  f"TESTER_BUNDLE_{run_id}")
        manifest = TesterBundleManifest(run_id=run_id, bundle_dir=bundle_dir)
        if dry_run:
            return TesterArtifactBundle(manifest=manifest)
        os.makedirs(bundle_dir, exist_ok=True)

        # Inline JSON documents written directly into the bundle.
        inline = dict(inline or {})
        inline.setdefault("TESTER_RUN_SUMMARY.json", run_summary)
        inline.setdefault("SKIPPED_STAGES.json",
                          {"skipped_optional_stages": list(skipped_stages or [])})
        for name, obj in inline.items():
            path = os.path.join(bundle_dir, name)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, indent=2, default=str)
            manifest.entries.append({"name": name, "kind": "inline",
                                     "required": True})

        # Copy referenced artifacts (required + optional).
        def _copy(label: str, src: Optional[str], required: bool) -> None:
            if src and os.path.isfile(src):
                dest_name = f"{label}__{os.path.basename(src)}"
                shutil.copy(src, os.path.join(bundle_dir, dest_name))
                manifest.entries.append({"name": dest_name, "kind": "copy",
                                         "label": label, "required": required,
                                         "source": src})
            else:
                if required:
                    manifest.entries.append({"name": label, "kind": "missing",
                                             "required": True, "source": src})
                else:
                    manifest.missing_optional.append(label)

        for label, src in (artifacts or {}).items():
            _copy(label, src, required=True)
        for label, src in (optional_artifacts or {}).items():
            _copy(label, src, required=False)

        readme_path = os.path.join(bundle_dir, "README_FOR_TESTER.md")
        with open(readme_path, "w", encoding="utf-8") as fh:
            fh.write(_README)
        manifest.entries.append({"name": "README_FOR_TESTER.md", "kind": "doc",
                                 "required": True})

        feedback_path = os.path.join(bundle_dir, "TESTER_FEEDBACK_FORM.md")
        with open(feedback_path, "w", encoding="utf-8") as fh:
            fh.write(_FEEDBACK_FORM)
        manifest.entries.append({"name": "TESTER_FEEDBACK_FORM.md",
                                 "kind": "doc", "required": True})

        manifest_path = os.path.join(bundle_dir, "BUNDLE_MANIFEST.json")
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest.to_dict(), fh, indent=2, default=str)

        return TesterArtifactBundle(manifest=manifest, readme_path=readme_path,
                                    feedback_form_path=feedback_path)
