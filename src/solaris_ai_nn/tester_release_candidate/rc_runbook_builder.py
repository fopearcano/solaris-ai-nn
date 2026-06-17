"""Tester RC runbook builder -- the ordered, fixture-first tester runbook.

:class:`TesterRunbookBuilder` generates ``TESTER_RUNBOOK.md``: an ordered set of sections
(install, fixture, console, live-read-only init, optional live run, feedback, stop
conditions). The runbook is fixture-first: it never tells a tester to run external
feeders before the fixture path passes, never enables live-read-only without reading
governance, and never includes commands that upload/publish/create releases or start
feeders from Solaris.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class RunbookStep:
    text: str
    command: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "command": self.command}


@dataclass
class RunbookSection:
    key: str
    title: str
    steps: List[RunbookStep] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [f"## {self.title}", ""]
        cmds = [s.command for s in self.steps if s.command]
        prose = [s.text for s in self.steps if s.text and not s.command]
        for p in prose:
            lines.append(f"- {p}")
        if prose and cmds:
            lines.append("")
        if cmds:
            lines.append("```bash")
            lines += cmds
            lines.append("```")
        for n in self.notes:
            lines += ["", f"> {n}"]
        return "\n".join(lines)


def _default_sections() -> List[RunbookSection]:
    S = RunbookSection
    P = RunbookStep
    return [
        S("install", "A. Install", [
            P("", "python -m venv .venv"),
            P("", "pip install -e ."),
            P("", "python -m solaris_ai_nn doctor")],
          notes=["Use a virtual environment. A global install is not "
                 "supported and admin/root is never required."]),
        S("fixture", "B. Fixture run (do this first)", [
            P("", "python -m solaris_ai_nn tester-demo "
                  "--state-dir .solaris_ai_nn_tester "
                  "--profile fixture_tester_v0"),
            P("", "python -m solaris_ai_nn tester-console "
                  "--state-dir .solaris_ai_nn_live "
                  "--tester-state-dir .solaris_ai_nn_tester "
                  "--console-dir .solaris_ai_nn_tester/console")],
          notes=["The fixture demo is self-contained. Do not run external "
                 "feeders before the fixture path passes."]),
        S("console", "C. Inspect console", [
            P("open `.solaris_ai_nn_tester/console/INDEX.md`"),
            P("optionally open `.solaris_ai_nn_tester/console/INDEX.html` "
              "manually in a browser you open yourself")],
          notes=["The console is read-only. It controls no feeders, hardware, "
                 "or network."]),
        S("live_init", "D. Live-read-only init (optional, governance-gated)", [
            P("", "python -m solaris_ai_nn tester-live-init "
                  "--state-dir .solaris_ai_nn_live "
                  "--tester-state-dir .solaris_ai_nn_tester/live"),
            P("", "python -m solaris_ai_nn tester-live-doctor "
                  "--state-dir .solaris_ai_nn_live "
                  "--tester-state-dir .solaris_ai_nn_tester/live"),
            P("", "python -m solaris_ai_nn tester-live-samples "
                  "--state-dir .solaris_ai_nn_live "
                  "--tester-state-dir .solaris_ai_nn_tester/live")],
          notes=["Read the governance template before enabling live-read-only. "
                 "External feeders are manual and run by you, never started by "
                 "Solaris."]),
        S("live_run", "E. Optional live-read-only run", [
            P("", "python -m solaris_ai_nn tester-live-run "
                  "--state-dir .solaris_ai_nn_live "
                  "--tester-state-dir .solaris_ai_nn_tester/live "
                  "--run-birth --run-membrane --run-integration "
                  "--run-observation --max-events 500")],
          notes=["Only after the fixture path passes and governance is read. "
                 "The membrane forms impressions before any downstream live "
                 "learning; raw events are audit material, not perception."]),
        S("feedback", "F. Feedback", [
            P("", "python -m solaris_ai_nn tester-feedback-init "
                  "--tester-state-dir .solaris_ai_nn_tester"),
            P("", "python -m solaris_ai_nn tester-feedback-report "
                  "--tester-state-dir .solaris_ai_nn_tester"),
            P("", "python -m solaris_ai_nn tester-feedback-bundle "
                  "--tester-state-dir .solaris_ai_nn_tester")],
          notes=["Feedback is local QA evidence, never training. Do not include "
                 "passwords, tokens, private messages, credentials, or secrets."]),
        S("stop", "G. Stop conditions", [
            P("doctor is blocked"),
            P("the fixture demo fails"),
            P("the safety freeze reports a blocker"),
            P("governance is unclear"),
            P("a forbidden source appears"),
            P("the feeder registry looks unsafe"),
            P("the membrane is missing when live modules ran"),
            P("a raw-event bypass is detected"),
            P("an unsupported claim appears"),
            P("private data or a secret appears"),
            P("you are unsure what a command does")],
          notes=["If any stop condition occurs, stop and report it via local "
                 "feedback. Do not work around a safety blocker."])]


@dataclass
class TesterRunbookBuilder:
    """Builds the ordered tester runbook."""

    sections: List[RunbookSection] = field(default_factory=_default_sections)

    def build_text(self) -> str:
        lines = ["# Tester Runbook", "",
                 "An ordered, fixture-first runbook for the local tester "
                 "release candidate. Follow the sections in order; the fixture "
                 "path comes first and live-read-only is optional and "
                 "governance-gated.", ""]
        for sec in self.sections:
            lines.append(sec.to_markdown())
            lines.append("")
        lines += ["_Local fixture-first runbook. Every command is local and "
                  "read-only with respect to feeders; nothing is sent anywhere "
                  "and no release/tag/issue is created. The runtime is "
                  "local-only and non-actuating and makes no claim of "
                  "consciousness/life/agency._"]
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {"sections": [{"key": s.key, "title": s.title,
                              "steps": [st.to_dict() for st in s.steps],
                              "notes": list(s.notes)} for s in self.sections],
                "fixture_first": True, "local_only": True, "publishes": False}

    def write(self, docs_dir: str) -> str:
        os.makedirs(docs_dir, exist_ok=True)
        path = os.path.join(docs_dir, "TESTER_RUNBOOK.md")
        text = self.build_text()
        try:
            from ..governance.compliance import ClaimGuard
            guard = ClaimGuard()
            if not guard.scan_text(text).safe:
                text = guard.rewrite(text)
        except Exception:
            pass
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path
