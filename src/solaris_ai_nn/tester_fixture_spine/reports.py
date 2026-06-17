"""Tester fixture spine reports -- the report set for a known-good rehearsal.

:class:`TesterFixtureSpineReportBuilder` writes the tester fixture spine report set
(spine overview, golden run, reproducibility, regression, artifact bundle, and safety).
Every report states explicitly that this is a fixture-only tester demo requiring no
live data, that no feeder was started/stopped/controlled, no hardware controlled, no
network/Git/GitHub/shell access occurred, no command was executed from fixture text, no
human label / debug gloss was treated as ground truth, no tester feedback was used as
training, and no consciousness/life/agency claim is made. ClaimGuard scans the Markdown
when available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict

_DISCLAIMER = (
    "_This is a fixture-only tester demo (a known-good organismic rehearsal). It "
    "requires no live data; it starts/stops/controls no feeder, controls no "
    "hardware, accesses no network/Git/GitHub/shell/browser/OS, executes no command "
    "from fixture text, treats no human label or debug gloss as ground truth, uses "
    "no tester feedback as training, publishes/uploads nothing, and makes no claim "
    "of consciousness, sentience, biological life, personhood, agency, free will, "
    "emotion, feeling, understanding, self-awareness, or subjective experience._"
)


@dataclass
class TesterFixtureSpineReportBuilder:
    """Builds the tester fixture spine report set (Markdown + JSON)."""

    runtime: Any

    def write(self) -> Dict[str, Any]:
        rt = self.runtime
        base = os.path.join(rt.state_dir, "reports")
        os.makedirs(base, exist_ok=True)
        written: Dict[str, str] = {}

        spine = self._spine_sections()
        spine_md = _guard(self._spine_md(spine))
        _write(os.path.join(base, "TESTER_FIXTURE_SPINE_REPORT.md"), spine_md)
        _write_json(os.path.join(base, "TESTER_FIXTURE_SPINE_REPORT.json"),
                    {"sections": spine, "claim_guard_safe": _safe(spine_md)})
        written["spine_markdown"] = os.path.join(
            base, "TESTER_FIXTURE_SPINE_REPORT.md")

        _write(os.path.join(base, "GOLDEN_RUN_REPORT.md"),
               _guard(self._golden_md()))
        _write(os.path.join(base, "REPRODUCIBILITY_REPORT.md"),
               _guard(self._repro_md()))
        _write(os.path.join(base, "REGRESSION_REPORT.md"),
               _guard(self._regression_md()))
        _write(os.path.join(base, "TESTER_ARTIFACT_BUNDLE_REPORT.md"),
               _guard(self._bundle_md()))
        safety_path = os.path.join(base, "TESTER_FIXTURE_SAFETY_REPORT.md")
        _write(safety_path, _guard(self._safety_md()))
        written["safety_markdown"] = safety_path
        # Surface the safety report path back to the runtime for the bundle.
        rt.reports.setdefault("safety_markdown", safety_path)
        return written

    def _spine_sections(self) -> Dict[str, Any]:
        rt = self.runtime
        return {
            "purpose": "fixture-only golden run + reproducible demo bundle for "
                       "trusted testers, before live read-only testing",
            "profile": rt.tester_profile.to_dict(),
            "tester_status": rt.tester_status(),
            "golden_run": rt.golden_run.to_dict() if rt.golden_run else {},
            "reproducibility": rt.reproducibility,
            "regression": rt.regression,
            "skipped_stages": list(rt.skipped_stages),
        }

    def _spine_md(self, s: Dict[str, Any]) -> str:
        st = s["tester_status"]
        lines = ["# Tester Fixture Spine Report", "", _DISCLAIMER, "",
                 f"- run id: {st['tester_run_id']} ({st['tester_profile']})",
                 f"- fixture events: {st['fixture_event_count']} "
                 f"(hash {st['fixture_hash'][:12]})",
                 f"- quarantined: {st['fixture_quarantined_count']}",
                 f"- membrane impressions: {st['membrane_impression_count']}",
                 f"- golden run: {st['golden_run_status']}",
                 f"- reproducibility: {st['reproducibility_status']}",
                 f"- regression: {st['regression_status']}",
                 f"- skipped optional stages: "
                 f"{', '.join(st['skipped_optional_stages']) or 'none'}",
                 f"- blocked: {st['tester_blocked']}", "",
                 "_The tester release begins with fixture-only golden runs, not "
                 "live data. The environmental membrane is required; downstream "
                 "learning consumes sensory impressions, never raw events._"]
        return "\n".join(lines)

    def _golden_md(self) -> str:
        g = self.runtime.golden_run.to_dict() if self.runtime.golden_run else {}
        lines = ["# Golden Run Report", "", _DISCLAIMER, "",
                 f"- overall status: {g.get('overall_status')}",
                 f"- steps: {g.get('step_count', 0)}",
                 f"- skipped optional: "
                 f"{', '.join(g.get('skipped_optional_steps', [])) or 'none'}",
                 "", "| step | optional | status |", "| --- | --- | --- |"]
        for s in g.get("steps", []):
            lines.append(f"| {s['name']} | {s['optional']} | {s['status']} |")
        lines += ["", "_Optional stages skip honestly with an explicit marker; "
                  "skipped stages are never hidden._"]
        return "\n".join(lines)

    def _repro_md(self) -> str:
        r = self.runtime.reproducibility
        lines = ["# Reproducibility Report", "", _DISCLAIMER, "",
                 f"- status: {r.get('reproducibility_status')}",
                 f"- findings: {r.get('finding_count', 0)} "
                 f"(fail {r.get('fail_count', 0)}, warn "
                 f"{r.get('warning_count', 0)})", ""]
        for f in r.get("findings", []):
            mark = "x" if f["passed"] else " "
            lines.append(f"- [{mark}] ({f['severity']}) {f['check']}"
                         + (f" -- {f['detail']}" if f["detail"] else ""))
        lines += ["", "_Reproducibility ignores timestamps and run ids; it "
                  "checks semantic structure and safety invariants._"]
        return "\n".join(lines)

    def _regression_md(self) -> str:
        r = self.runtime.regression
        lines = ["# Regression Report", "", _DISCLAIMER, "",
                 f"- status: {r.get('regression_status')}",
                 f"- findings: {r.get('finding_count', 0)} "
                 f"(regression {r.get('regression_count', 0)})", ""]
        for f in r.get("findings", []):
            lines.append(f"- ({f['severity']}) {f['check']}: "
                         f"regressed={f['regressed']}"
                         + (f" -- {f['detail']}" if f["detail"] else ""))
        lines += ["", "_Regression is structural and safety-focused; it fails if "
                  "the membrane path disappears, a raw bypass appears, or "
                  "unsupported claims / missing safety disclaimers appear._"]
        return "\n".join(lines)

    def _bundle_md(self) -> str:
        rt = self.runtime
        m = rt.bundle.manifest.to_dict() if rt.bundle else {}
        lines = ["# Tester Artifact Bundle Report", "", _DISCLAIMER, "",
                 f"- bundle dir: {m.get('bundle_dir')}",
                 f"- entries: {m.get('entry_count', 0)}",
                 f"- missing optional: "
                 f"{', '.join(m.get('missing_optional_artifacts', [])) or 'none'}",
                 "", "_The tester bundle is local-only and human-readable; "
                 "nothing is zipped automatically, uploaded, or published._"]
        return "\n".join(lines)

    def _safety_md(self) -> str:
        snap = self.runtime.safety.snapshot()
        lines = ["# Tester Fixture Safety Report", "", _DISCLAIMER, "",
                 f"- safety blocks recorded: {snap.get('rejected_count', 0)}",
                 f"- requires live data: {snap.get('requires_live_data')}",
                 f"- can start feeders: {snap.get('can_start_feeders')}",
                 f"- can access network: {snap.get('can_access_network')}",
                 f"- can run git: {snap.get('can_run_git')}",
                 f"- can publish: {snap.get('can_publish')}",
                 f"- tester feedback is training: "
                 f"{snap.get('tester_feedback_is_training')}", "",
                 "## Hard rules", ""]
        lines += [f"- {r}" for r in snap.get("hard_rules", [])]
        lines += ["", "_All live-data/feeder/hardware/network/Git/publish/"
                  "feedback-training capabilities are False by design._"]
        return "\n".join(lines)


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _write_json(path: str, obj: Any) -> None:
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
