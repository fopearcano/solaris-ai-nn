"""Tester capability freeze -- scan artifacts for active-control implications.

:class:`TesterCapabilityFreeze` scans configuration/docs/reports/templates for capability
claims or permissions that would imply active control: feeder/hardware control, network/
shell/browser/OS access, Git/GitHub, release/tag/issue creation, upload/publish,
background services, camera/mic/clipboard/screen capture, private-message/credential
ingestion, filesystem-wide scan, raw-event downstream bypass, membrane bypass, or
feedback-as-training. Any active-control implication blocks the tester release. It
executes nothing and does not inspect sensitive payloads by default.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

_MAX_BYTES = 1_000_000


class CapabilityCategory:
    FEEDER_CONTROL = "feeder_control"
    HARDWARE_CONTROL = "hardware_control"
    NETWORK_ACCESS = "network_access"
    SHELL_EXECUTION = "shell_execution"
    BROWSER_CONTROL = "browser_control"
    OS_CONTROL = "os_control"
    GIT_GITHUB = "git_github_access"
    RELEASE_TAG = "release_tag_creation"
    ISSUE_CREATION = "issue_creation"
    UPLOAD_PUBLISH = "upload_publish"
    BACKGROUND_SERVICE = "background_service"
    CAMERA_MIC = "camera_microphone"
    CLIPBOARD_SCREEN = "clipboard_screen_capture"
    PRIVATE_MESSAGE = "private_message_ingestion"
    CREDENTIAL = "credential_secret_access"
    FILESYSTEM_SCAN = "filesystem_wide_scan"
    RAW_EVENT_BYPASS = "raw_event_downstream_bypass"
    MEMBRANE_BYPASS = "membrane_bypass"
    FEEDBACK_TRAINING = "feedback_as_training"
    UNKNOWN = "unknown"


# Disclaimer markers near a match neutralise it (e.g. "Solaris does NOT start
# feeders"). Matching is on markdown-stripped text within a character window.
_NEGATORS = ("not", "no ", "never", "nothing", "none", "does not", "doesn't",
             "do not", "don't", "cannot", "can't", "is not", "are not",
             "isn't", "aren't", "won't", "will not", "without", "must not",
             "should not", "no feeder", "non-actuating", "non actuating",
             "read-only", "read only", "false", "no hardware", "no network",
             "no shell", "no git", "no upload", "no publish", "no browser",
             "remains local", "local-only", "local only", "manual",
             "externally", "not control", "never start", "blocked",
             "no feeder/hardware", "must remain", "forbidden", "prohibited",
             "deny", "denied", "refuses", "refuse", "would require",
             "require explicit", "requires explicit", "require human approval")


def _strip_markdown(text: str) -> str:
    return text.replace("*", "").replace("`", "").replace("_", "")

# (regex, category) -- active-control implications.
_PATTERNS: Tuple[Tuple[str, str], ...] = (
    (r"\b(start|stop|schedule|control|launch|restart)\s+(the\s+)?feeders?\b",
     CapabilityCategory.FEEDER_CONTROL),
    (r"\bsolaris_may_(start|stop|control|schedule|modify)_feeders?\s*[:=]\s*true",
     CapabilityCategory.FEEDER_CONTROL),
    (r"\bcontrols?\s+(physical\s+)?hardware\b|\breal[-\s]world\s+actuation\b|"
     r"\bactuates?\s+(a|an|the|real)\b", CapabilityCategory.HARDWARE_CONTROL),
    (r"\b(opens?|uses?|calls?|accesses?)\s+(the\s+)?network\b|\brequests\.(get|post)",
     CapabilityCategory.NETWORK_ACCESS),
    (r"\b(runs?|executes?)\s+(a\s+)?shell\b|\bsubprocess\.|os\.system\(",
     CapabilityCategory.SHELL_EXECUTION),
    (r"\b(opens?|launch(es)?)\s+(a\s+)?browser\b|webbrowser\.open",
     CapabilityCategory.BROWSER_CONTROL),
    (r"\b(git\s+push|git\s+commit|github\s+api|create\s+(a\s+)?release|"
     r"create\s+(a\s+)?tag)\b", CapabilityCategory.GIT_GITHUB),
    (r"\bcreate\s+(a\s+)?github\s+issue\b|\bopens?\s+(an\s+)?issue\b",
     CapabilityCategory.ISSUE_CREATION),
    (r"\b(uploads?|publish(es)?)\s+(the\s+)?(report|artifact|package|bundle)",
     CapabilityCategory.UPLOAD_PUBLISH),
    (r"\b(starts?|runs?)\s+(a\s+)?(background\s+service|daemon|web\s+server)\b",
     CapabilityCategory.BACKGROUND_SERVICE),
    (r"\b(reads?|captures?)\s+(the\s+)?(camera|microphone)\b",
     CapabilityCategory.CAMERA_MIC),
    (r"\b(reads?|captures?)\s+(the\s+)?(clipboard|screen)\b",
     CapabilityCategory.CLIPBOARD_SCREEN),
    (r"\b(reads?|ingests?)\s+private\s+messages?\b",
     CapabilityCategory.PRIVATE_MESSAGE),
    (r"\b(reads?|accesses?)\s+(credentials?|passwords?|api\s*keys?|secrets?)\b",
     CapabilityCategory.CREDENTIAL),
    (r"\bfilesystem[-\s]wide\s+scan\b|\bscans?\s+the\s+whole\s+(disk|filesystem)\b",
     CapabilityCategory.FILESYSTEM_SCAN),
    (r"\braw\s+events?\s+(flow|go|pass)\s+(directly\s+)?into\s+"
     r"(ontogenesis|semiogenesis|cognition)\b",
     CapabilityCategory.RAW_EVENT_BYPASS),
    (r"\b(skip|bypass)\s+the\s+membrane\b",
     CapabilityCategory.MEMBRANE_BYPASS),
    (r"\b(trains?\s+on|learns?\s+from)\s+(tester\s+)?feedback\b|"
     r"tester_feedback_is_training\s*[:=]\s*true",
     CapabilityCategory.FEEDBACK_TRAINING),
)


@dataclass
class CapabilityFinding:
    """One capability-scan finding (an active-control implication)."""

    path: str
    line: int
    category: str
    matched_text: str
    blocking: bool = True  # active-control implications block the tester release

    def to_dict(self) -> Dict[str, Any]:
        return {"path": self.path, "line": self.line, "category": self.category,
                "matched_text": self.matched_text, "blocking": self.blocking}


@dataclass
class CapabilityFreezeResult:
    """The aggregate capability-freeze result."""

    findings: List[CapabilityFinding] = field(default_factory=list)
    scanned_files: int = 0

    @property
    def blocker_count(self) -> int:
        return sum(1 for f in self.findings if f.blocking)

    @property
    def passed(self) -> bool:
        return not any(f.blocking for f in self.findings)

    def to_dict(self) -> Dict[str, Any]:
        cats: Dict[str, int] = {}
        for f in self.findings:
            cats[f.category] = cats.get(f.category, 0) + 1
        return {
            "passed": self.passed, "scanned_files": self.scanned_files,
            "blocker_count": self.blocker_count, "by_category": cats,
            "findings": [f.to_dict() for f in self.findings],
            "executes_anything": False,
            "note": "any active-control implication (feeder/hardware/network/"
                    "shell/publish/raw-bypass/membrane-bypass/feedback-training) "
                    "blocks the tester release",
        }


@dataclass
class TesterCapabilityFreeze:
    """Scans artifacts for active-control capability implications."""

    _compiled = None

    def _patterns(self):
        if self._compiled is None:
            self._compiled = [(re.compile(rx, re.IGNORECASE), cat)
                              for rx, cat in _PATTERNS]
        return self._compiled

    def scan_paths(self, paths: List[str]) -> CapabilityFreezeResult:
        result = CapabilityFreezeResult()
        for path in paths:
            text = _read(path)
            if text is None:
                continue
            result.scanned_files += 1
            self._scan_one(path, text, result)
        return result

    def _scan_one(self, path: str, text: str,
                  result: CapabilityFreezeResult) -> None:
        from .claim_freeze import _is_research_doc
        research = _is_research_doc(path)
        text = _strip_markdown(text)
        for rx, cat in self._patterns():
            for m in rx.finditer(text):
                if self._negated(text, m.start(), m.end()):
                    continue
                line = text.count("\n", 0, m.start()) + 1
                result.findings.append(CapabilityFinding(
                    path=path, line=line, category=cat,
                    matched_text=text[m.start():m.end()].strip(),
                    blocking=not research))

    @staticmethod
    def _negated(text: str, start: int, end: int) -> bool:
        # Docs assert these capabilities only to deny them ("Solaris does not
        # start feeders", "no network access"). Inspect the enclosing sentence/
        # paragraph (single newlines are markdown soft-wraps, not boundaries).
        from .forbidden_claims import _enclosing_sentence
        clause = _enclosing_sentence(text, start, end).lower()
        return any(n in clause for n in _NEGATORS)


def _read(path: str):
    try:
        if not os.path.isfile(path) or os.path.getsize(path) > _MAX_BYTES:
            return None
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except Exception:
        return None
