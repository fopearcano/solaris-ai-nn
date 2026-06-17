"""Tester install guide builder -- local editable-install guide + quickstart.

:class:`TesterInstallGuideBuilder` writes the install guide, quickstart, and
troubleshooting docs for a trusted local install (``pip install -e .`` in a venv). The
guide states the safety rules: do not run live-read-only until the fixture demo passes,
do not put secrets/private data into event files, do not approve unknown feeder sources,
Solaris does not start feeders, external feeders are manual, and feedback is not
training.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class InstallStep:
    """One documented install/verify step."""

    title: str
    body: str

    def to_dict(self) -> Dict[str, Any]:
        return {"title": self.title, "body": self.body}


@dataclass
class InstallGuide:
    """The structured install guide."""

    steps: List[InstallStep] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"step_count": len(self.steps),
                "steps": [s.to_dict() for s in self.steps]}


_SAFETY_TEXT = (
    "## Safety\n\n"
    "- Do **not** run the live-read-only path until the fixture demo passes.\n"
    "- Do **not** put secrets, credentials, or private data into event files.\n"
    "- Do **not** approve feeder sources you do not understand.\n"
    "- Solaris does **not** start, stop, schedule, or control feeders.\n"
    "- External feeders are **manual** scripts you run yourself.\n"
    "- Tester feedback is **not** training, RLHF, ground truth, or a command.\n"
    "- Nothing here implies consciousness, sentience, biological life, "
    "personhood, agency, free will, emotion, feeling, understanding, "
    "self-awareness, autonomous self-improvement, or subjective experience.\n"
)


@dataclass
class TesterInstallGuideBuilder:
    """Builds the tester install guide, quickstart, and troubleshooting docs."""

    python_requirement: str = ">=3.11"

    def build(self) -> InstallGuide:
        return InstallGuide(steps=[
            InstallStep("Requirements", self._requirements()),
            InstallStep("Install", self._install()),
            InstallStep("Verify", self._verify()),
            InstallStep("Live-read-only (optional)", self._live()),
            InstallStep("Feedback", self._feedback())])

    def write(self, guides_dir: str) -> Dict[str, str]:
        os.makedirs(guides_dir, exist_ok=True)
        guide = self.build()
        install_path = os.path.join(guides_dir, "TESTER_INSTALL_GUIDE.md")
        quickstart_path = os.path.join(guides_dir, "TESTER_QUICKSTART.md")
        trouble_path = os.path.join(guides_dir, "TROUBLESHOOTING.md")
        _w(install_path, _guard(self._install_md(guide)))
        _w(quickstart_path, _guard(self._quickstart_md()))
        _w(trouble_path, _guard(self._troubleshooting_md()))
        return {"install_guide": install_path, "quickstart": quickstart_path,
                "troubleshooting": trouble_path}

    # -- sections -----------------------------------------------------------

    def _requirements(self) -> str:
        return (f"- Python {self.python_requirement}\n"
                "- Git is optional (you can download the repo instead)\n"
                "- A terminal and a local folder\n"
                "- No cloud account is required\n"
                "- No network is required after install, unless you manually "
                "install dependencies")

    def _install(self) -> str:
        return ("```bash\npython -m venv .venv\nsource .venv/bin/activate\n"
                "pip install -e .\n```\n\n"
                "Windows (PowerShell):\n\n"
                "```powershell\npython -m venv .venv\n"
                ".venv\\Scripts\\Activate.ps1\npip install -e .\n```")

    def _verify(self) -> str:
        return ("```bash\npython -m solaris_ai_nn doctor\n"
                "python -m solaris_ai_nn tester-demo --state-dir "
                ".solaris_ai_nn_tester --profile fixture_tester_v0\n"
                "python -m solaris_ai_nn tester-console --state-dir "
                ".solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester "
                "--console-dir .solaris_ai_nn_tester/console\n```")

    def _live(self) -> str:
        return ("Only after the fixture demo passes:\n\n"
                "```bash\npython -m solaris_ai_nn tester-live-init --state-dir "
                ".solaris_ai_nn_live --tester-state-dir "
                ".solaris_ai_nn_tester/live\n"
                "python -m solaris_ai_nn tester-live-doctor --state-dir "
                ".solaris_ai_nn_live --tester-state-dir "
                ".solaris_ai_nn_tester/live\n"
                "python -m solaris_ai_nn tester-live-samples --state-dir "
                ".solaris_ai_nn_live --tester-state-dir "
                ".solaris_ai_nn_tester/live\n```")

    def _feedback(self) -> str:
        return ("```bash\npython -m solaris_ai_nn tester-feedback-init "
                "--tester-state-dir .solaris_ai_nn_tester\n"
                "python -m solaris_ai_nn tester-feedback-report "
                "--tester-state-dir .solaris_ai_nn_tester\n```")

    # -- documents ----------------------------------------------------------

    def _install_md(self, guide: InstallGuide) -> str:
        lines = ["# Tester Install Guide", "",
                 "_A local, editable install for trusted testers. No cloud, no "
                 "global install, no publish/upload, no release/tag automation._",
                 ""]
        letters = "ABCDE"
        for i, step in enumerate(guide.steps):
            prefix = letters[i] if i < len(letters) else str(i)
            lines += [f"## {prefix}. {step.title}", "", step.body, ""]
        lines += [_SAFETY_TEXT]
        return "\n".join(lines)

    def _quickstart_md(self) -> str:
        return ("# Tester Quickstart\n\n"
                "```bash\npython -m venv .venv\nsource .venv/bin/activate\n"
                "pip install -e .\npython -m solaris_ai_nn doctor\n"
                "python -m solaris_ai_nn tester-demo --profile "
                "fixture_tester_v0\npython -m solaris_ai_nn tester-console "
                "--tester-state-dir .solaris_ai_nn_tester\n```\n\n"
                "Run the fixture demo before any live-read-only path. Solaris "
                "does not start feeders; external feeders are manual; feedback "
                "is not training.\n")

    def _troubleshooting_md(self) -> str:
        return ("# Troubleshooting\n\n"
                "- **`python -m solaris_ai_nn` not found** -- activate the venv "
                "and run `pip install -e .` again.\n"
                "- **`numpy` import error** -- `pip install -e .` installs the "
                "required `numpy`; ensure the venv is active.\n"
                "- **Windows: cannot activate the venv** -- run "
                "`Set-ExecutionPolicy -Scope Process RemoteSigned` in PowerShell, "
                "then activate again.\n"
                "- **`pytest` not found** -- it is optional; install with "
                "`pip install -e '.[test]'` only if you want to run the tests.\n"
                "- **Permission errors writing state** -- run from a folder you "
                "own; the tooling only writes under the chosen state dirs.\n"
                "- **Live commands blocked** -- governance ships disabled; edit "
                "it by hand to enable live-read-only testing, and run the fixture "
                "demo first.\n\n"
                "Nothing here installs global packages, accesses the network, or "
                "uploads anything.\n")


def _w(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _guard(text: str) -> str:
    try:
        from ..governance.compliance import ClaimGuard
        guard = ClaimGuard()
        if not guard.scan_text(text).safe:
            return guard.rewrite(text)
    except Exception:
        pass
    return text
