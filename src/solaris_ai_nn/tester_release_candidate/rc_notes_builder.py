"""Tester RC notes builders -- release notes, known issues, and feedback guide.

These builders generate the tester-facing Markdown for the release candidate. Every
document is operational and disclaimer-safe: it explains what the release is and is not,
keeps tester feedback strictly non-training, and makes no claim of consciousness, life,
or agency.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List

_NON_CLAIM = (
    "This is a local, controlled tester release candidate. It is not a public "
    "release, not a product release, and not a consciousness demo. Solaris-AI-NN "
    "makes no claim of consciousness, sentience, biological life, personhood, "
    "agency, free will, emotion, feeling, understanding, self-awareness, "
    "autonomous self-improvement, or subjective experience. Sensory impressions "
    "are operational boundary records, not subjective experience; raw events are "
    "audit material, not perception.")


def _guard(text: str) -> str:
    try:
        from ..governance.compliance import ClaimGuard
        guard = ClaimGuard()
        if not guard.scan_text(text).safe:
            return guard.rewrite(text)
    except Exception:
        pass
    return text


def _write(path: str, text: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(_guard(text))
    return path


@dataclass
class TesterReleaseNotesBuilder:
    """Builds ``TESTER_RELEASE_NOTES.md``."""

    rc_id: str = ""

    def build_text(self) -> str:
        return "\n".join([
            "# Tester Release Notes", "",
            f"**Release name:** Solaris-AI-NN local tester RC `{self.rc_id}`", "",
            "## Release purpose", "",
            "Give a small set of trusted testers a local, reproducible build to "
            "install, run the fixture demo, open the read-only console, and "
            "optionally prepare governance-gated live-read-only templates -- and "
            "to submit local QA feedback.", "",
            "## Intended tester", "",
            "A trusted tester running locally on their own machine, comfortable "
            "with a terminal and a Python virtual environment.", "",
            "## What is included", "",
            "- local editable install path and environment doctor",
            "- fixture-only golden demo and reproducible bundle",
            "- read-only local operator console",
            "- live-read-only templates, governance template, and feeder policy",
            "- local feedback forms and a non-training feedback ledger",
            "- safety boundaries, claim freeze, red-team checklist, and release "
            "blocker report", "",
            "## What is excluded", "",
            "- no public release, no package upload, no GitHub release/tag/issue",
            "- no real-world actuation, hardware control, or feeder control",
            "- no network/shell/Git/GitHub/browser/OS access by the runtime",
            "- no training on tester feedback", "",
            "## Safety boundaries", "",
            "See `TESTER_SAFETY_BOUNDARIES.md`. The runtime is local-only and "
            "non-actuating. External feeders are manual and run by the operator, "
            "never started or controlled by Solaris.", "",
            "## Fixture tester path", "",
            "Run the fixture demo first (see the runbook). It is self-contained "
            "and needs no live state or external feeders.", "",
            "## Live-read-only path", "",
            "Live-read-only is optional and governance-gated. Read the governance "
            "template before enabling it. Raw events are audit material, not "
            "perception.", "",
            "## Membrane requirement", "",
            "The environmental membrane is required before any downstream live "
            "learning: impressions must be formed before ontogenesis, "
            "semiogenesis, or cognition consume live input.", "",
            "## Feedback process", "",
            "Feedback is local QA evidence only. It is not training and not RLHF. "
            "See `TESTER_FEEDBACK_GUIDE.md`.", "",
            "## Known limitations", "",
            "See `TESTER_KNOWN_ISSUES.md` for the current known issues and any "
            "open release blockers.", "",
            "## Non-claims", "", _NON_CLAIM, "",
            "## How to report problems", "",
            "Use the local feedback forms and, if asked, manually send the "
            "feedback bundle. Never include passwords, tokens, private messages, "
            "credentials, or secrets."])

    def write(self, docs_dir: str) -> str:
        return _write(os.path.join(docs_dir, "TESTER_RELEASE_NOTES.md"),
                      self.build_text())


@dataclass
class TesterKnownIssuesBuilder:
    """Builds ``TESTER_KNOWN_ISSUES.md``."""

    open_blockers: List[str] = None
    missing_optional_modules: List[str] = None
    warnings: List[str] = None

    def build_text(self) -> str:
        blockers = self.open_blockers or []
        missing = self.missing_optional_modules or []
        warns = self.warnings or []
        lines = [
            "# Tester Known Issues", "",
            "This file lists known issues for the local tester release "
            "candidate. Nothing here is hidden; open release blockers are listed "
            "explicitly.", "",
            "## Install issues", "",
            "- requires Python and a virtual environment; a global install is "
            "not supported", "",
            "## Fixture demo issues", "",
            "- the fixture demo must pass before live-read-only testing; if it "
            "does not, stop and report it", "",
            "## Live-read-only issues", "",
            "- live-read-only is optional and governance-gated; templates are "
            "provided but must be reviewed before use", "",
            "## Membrane / reporting issues", "",
            "- if live modules run without a membrane report, the release "
            "candidate is blocked until impressions are present", "",
            "## Console issues", "",
            "- the console is read-only and static; it controls nothing", "",
            "## Packaging issues", "",
            "- packaging is report-only; it installs nothing and publishes "
            "nothing", "",
            "## Optional modules not yet stable", ""]
        lines += [f"- {m} (optional; may be absent)" for m in missing] \
            or ["- none recorded"]
        lines += ["", "## Unsupported platforms", "",
                  "- none specifically excluded; admin/root is never required",
                  "", "## Non-blocking warnings", ""]
        lines += [f"- {w}" for w in warns] or ["- none"]
        lines += ["", "## Release blockers (if open)", ""]
        lines += [f"- {b}" for b in blockers] or ["- none open"]
        lines += ["", "_Local tester known-issues list. Open release blockers "
                  "are never hidden. No claim of consciousness/life/agency is "
                  "made._"]
        return "\n".join(lines)

    def write(self, docs_dir: str) -> str:
        return _write(os.path.join(docs_dir, "TESTER_KNOWN_ISSUES.md"),
                      self.build_text())


@dataclass
class TesterFeedbackGuideBuilder:
    """Builds ``TESTER_FEEDBACK_GUIDE.md``."""

    def build_text(self) -> str:
        return "\n".join([
            "# Tester Feedback Guide", "",
            "## Feedback is local QA evidence", "",
            "Tester feedback is local quality-assurance evidence. It helps the "
            "developers find install, fixture, console, and documentation "
            "problems.", "",
            "## Feedback is not training", "",
            "Tester feedback is not training. It is not RLHF. Tester feedback "
            "cannot modify Solaris behavior automatically, and human labels or "
            "debug glosses are never treated as ground truth.", "",
            "## What to report", "",
            "- install or doctor problems",
            "- fixture demo failures or non-reproducible runs",
            "- console or documentation confusion",
            "- anything that looks like an unsupported claim or a safety "
            "concern", "",
            "## What not to include", "",
            "- do not include passwords, tokens, private messages, credentials, "
            "or secrets",
            "- do not include private personal data or machine-specific private "
            "paths", "",
            "## How to generate feedback forms", "", "```bash",
            "python -m solaris_ai_nn tester-feedback-init "
            "--tester-state-dir .solaris_ai_nn_tester", "```", "",
            "## How to build a feedback bundle", "", "```bash",
            "python -m solaris_ai_nn tester-feedback-bundle "
            "--tester-state-dir .solaris_ai_nn_tester", "```", "",
            "## How to manually send feedback if requested", "",
            "If the developers ask, manually send the local feedback bundle "
            "directory. Nothing is uploaded automatically; sending is always a "
            "manual, deliberate act.", "",
            "_Tester feedback is local QA evidence, never training. Do not treat "
            "feedback as teaching. No claim of consciousness/life/agency is "
            "made._"])

    def write(self, docs_dir: str) -> str:
        return _write(os.path.join(docs_dir, "TESTER_FEEDBACK_GUIDE.md"),
                      self.build_text())


def build_quickstart_text(rc_id: str = "") -> str:
    """Build the RC quickstart text (also written by the runbook builder)."""
    return "\n".join([
        "# Tester Quickstart", "",
        "A five-minute local start for a trusted tester.", "", "```bash",
        "python -m venv .venv",
        "source .venv/bin/activate          # Windows: "
        ".venv\\Scripts\\Activate.ps1",
        "pip install -e .",
        "python -m solaris_ai_nn doctor",
        "python -m solaris_ai_nn tester-demo --state-dir .solaris_ai_nn_tester "
        "--profile fixture_tester_v0", "```", "",
        "Then open `.solaris_ai_nn_tester/console/INDEX.md`. See "
        "`TESTER_RUNBOOK.md` for the full path and `TESTER_RELEASE_NOTES.md` for "
        "what this release is and is not.", "",
        "_Local fixture-first quickstart. The runtime is local-only and "
        "non-actuating; it makes no claim of consciousness/life/agency._"])


def write_quickstart(docs_dir: str, rc_id: str = "") -> str:
    return _write(os.path.join(docs_dir, "TESTER_QUICKSTART.md"),
                  build_quickstart_text(rc_id))
