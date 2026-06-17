"""Tester RC bundle builder -- the local-only release-candidate bundle.

:class:`TesterRCBundleBuilder` assembles a local bundle directory containing the RC docs,
manifest, readiness report, safety docs, install guide, packaging/safety reports, feedback
forms, feeder templates, governance template, and event-pack examples. The bundle is local
only: nothing is uploaded, published, tagged, or released. A bundle manifest lists every
included and missing artifact. Zipping is optional and local-only (off by default).
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TesterRCBundleManifest:
    """Lists every included and missing artifact in the local bundle."""

    bundle_dir: str = ""
    included: List[Dict[str, str]] = field(default_factory=list)
    missing: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bundle_version": "tester_rc_bundle_v0",
            "bundle_dir": self.bundle_dir,
            "included_count": len(self.included),
            "missing_count": len(self.missing),
            "included": list(self.included),
            "missing": list(self.missing),
            "local_only": True, "uploaded": False, "published": False,
            "zipped": False, "includes_private_payloads": False,
            "note": "local RC bundle manifest; nothing was uploaded, published, "
                    "tagged, or released, and no private payloads/secrets are "
                    "included",
        }

    def to_markdown(self) -> str:
        d = self.to_dict()
        lines = ["# Tester RC Bundle Manifest", "",
                 f"- bundle dir: `{d['bundle_dir']}`",
                 f"- included: {d['included_count']}; missing: "
                 f"{d['missing_count']}", "", "## Included", ""]
        lines += [f"- {a['name']} (from `{a['source']}`)"
                  for a in d["included"]] or ["- none"]
        lines += ["", "## Missing", ""]
        lines += [f"- {a['name']} (expected `{a['source']}`)"
                  for a in d["missing"]] or ["- none"]
        lines += ["", "_Local RC bundle. Nothing was uploaded, published, "
                  "tagged, or released. Share it manually only if requested._"]
        return "\n".join(lines)


@dataclass
class TesterRCBundle:
    """A built local RC bundle (a directory, not an upload)."""

    bundle_dir: str
    manifest: TesterRCBundleManifest
    zip_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {"bundle_dir": self.bundle_dir, "zip_path": self.zip_path}
        d.update(self.manifest.to_dict())
        return d


@dataclass
class TesterRCBundleBuilder:
    """Assembles the local RC bundle directory."""

    rc_id: str = ""
    bundles_root: str = ""
    docs_dir: str = ""
    manifests_dir: str = ""
    reports_dir: str = ""
    checklists_dir: str = ""
    include_zip: bool = False
    include_private_payloads: bool = False

    def build(self, *, collection, tester_state_dir: str) -> TesterRCBundle:
        bundle_dir = os.path.join(self.bundles_root,
                                  f"TESTER_RC_BUNDLE_{self.rc_id}")
        os.makedirs(bundle_dir, exist_ok=True)
        manifest = TesterRCBundleManifest(bundle_dir=bundle_dir)

        # (display name, source path). Sources may be absent.
        sources: List[Tuple[str, str]] = []
        for name in ("TESTER_RELEASE_NOTES.md", "TESTER_QUICKSTART.md",
                     "TESTER_RUNBOOK.md", "TESTER_KNOWN_ISSUES.md",
                     "TESTER_FEEDBACK_GUIDE.md"):
            sources.append((name, os.path.join(self.docs_dir, name)))
        for name in ("TESTER_RC_MANIFEST.md", "TESTER_RC_MANIFEST.json"):
            sources.append((name, os.path.join(self.manifests_dir, name)))
        for name in ("TESTER_RC_READINESS_REPORT.md",
                     "TESTER_RC_READINESS_REPORT.json"):
            sources.append((name, os.path.join(self.reports_dir, name)))
        sources.append(("TESTER_RC_CHECKLIST.md",
                        os.path.join(self.checklists_dir,
                                     "TESTER_RC_CHECKLIST.md")))
        # Repo-level safety docs.
        for name in ("TESTER_SAFETY_BOUNDARIES.md", "TESTER_CLAIM_FREEZE.md",
                     "FORBIDDEN_CLAIMS.md", "ALLOWED_OPERATIONAL_LANGUAGE.md",
                     "RED_TEAM_CHECKLIST.md", "RELEASE_BLOCKERS.md"):
            sources.append((name, os.path.join("docs", name)))
        # Collected artifacts (install guide, packaging/safety reports,
        # feedback forms).
        for key, name in (("install_guide", "TESTER_INSTALL_GUIDE.md"),
                          ("packaging_report", "PACKAGING_REPORT.md"),
                          ("safety_freeze_report",
                           "TESTER_SAFETY_FREEZE_REPORT.md"),
                          ("release_blocker_report",
                           "TESTER_RELEASE_BLOCKERS.md"),
                          ("feedback_form", "TESTER_FEEDBACK_FORM.md")):
            path = collection.path(key)
            sources.append((name, path or ""))
        # Live-read-only templates + event packs (from examples).
        tmpl = os.path.join("examples", "tester_live_readonly")
        sources.append(("EXTERNAL_FEEDER_POLICY.md",
                        os.path.join(tmpl, "README.md")))
        sources.append(("LIVE_READONLY_GOVERNANCE.tester.template.json",
                        os.path.join(
                            tmpl,
                            "LIVE_READONLY_GOVERNANCE.tester.template.json")))
        sources.append(("FEEDER_REGISTRY.tester.template.json",
                        os.path.join(
                            tmpl, "FEEDER_REGISTRY.tester.template.json")))
        sources.append(("SAFE_EVENT_PACK.jsonl",
                        os.path.join(tmpl, "sample_safe_events",
                                     "live_safe_events.jsonl")))
        sources.append(("UNSAFE_EVENT_PACK.jsonl",
                        os.path.join(tmpl, "sample_unsafe_events",
                                     "live_unsafe_events.jsonl")))

        seen = set()
        for name, src in sources:
            if name in seen:
                continue
            seen.add(name)
            if src and os.path.isfile(src):
                try:
                    shutil.copy2(src, os.path.join(bundle_dir, name))
                    manifest.included.append({"name": name, "source": src})
                except Exception:
                    manifest.missing.append({"name": name, "source": src})
            else:
                manifest.missing.append({"name": name, "source": src or name})

        # Write the bundle manifest itself.
        with open(os.path.join(bundle_dir, "BUNDLE_MANIFEST.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(manifest.to_dict(), fh, indent=2, default=str)
        with open(os.path.join(bundle_dir, "BUNDLE_MANIFEST.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(manifest.to_markdown())

        zip_path = None
        if self.include_zip:
            try:
                zip_path = shutil.make_archive(bundle_dir, "zip", bundle_dir)
            except Exception:
                zip_path = None
        return TesterRCBundle(bundle_dir=bundle_dir, manifest=manifest,
                              zip_path=zip_path)
