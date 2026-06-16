"""Diff audit -- assess a change set against the declared scope and prohibitions.

:class:`DiffAudit` works from the provided diff/patch/changed-file artifacts
(never running Git). It classifies each changed file (expected, unexpected,
forbidden path, safety-critical, generated, docs, test, example, source) and
scans the added patch lines for forbidden behavior (network/shell/browser/OS,
hardware/control imports, source-mutation, human-label-as-ground-truth,
unsupported claim text). An unexpected file change is a warning or blocker by
path/risk; forbidden behavior is always a blocker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class DiffSeverity:
    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"

    ALL = (INFO, WARNING, BLOCKER)


# Forbidden path fragments: touching these is a blocker.
_FORBIDDEN_PATHS = (".github/workflows", ".git/", "id_rsa", "secrets",
                    "credentials")
# Safety-critical path fragments: changes here are warnings (operator review).
_SAFETY_CRITICAL_PATHS = ("/safety.py", "governance/", "motor_membrane/",
                          "safety_invariant", "/compliance.py")
_GENERATED_PATHS = (".solaris_ai_nn_", "_REPORT.", "artifacts/")
_TEST_PATHS = ("tests/",)
_EXAMPLE_PATHS = ("examples/",)
_DOC_PATHS = ("docs/", "readme")
_SOURCE_PATHS = ("src/",)

# Forbidden code markers scanned in *added* patch lines.
_NETWORK_MARKERS = ("import socket", "import requests", "import urllib",
                    "urllib.request", "http://", "https://", "websocket",
                    "import http", "aiohttp")
_SHELL_MARKERS = ("import subprocess", "subprocess.", "os.system(", "os.popen(",
                  "pty.spawn", "exec(", "eval(")
_HARDWARE_MARKERS = ("import serial", "rpi.gpio", "import cv2", "import pyaudio",
                     "sounddevice", "import usb", "/dev/tty", "open_device")
_GIT_GITHUB_MARKERS = ("gh pr ", "github api", "git commit", "git push",
                       "git checkout", "octokit", "from github import")
_MUTATION_MARKERS = ('open(', )  # combined with write-mode + .py heuristic
_HUMAN_LABEL_MARKERS = ("ground_truth = human", "human_label_is_truth",
                        "label_as_ground_truth", "treat label as truth")
_CLAIM_MARKERS = ("is conscious", "is sentient", "is alive", "has free will",
                  "has agency", "subjective experience", "truly understands")


@dataclass
class ChangedFileAssessment:
    """How one changed file relates to the declared scope."""

    path: str
    category: str  # source | test | example | docs | report | safety_critical
    #                | forbidden | unexpected | expected
    expected: bool = False
    blocker: bool = False
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"path": self.path, "category": self.category,
                "expected": self.expected, "blocker": self.blocker,
                "note": self.note}


@dataclass
class DiffAuditFinding:
    """One diff-audit finding (with severity + evidence refs)."""

    dimension: str
    severity: str
    detail: str = ""
    paths: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"dimension": self.dimension, "severity": self.severity,
                "detail": self.detail, "paths": list(self.paths)}


@dataclass
class DiffAudit:
    """Audits a change set against declared scope and forbidden behavior."""

    assessments: List[ChangedFileAssessment] = field(default_factory=list)
    findings: List[DiffAuditFinding] = field(default_factory=list)

    def audit(self, *, changed_files: Optional[List[str]] = None,
              expected_files: Optional[List[str]] = None,
              required_files: Optional[List[str]] = None,
              patch_text: str = "") -> Dict[str, Any]:
        changed = [str(p).strip() for p in (changed_files or []) if p]
        expected = [str(p) for p in (expected_files or [])]
        required = [str(p) for p in (required_files or [])]

        self._assess_files(changed, expected)
        self._check_missing(changed, required)
        self._scan_patch(patch_text or "")
        return self.to_dict()

    @staticmethod
    def _is_expected(path: str, expected: List[str]) -> bool:
        low = path.lower()
        for e in expected:
            el = str(e).lower()
            # Expected entries may be free-text scope hints (e.g. "src/x/").
            if el and (el in low or low in el
                       or el.rstrip("/") in low):
                return True
        return False

    def _classify(self, path: str) -> str:
        low = path.lower()
        if any(f in low for f in _FORBIDDEN_PATHS):
            return "forbidden"
        if any(s in low for s in _SAFETY_CRITICAL_PATHS):
            return "safety_critical"
        if any(g in low for g in _GENERATED_PATHS):
            return "report"
        if any(t in low for t in _TEST_PATHS):
            return "test"
        if any(x in low for x in _EXAMPLE_PATHS):
            return "example"
        if any(d in low for d in _DOC_PATHS):
            return "docs"
        if any(s in low for s in _SOURCE_PATHS):
            return "source"
        return "unexpected"

    def _assess_files(self, changed: List[str], expected: List[str]) -> None:
        expected_hits, unexpected, forbidden, safety_crit = [], [], [], []
        docs, tests, examples = [], [], []
        for path in changed:
            category = self._classify(path)
            is_expected = self._is_expected(path, expected)
            blocker = category == "forbidden"
            note = ""
            if category == "forbidden":
                note = "forbidden path touched"
                forbidden.append(path)
            elif category == "safety_critical":
                note = "safety-critical file changed; operator review required"
                safety_crit.append(path)
            elif not is_expected and category in ("source", "unexpected"):
                note = "changed outside declared scope"
                unexpected.append(path)
            if category == "docs":
                docs.append(path)
            elif category == "test":
                tests.append(path)
            elif category == "example":
                examples.append(path)
            if is_expected:
                expected_hits.append(path)
            self.assessments.append(ChangedFileAssessment(
                path=path, category=category, expected=is_expected,
                blocker=blocker, note=note))

        if expected_hits:
            self._add("expected_files_changed", DiffSeverity.INFO,
                      f"{len(expected_hits)} expected file(s) changed",
                      expected_hits)
        if unexpected:
            self._add("source_files_modified_outside_declared_scope",
                      DiffSeverity.WARNING,
                      f"{len(unexpected)} file(s) changed outside declared "
                      "scope", unexpected)
        if forbidden:
            self._add("forbidden_paths_touched", DiffSeverity.BLOCKER,
                      f"{len(forbidden)} forbidden path(s) touched", forbidden)
        if safety_crit:
            self._add("safety_critical_files_changed", DiffSeverity.WARNING,
                      f"{len(safety_crit)} safety-critical file(s) changed",
                      safety_crit)
        if docs:
            self._add("docs_updated", DiffSeverity.INFO,
                      f"{len(docs)} doc file(s) updated", docs)
        if tests:
            self._add("tests_added", DiffSeverity.INFO,
                      f"{len(tests)} test file(s) added/changed", tests)
        if examples:
            self._add("examples_added", DiffSeverity.INFO,
                      f"{len(examples)} example file(s) added/changed", examples)

    def _check_missing(self, changed: List[str],
                       required: List[str]) -> None:
        missing = [r for r in required
                   if not any(str(r).lower().rstrip("/") in c.lower()
                              or c.lower() in str(r).lower()
                              for c in changed)]
        if missing:
            self._add("required_files_missing", DiffSeverity.WARNING,
                      f"{len(missing)} required file(s) not in the change set",
                      missing)

    def _scan_patch(self, patch_text: str) -> None:
        added = [ln[1:].lower() for ln in patch_text.splitlines()
                 if ln.startswith("+") and not ln.startswith("+++")]
        if not added and patch_text:
            # Not a unified diff; scan the whole text conservatively.
            added = [patch_text.lower()]
        blob = "\n".join(added)

        def hits(markers):
            return [m for m in markers if m in blob]

        for dimension, markers, sev in (
                ("network_shell_browser_os_calls_introduced",
                 _NETWORK_MARKERS + _SHELL_MARKERS, DiffSeverity.BLOCKER),
                ("hardware_control_imports_introduced", _HARDWARE_MARKERS,
                 DiffSeverity.BLOCKER),
                ("git_github_calls_introduced", _GIT_GITHUB_MARKERS,
                 DiffSeverity.BLOCKER),
                ("human_label_as_ground_truth_risk_introduced",
                 _HUMAN_LABEL_MARKERS, DiffSeverity.BLOCKER),
                ("unsupported_claim_text_introduced", _CLAIM_MARKERS,
                 DiffSeverity.BLOCKER)):
            found = hits(markers)
            if found:
                self._add(dimension, sev, f"markers: {found}", [])
        # Source-mutation heuristic: writing a .py file from added lines.
        if "open(" in blob and ('"w"' in blob or "'w'" in blob) and \
                (".py" in blob):
            self._add("source_mutation_behavior_introduced",
                      DiffSeverity.BLOCKER,
                      "added code writes a .py source file", [])
        # Runtime control-surface heuristic.
        if "argv" in blob and "subprocess" in blob:
            self._add("runtime_control_surfaces_added", DiffSeverity.WARNING,
                      "possible runtime control surface added", [])

    def _add(self, dimension: str, severity: str, detail: str,
             paths: List[str]) -> None:
        self.findings.append(DiffAuditFinding(dimension, severity, detail,
                                              list(paths)))

    @property
    def blocker_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == DiffSeverity.BLOCKER)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == DiffSeverity.WARNING)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "changed_file_count": len(self.assessments),
            "assessments": [a.to_dict() for a in self.assessments],
            "findings": [f.to_dict() for f in self.findings],
            "blocker_count": self.blocker_count,
            "warning_count": self.warning_count,
            "unexpected_file_change_count": sum(
                1 for a in self.assessments
                if a.note == "changed outside declared scope"),
            "forbidden_file_change_count": sum(
                1 for a in self.assessments if a.category == "forbidden"),
            "note": "audit works from provided diff/patch/changed-file "
                    "artifacts; no Git was run and no code was modified",
        }
