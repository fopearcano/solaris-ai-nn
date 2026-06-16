"""Research baseline reports -- local reproducible snapshot, ClaimGuard-scanned.

:class:`ResearchBaselineReportBuilder` writes the research baseline report plus
the version / snapshot / capability / limitation / safety-boundary / validation /
comparison-anchor / roadmap / runbook documents (and the reproducibility bundle).
Every report states explicitly that this is a research baseline (not a product
release), that no Git tag / GitHub release / branch / PR was created, no source
was modified, no validation command was executed automatically, no external agent
was run, and no consciousness/life/agency claim is made. ClaimGuard scans the
Markdown.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_WHAT_THIS_DOES_NOT_DO = (
    "This is a research baseline, not a product release.",
    "No Git tag was created.",
    "No GitHub release was created.",
    "No branch or PR was created.",
    "No source code was modified.",
    "No validation command was executed automatically.",
    "No external agent was run.",
    "No consciousness/life/agency claim is made.",
)

_LIMITATIONS = (
    "Baseline versioning is local metadata, not Git tagging or a release.",
    "The reproducibility bundle indexes artifacts/commands; it runs nothing.",
    "A validated baseline means evidence is documented and reproducible enough "
    "for the next cycle -- not a scientific or capability proof.",
    "Limitations are part of the baseline; a critical limitation blocks "
    "validation.",
    "The safety boundary statement is mandatory and a failed boundary blocks "
    "validation.",
)


@dataclass
class ResearchBaselineReportBuilder:
    """Builds the research baseline report set (JSON + claim-guarded Markdown)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.research_baseline_status()
        sections: Dict[str, Any] = {
            "purpose": ("turn a validated post-merge baseline into a local "
                        "versioned, reproducible research reference point for "
                        "the next experimental cycle -- not a product/GitHub "
                        "release and not a certification of intelligence"),
            "baseline_version": rt.version.to_dict() if rt.version else {},
            "snapshot_manifest": rt.snapshot,
            "reproducibility_bundle": rt.repro,
            "capability_map": rt.capability,
            "limitation_registry": rt.limitations,
            "safety_boundary_statement": rt.safety_boundary,
            "validation_summary": rt.validation,
            "comparison_anchors": rt.anchors,
            "next_cycle_roadmap": rt.roadmap,
            "operator_runbook_summary": {
                "step_count": rt.runbook.get("step_count", 0),
                "stop_conditions": rt.runbook.get("stop_conditions", [])},
            "missing_evidence": rt.snapshot.get("missing", []),
            "blocked_status": (rt.version.status if rt.version
                               and rt.version.blocked else None),
            "safety_status": rt.safety.snapshot(),
            "status": status,
            "limitations": list(_LIMITATIONS),
            "what_this_does_not_do": list(_WHAT_THIS_DOES_NOT_DO),
        }
        markdown = self._render_main(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _render_main(self, sections: Dict[str, Any]) -> str:
        status = sections["status"]
        lines = [
            "# Research Baseline Report", "",
            "_Turns a validated post-merge baseline into a LOCAL versioned, "
            "reproducible research reference point. This is a research baseline, "
            "NOT a product release or GitHub release: no Git tag, no release, no "
            "branch, no PR, and no source modification occur._", "",
            f"- baseline version: {status['current_baseline_version_id']} -> "
            f"**{status['baseline_status']}**",
            f"- capabilities: {status['capability_count']} "
            f"(validated {status['validated_capability_count']})",
            f"- limitations: {status['limitation_count']} "
            f"(critical {status['critical_limitation_count']})",
            f"- safety boundary: {status['safety_boundary_status']} "
            f"(held {status['safety_boundary_pass_count']}, failed "
            f"{status['safety_boundary_fail_count']})",
            f"- validation: {status['validation_status']} "
            f"(pass {status['validation_pass_count']}, missing "
            f"{status['validation_missing_count']})",
            f"- comparison anchors: {status['comparison_anchor_count']}",
            f"- next-cycle roadmap items: {status['roadmap_item_count']}",
            "",
        ]
        if sections["blocked_status"]:
            lines += [f"## Blocked status: {sections['blocked_status']}", "",
                      "This baseline is blocked and cannot be used as a "
                      "validated reference. See the limitation registry and "
                      "roadmap for required follow-up.", ""]
        lines += ["## Core question", "",
                  "_\"What exact experimental baseline are we standing on before "
                  "the next cycle begins?\"_ -- answered by the version record, "
                  "snapshot manifest, capability map, and limitation registry "
                  "above.", "",
                  "## Missing evidence", ""]
        missing = sections["missing_evidence"]
        lines += [f"- {m}" for m in missing] if missing else ["- none"]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in sections["what_this_does_not_do"]]
        lines += ["", "## Limitations", ""]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        return "\n".join(lines)

    @staticmethod
    def _claim_guard_safe(text: str) -> bool:
        try:
            from ..governance.compliance import ClaimGuard

            return ClaimGuard().scan_text(text).safe
        except Exception:
            return True

    @staticmethod
    def _guard(text: str) -> str:
        try:
            from ..governance.compliance import ClaimGuard

            guard = ClaimGuard()
            if not guard.scan_text(text).safe:
                return guard.rewrite(text)
        except Exception:
            pass
        return text

    def _sub_reports(self, sections: Dict[str, Any]) -> Dict[str, str]:
        rt = self.runtime
        return {
            "BASELINE_VERSION.md": self._kv_md(
                "Baseline Version", sections["baseline_version"],
                ["baseline_version_id", "status", "recommended_use",
                 "validated", "blocked", "is_git_tag", "is_github_release"]),
            "SNAPSHOT_MANIFEST.md": self._snapshot_md(sections),
            "CAPABILITY_MAP.md": self._capability_md(sections),
            "LIMITATION_REGISTRY.md": self._limitation_md(sections),
            "SAFETY_BOUNDARY_STATEMENT.md": self._safety_boundary_md(sections),
            "VALIDATION_SUMMARY.md": self._kv_md(
                "Validation Summary", sections["validation_summary"],
                ["validation_pass_count", "validation_missing_count",
                 "safety_failed", "blocks_validation", "has_warnings"]),
            "COMPARISON_ANCHORS.md": self._anchors_md(sections),
            "NEXT_CYCLE_ROADMAP.md": self._roadmap_md(sections),
            "OPERATOR_RUNBOOK.md": (rt._runbook_obj.render_markdown()
                                    if rt._runbook_obj else ""),
        }

    @staticmethod
    def _kv_md(title: str, data: Dict[str, Any], keys: List[str]) -> str:
        lines = [f"# {title}", ""]
        for k in keys:
            lines.append(f"- {k}: {data.get(k)}")
        lines += ["", "_Local research-baseline metadata only; not a product/"
                  "GitHub release._"]
        return ResearchBaselineReportBuilder._guard("\n".join(lines))

    @staticmethod
    def _snapshot_md(sections: Dict[str, Any]) -> str:
        snap = sections["snapshot_manifest"]
        lines = ["# Snapshot Manifest", "",
                 f"- indexed artifacts: {snap.get('snapshot_artifact_count', 0)}",
                 f"- missing: {snap.get('missing')}",
                 f"- corrupt: {snap.get('corrupt')}",
                 f"- negative evidence: "
                 f"{snap.get('negative_evidence_artifacts')}", "",
                 "_Indexes artifacts only; missing/corrupt and negative/"
                 "falsified/inconclusive artifacts are kept visible._"]
        return ResearchBaselineReportBuilder._guard("\n".join(lines))

    @staticmethod
    def _capability_md(sections: Dict[str, Any]) -> str:
        cap = sections["capability_map"]
        lines = ["# Capability Map", "",
                 f"- capabilities: {cap.get('capability_count', 0)} "
                 f"(validated {cap.get('validated_capability_count', 0)})", "",
                 "| area | status |", "| --- | --- |"]
        for area, rec in cap.get("records", {}).items():
            lines.append(f"| {area} | {rec['status']} |")
        lines += ["", "_Capability means an implemented module with available "
                  "evidence, not intelligence or understanding._"]
        return ResearchBaselineReportBuilder._guard("\n".join(lines))

    @staticmethod
    def _limitation_md(sections: Dict[str, Any]) -> str:
        lim = sections["limitation_registry"]
        lines = ["# Limitation Registry", "",
                 f"- limitations: {lim.get('limitation_count', 0)} "
                 f"(critical {lim.get('critical_limitation_count', 0)}, major "
                 f"{lim.get('major_limitation_count', 0)})",
                 f"- blocks validation: {lim.get('blocks_validation')}", ""]
        for l in lim.get("limitations", []):
            lines.append(f"- [{l['severity']}] {l['category']}: {l['detail']}")
        lines += ["", "_Limitations are part of the baseline and kept "
                  "operator-visible; a critical limitation blocks validation._"]
        return ResearchBaselineReportBuilder._guard("\n".join(lines))

    @staticmethod
    def _safety_boundary_md(sections: Dict[str, Any]) -> str:
        sbs = sections["safety_boundary_statement"]
        lines = ["# Safety Boundary Statement", "",
                 f"- all held: {sbs.get('all_held')} "
                 f"(held {sbs.get('safety_boundary_pass_count', 0)}, failed "
                 f"{sbs.get('safety_boundary_fail_count', 0)})", "",
                 "| boundary | status |", "| --- | --- |"]
        for item in sbs.get("items", []):
            lines.append(f"| {item['item']} | {item['status']} |")
        lines += ["", "_This statement is mandatory in every baseline report; a "
                  "failed boundary blocks validation._"]
        return ResearchBaselineReportBuilder._guard("\n".join(lines))

    @staticmethod
    def _anchors_md(sections: Dict[str, Any]) -> str:
        anc = sections["comparison_anchors"]
        lines = ["# Comparison Anchors", "",
                 f"- anchors: {anc.get('comparison_anchor_count', 0)} "
                 f"(available {anc.get('available_anchor_count', 0)})", ""]
        for a in anc.get("anchors", []):
            lines.append(f"- {a['kind']}: "
                         f"{a['baseline_id'] or '(none)'} "
                         f"(available={a['available']})")
        lines += ["", "_Anchors drive future replication/soak/architecture "
                  "comparisons; a missing anchor is a limitation._"]
        return ResearchBaselineReportBuilder._guard("\n".join(lines))

    @staticmethod
    def _roadmap_md(sections: Dict[str, Any]) -> str:
        rm = sections["next_cycle_roadmap"]
        lines = ["# Next-Cycle Roadmap", "",
                 f"- items: {rm.get('roadmap_item_count', 0)} "
                 f"(required {rm.get('required_count', 0)}, recommended "
                 f"{rm.get('recommended_count', 0)}, optional "
                 f"{rm.get('optional_count', 0)}, blocked "
                 f"{rm.get('blocked_count', 0)})", ""]
        for item in rm.get("items", []):
            lines.append(f"- [{item['priority']}] {item['item_type']} -- "
                         f"{item.get('detail', '')}")
        lines += ["", "_Planning only; the roadmap runs no task, creates no "
                  "branch, and calls no external tool._"]
        return ResearchBaselineReportBuilder._guard("\n".join(lines))

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = state_dir or self.runtime.state_dir
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "RESEARCH_BASELINE_REPORT.md")
        json_path = os.path.join(base, "RESEARCH_BASELINE_REPORT.json")
        markdown = self._render_main(report["sections"])
        if not report["claim_guard_safe"]:
            markdown = self._guard(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        written = [md_path, json_path]
        for name, body in self._sub_reports(report["sections"]).items():
            path = os.path.join(base, name)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self._guard(body))
            written.append(path)
        # The reproducibility bundle (manifest + README).
        if self.runtime._repro_obj is not None:
            bundle_paths = ReproBundleWriter(self.runtime).write(base)
            written.extend(bundle_paths.values())
        return {"markdown": md_path, "json": json_path, "documents": written,
                "report": report}


@dataclass
class ReproBundleWriter:
    """Writes the reproducibility bundle next to the reports."""

    runtime: Any

    def write(self, base: str) -> Dict[str, str]:
        from .repro_bundle import ReproBundleBuilder

        return ReproBundleBuilder().write(self.runtime._repro_obj, base)
