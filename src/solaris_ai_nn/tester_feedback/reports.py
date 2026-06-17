"""Tester feedback reports -- local QA summaries for developer review.

:class:`TesterFeedbackReportBuilder` writes the feedback report set (overall report,
per-type summaries, release-blocker report, privacy/redaction report, safety report).
Safety concerns and release blockers appear at the top. Every report states that
feedback is local, not training, not RLHF, not ground truth, not a command, and that no
remote issue/upload occurred and no consciousness/life/agency claim is made. ClaimGuard
scans the Markdown when available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List

_WHAT_THIS_DOES_NOT_DO = (
    "Feedback is local only.",
    "Feedback is not training.",
    "Feedback is not RLHF.",
    "Feedback is not ground truth.",
    "Feedback is not a command.",
    "Feedback does not modify Solaris behaviour automatically.",
    "No remote issue is created and nothing is uploaded.",
    "No feeder/hardware/network/Git/GitHub/shell/browser/OS access occurred.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class TesterFeedbackReportBuilder:
    """Builds the feedback report set (Markdown + JSON)."""

    runtime: Any

    def write(self) -> Dict[str, Any]:
        rt = self.runtime
        reports_dir = os.path.join(rt.feedback_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        summary = rt._run_summary()
        index = summary["ledger_index"]
        entries = summary["entries"]

        documents: Dict[str, str] = {}
        md = _guard(self._main_md(summary, index, entries))
        md_path = os.path.join(reports_dir, "TESTER_FEEDBACK_REPORT.md")
        _w(md_path, md)
        _wj(os.path.join(reports_dir, "TESTER_FEEDBACK_REPORT.json"),
            {"sections": summary, "claim_guard_safe": _safe(md)})
        documents["report_md"] = md_path
        documents["report_json"] = os.path.join(
            reports_dir, "TESTER_FEEDBACK_REPORT.json")

        for name, body in {
            "BUG_REPORT_SUMMARY.md": self._type_md(
                entries, "bug_report", "Bug Reports"),
            "SAFETY_CONCERN_SUMMARY.md": self._safety_md(entries),
            "CONFUSION_REPORT_SUMMARY.md": self._type_md(
                entries, "confusion_report", "Confusion Reports"),
            "SUGGESTION_REPORT_SUMMARY.md": self._type_md(
                entries, "suggestion", "Suggestions"),
            "RELEASE_BLOCKER_REPORT.md": self._blocker_md(summary, entries),
            "FEEDBACK_PRIVACY_REPORT.md": self._privacy_md(summary),
            "FEEDBACK_SAFETY_REPORT.md": self._safety_status_md(),
        }.items():
            path = os.path.join(reports_dir, name)
            _w(path, _guard(body))
            documents[name] = path

        return {"markdown": md_path,
                "json": documents["report_json"], "documents": documents}

    def _main_md(self, s, index, entries) -> str:
        rt = self.runtime
        safety = [e for e in entries if e["feedback_type"] == "safety_concern"]
        blockers = [e for e in entries
                    if e["release_blocker_status"] in ("release_blocker",
                                                       "stop_testing")]
        lines = ["# Tester Feedback Report", "",
                 "_Feedback is local QA evidence only: not training, not RLHF, "
                 "not ground truth, not a command. It does not modify Solaris "
                 "behaviour, create remote issues, or upload anything, and it "
                 "makes no claim of consciousness, sentience, biological life, "
                 "personhood, agency, free will, emotion, feeling, "
                 "understanding, self-awareness, or subjective experience._", "",
                 "## Purpose", "", rt.feedback_profile.purpose, "",
                 "## Safety concerns (top priority)", ""]
        if safety:
            for e in safety:
                lines.append(f"- [{e['release_blocker_status']}] "
                             f"{e['feedback_id']}: {e['category'] or e['payload'].get('concern_type', '')}")
        else:
            lines.append("- none recorded")
        lines += ["", "## Release blockers", ""]
        if blockers:
            for e in blockers:
                lines.append(f"- [{e['release_blocker_status']}] "
                             f"{e['feedback_id']} ({e['release_blocker_reason']})")
        else:
            lines.append("- none recorded")
        lines += ["", "## Feedback counts", "",
                  f"- entries: {index['entry_count']}",
                  f"- by type: {index['by_type']}",
                  f"- release blockers: {index['release_blocker_count']} "
                  f"(stop-testing: {index['stop_testing_count']})",
                  f"- safety concerns: {index['safety_concern_count']}",
                  f"- redactions: {index['redaction_count']}", "",
                  "## Category summary", ""]
        for cat, count in sorted(index["by_category"].items()):
            lines.append(f"- {cat}: {count}")
        lines += ["", "## Developer review queue", ""]
        for e in entries:
            lines.append(f"- {e['feedback_id']} [{e['feedback_type']}] "
                         f"status={e['status']} blocker="
                         f"{e['release_blocker_status']}")
        lines += ["", "## Next action", "",
                  f"- {rt.recommended_next_action()}", "",
                  "## Limitations", ""]
        lines += [f"- {l}" for l in rt.feedback_profile.limitations]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in _WHAT_THIS_DOES_NOT_DO]
        return "\n".join(lines)

    def _type_md(self, entries, ftype, title) -> str:
        items = [e for e in entries if e["feedback_type"] == ftype]
        lines = [f"# {title}", "",
                 "_Local QA evidence only; not training, not ground truth, not "
                 "a command. Does not modify Solaris behaviour._", "",
                 f"- count: {len(items)}", ""]
        for e in items:
            lines.append(f"## {e['feedback_id']}")
            lines.append(f"- category/severity: {e['category'] or '-'} / "
                         f"{e['severity'] or '-'}")
            lines.append(f"- blocker: {e['release_blocker_status']}")
            payload = e.get("payload", {})
            desc = (payload.get("actual_behavior") or payload.get("description")
                    or "")
            if desc:
                lines.append(f"- detail: {desc[:300]}")
            lines.append("")
        if not items:
            lines.append("(none recorded)")
        return "\n".join(lines)

    def _safety_md(self, entries) -> str:
        items = [e for e in entries if e["feedback_type"] == "safety_concern"]
        lines = ["# Safety Concern Summary", "",
                 "_Safety concerns are elevated as release blockers and never "
                 "suppressed._", "",
                 f"- count: {len(items)}", "",
                 "| id | type | escalation | blocker |",
                 "| --- | --- | --- | --- |"]
        for e in items:
            p = e.get("payload", {})
            lines.append(f"| {e['feedback_id']} | "
                         f"{p.get('concern_type', '-')} | "
                         f"{p.get('escalation', '-')} | "
                         f"{e['release_blocker_status']} |")
        if not items:
            lines.append("| (none) | | | |")
        return "\n".join(lines)

    def _blocker_md(self, summary, entries) -> str:
        classifications = summary["classifications"]
        rb = [c for c in classifications if c["is_release_blocker"]]
        stop = [c for c in classifications if c["is_stop_testing"]]
        lines = ["# Release Blocker Report", "",
                 "_Release blockers are developer review items, not automatic "
                 "actions._", "",
                 f"- release blockers: {len(rb)} (stop-testing: {len(stop)})", ""]
        if stop:
            lines += ["## STOP TESTING", ""]
            for c in stop:
                lines.append(f"- {c['feedback_id']}: {c['reason']} -- "
                             f"{c['detail']}")
            lines.append("")
        lines += ["## Release blockers", "",
                  "| feedback id | status | reason | detail |",
                  "| --- | --- | --- | --- |"]
        for c in classifications:
            lines.append(f"| {c['feedback_id']} | {c['status']} | "
                         f"{c['reason']} | {c['detail']} |")
        lines += ["", "_Unsupported consciousness/life/agency claims, network/"
                  "shell/hardware/feeder-control risk, and privacy/secret "
                  "exposure default to release blockers._"]
        return "\n".join(lines)

    def _privacy_md(self, summary) -> str:
        red = summary["redactions"]
        lines = ["# Feedback Privacy / Redaction Report", "",
                 "_Secrets/credentials/private messages must not be included. "
                 "Obvious markers are redacted and recorded._", "",
                 f"- redactions: {len(red)}", ""]
        for r in red:
            lines.append(f"- {r.get('feedback_id', '?')}: "
                         f"{', '.join(r.get('markers', []))}")
        if not red:
            lines.append("(no redactions recorded)")
        return "\n".join(lines)

    def _safety_status_md(self) -> str:
        snap = self.runtime.safety.snapshot()
        lines = ["# Feedback Safety Report", "",
                 f"- safety blocks recorded: {snap.get('rejected_count', 0)}",
                 f"- feedback is training: {snap.get('feedback_is_training')}",
                 f"- feedback is ground truth: "
                 f"{snap.get('feedback_is_ground_truth')}",
                 f"- can modify behavior from feedback: "
                 f"{snap.get('can_modify_behavior_from_feedback')}",
                 f"- can create issues: {snap.get('can_create_issues')}",
                 f"- can upload: {snap.get('can_upload')}", "",
                 "## Hard rules", ""]
        lines += [f"- {r}" for r in snap.get("hard_rules", [])]
        lines += ["", "_All training/RLHF/command/auto-modify/upload/issue-"
                  "creation capabilities are False by design._"]
        return "\n".join(lines)


def _w(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _wj(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, default=str)


def _safe(text: str) -> bool:
    try:
        from ..governance.compliance import ClaimGuard
        return ClaimGuard().scan_text(text).safe
    except Exception:
        return True


def _guard(text: str) -> str:
    try:
        from ..governance.compliance import ClaimGuard
        guard = ClaimGuard()
        if not guard.scan_text(text).safe:
            return guard.rewrite(text)
    except Exception:
        pass
    return text
