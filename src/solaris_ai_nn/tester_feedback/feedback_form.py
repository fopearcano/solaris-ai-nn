"""Tester feedback form -- the local, non-training feedback schema + templates.

:class:`TesterFeedbackForm` defines the feedback categories, severities, and required
fields and renders the local Markdown/JSON form templates. :class:`FeedbackSubmission`
normalizes an ingested feedback dict. The form clearly states that feedback is not
training and that secrets/private data must not be included; artifact references are
local paths only.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class FeedbackCategory:
    INSTALLATION_FAILURE = "installation_failure"
    DEPENDENCY_PROBLEM = "dependency_problem"
    CLI_FAILURE = "cli_failure"
    FIXTURE_DEMO_FAILURE = "fixture_demo_failure"
    FIXTURE_REPRODUCIBILITY_PROBLEM = "fixture_reproducibility_problem"
    FIXTURE_REGRESSION_PROBLEM = "fixture_regression_problem"
    LIVE_INIT_PROBLEM = "live_init_problem"
    LIVE_DOCTOR_PROBLEM = "live_doctor_problem"
    GOVERNANCE_CONFUSION = "governance_confusion"
    FEEDER_REGISTRY_CONFUSION = "feeder_registry_confusion"
    EXTERNAL_FEEDER_PROBLEM = "external_feeder_problem"
    SAFE_EVENT_PACK_PROBLEM = "safe_event_pack_problem"
    LIVE_BIRTH_PROBLEM = "live_birth_problem"
    QUARANTINE_CONFUSION = "quarantine_confusion"
    MEMBRANE_CONFUSION = "membrane_confusion"
    MEMBRANE_BYPASS_CONCERN = "membrane_bypass_concern"
    OBSERVATION_PROBLEM = "observation_problem"
    CONSOLE_READABILITY_PROBLEM = "console_readability_problem"
    ARTIFACT_MISSING = "artifact_missing"
    ARTIFACT_UNEXPECTED = "artifact_unexpected"
    SAFETY_CONCERN = "safety_concern"
    UNSUPPORTED_CLAIM_CONCERN = "unsupported_claim_concern"
    PRIVACY_CONCERN = "privacy_concern"
    PERFORMANCE_PROBLEM = "performance_problem"
    DOCUMENTATION_CONFUSION = "documentation_confusion"
    TESTER_SUGGESTION = "tester_suggestion"
    OTHER = "other"

    ALL = (INSTALLATION_FAILURE, DEPENDENCY_PROBLEM, CLI_FAILURE,
           FIXTURE_DEMO_FAILURE, FIXTURE_REPRODUCIBILITY_PROBLEM,
           FIXTURE_REGRESSION_PROBLEM, LIVE_INIT_PROBLEM, LIVE_DOCTOR_PROBLEM,
           GOVERNANCE_CONFUSION, FEEDER_REGISTRY_CONFUSION,
           EXTERNAL_FEEDER_PROBLEM, SAFE_EVENT_PACK_PROBLEM, LIVE_BIRTH_PROBLEM,
           QUARANTINE_CONFUSION, MEMBRANE_CONFUSION, MEMBRANE_BYPASS_CONCERN,
           OBSERVATION_PROBLEM, CONSOLE_READABILITY_PROBLEM, ARTIFACT_MISSING,
           ARTIFACT_UNEXPECTED, SAFETY_CONCERN, UNSUPPORTED_CLAIM_CONCERN,
           PRIVACY_CONCERN, PERFORMANCE_PROBLEM, DOCUMENTATION_CONFUSION,
           TESTER_SUGGESTION, OTHER)


class FeedbackSeverity:
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"
    RELEASE_BLOCKER = "release_blocker"
    UNKNOWN = "unknown"

    ALL = (INFO, MINOR, MAJOR, CRITICAL, RELEASE_BLOCKER, UNKNOWN)
    _RANK = {INFO: 0, MINOR: 1, MAJOR: 2, CRITICAL: 3, RELEASE_BLOCKER: 4,
             UNKNOWN: 1}


@dataclass
class FeedbackQuestion:
    """One field in the feedback form."""

    key: str
    prompt: str
    required: bool = False
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"key": self.key, "prompt": self.prompt,
                "required": self.required, "note": self.note}


_REQUIRED_FIELDS = (
    ("feedback_id", "A unique feedback id (auto-filled if omitted)", False),
    ("created_utc", "Creation timestamp (auto-filled if omitted)", False),
    ("tester_alias", "Tester alias or 'anonymous'", True),
    ("version_or_commit", "Solaris-AI-NN version/commit if known", False),
    ("os", "Operating system if known", False),
    ("python_version", "Python version if known", False),
    ("command_run", "The command you ran, if applicable", False),
    ("profile_used", "The profile used, if applicable", False),
    ("stage_affected", "Which stage was affected", False),
    ("category", f"Category (one of: {', '.join(FeedbackCategory.ALL[:6])}, "
                 "...)", True),
    ("severity", f"Severity (one of: {', '.join(FeedbackSeverity.ALL)})", True),
    ("expected_behavior", "What you expected to happen", True),
    ("actual_behavior", "What actually happened", True),
    ("reproduction_steps", "Steps to reproduce (list)", False),
    ("artifact_paths", "Local artifact paths only (no contents)", False),
    ("manual_notes", "Optional notes / local screenshot paths only", False),
    ("privacy_warning_acknowledged",
     "Set true to confirm no secrets/private data are included", True),
    ("non_training_acknowledgement",
     "Set true to confirm you understand feedback is NOT training", True),
)

_PRIVACY_NOTICE = (
    "Do NOT include secrets, passwords, API keys, tokens, credentials, private "
    "messages, or raw private payloads. Artifact references must be local paths "
    "only (the form never collects file contents)."
)

_NON_TRAINING_NOTICE = (
    "This feedback is LOCAL QA evidence only. It is NOT training data, NOT RLHF, "
    "NOT ground truth, and NOT a command. It does NOT modify Solaris behaviour, "
    "create remote issues, or upload anything. It is reviewed by the developer."
)


@dataclass
class TesterFeedbackForm:
    """The local tester feedback form (categories + required fields)."""

    questions: List[FeedbackQuestion] = field(default_factory=list)

    @classmethod
    def build(cls) -> "TesterFeedbackForm":
        return cls(questions=[FeedbackQuestion(k, p, r)
                              for (k, p, r) in _REQUIRED_FIELDS])

    def required_keys(self) -> List[str]:
        return [q.key for q in self.questions if q.required]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "form_id": "tester_feedback_form_v0",
            "categories": list(FeedbackCategory.ALL),
            "severities": list(FeedbackSeverity.ALL),
            "questions": [q.to_dict() for q in self.questions],
            "privacy_notice": _PRIVACY_NOTICE,
            "non_training_notice": _NON_TRAINING_NOTICE,
            "feedback_is_training": False,
            "feedback_is_ground_truth": False,
        }

    def to_markdown(self) -> str:
        lines = ["# Tester Feedback Form", "",
                 f"> {_NON_TRAINING_NOTICE}", "",
                 f"> **Privacy:** {_PRIVACY_NOTICE}", "",
                 "## Categories", "",
                 ", ".join(f"`{c}`" for c in FeedbackCategory.ALL), "",
                 "## Severities", "",
                 ", ".join(f"`{s}`" for s in FeedbackSeverity.ALL), "",
                 "## Fields", ""]
        for q in self.questions:
            req = " (required)" if q.required else ""
            lines.append(f"- **{q.key}**{req}: {q.prompt}")
        lines += ["", "## Fixture-specific prompts", "",
                  "- fixture command run", "- fixture demo result",
                  "- golden manifest problem", "- reproducibility issue",
                  "- regression issue", "- missing artifact",
                  "- confusing report", "- unexpected report", "",
                  "## Live-read-only prompts", "",
                  "- governance confusion", "- feeder registry confusion",
                  "- external feeder issue", "- safe/unsafe event pack issue",
                  "- live birth problem", "- membrane problem",
                  "- membrane bypass concern", "- observation problem",
                  "- quarantine concern", "- source pressure/diet confusion", ""]
        return "\n".join(lines)


@dataclass
class FeedbackSubmission:
    """A normalized, validated feedback submission."""

    feedback_id: str
    category: str = FeedbackCategory.OTHER
    severity: str = FeedbackSeverity.UNKNOWN
    tester_alias: str = "anonymous"
    created_utc: str = ""
    stage_affected: str = ""
    command_run: str = ""
    profile_used: str = ""
    expected_behavior: str = ""
    actual_behavior: str = ""
    reproduction_steps: List[str] = field(default_factory=list)
    artifact_paths: List[str] = field(default_factory=list)
    manual_notes: str = ""
    version_or_commit: str = ""
    os: str = ""
    python_version: str = ""
    privacy_warning_acknowledged: bool = False
    non_training_acknowledgement: bool = False
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeedbackSubmission":
        steps = data.get("reproduction_steps", [])
        if isinstance(steps, str):
            steps = [s.strip() for s in steps.splitlines() if s.strip()]
        paths = data.get("artifact_paths", [])
        if isinstance(paths, str):
            paths = [paths] if paths else []
        fid = str(data.get("feedback_id")
                  or f"fb_{int(time.time() * 1000)}")
        category = str(data.get("category", FeedbackCategory.OTHER))
        if category not in FeedbackCategory.ALL:
            category = FeedbackCategory.OTHER
        severity = str(data.get("severity", FeedbackSeverity.UNKNOWN))
        if severity not in FeedbackSeverity.ALL:
            severity = FeedbackSeverity.UNKNOWN
        return cls(
            feedback_id=fid, category=category, severity=severity,
            tester_alias=str(data.get("tester_alias", "anonymous")),
            created_utc=str(data.get("created_utc")
                            or time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                             time.gmtime())),
            stage_affected=str(data.get("stage_affected", "")),
            command_run=str(data.get("command_run", "")),
            profile_used=str(data.get("profile_used", "")),
            expected_behavior=str(data.get("expected_behavior", "")),
            actual_behavior=str(data.get("actual_behavior", "")),
            reproduction_steps=list(steps),
            artifact_paths=[str(p) for p in paths],
            manual_notes=str(data.get("manual_notes", "")),
            version_or_commit=str(data.get("version_or_commit", "")),
            os=str(data.get("os", "")),
            python_version=str(data.get("python_version", "")),
            privacy_warning_acknowledged=bool(
                data.get("privacy_warning_acknowledged", False)),
            non_training_acknowledgement=bool(
                data.get("non_training_acknowledgement", False)),
            raw=dict(data))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_id": self.feedback_id, "category": self.category,
            "severity": self.severity, "tester_alias": self.tester_alias,
            "created_utc": self.created_utc,
            "stage_affected": self.stage_affected,
            "command_run": self.command_run, "profile_used": self.profile_used,
            "expected_behavior": self.expected_behavior,
            "actual_behavior": self.actual_behavior,
            "reproduction_steps": list(self.reproduction_steps),
            "artifact_paths": list(self.artifact_paths),
            "manual_notes": self.manual_notes,
            "version_or_commit": self.version_or_commit, "os": self.os,
            "python_version": self.python_version,
            "privacy_warning_acknowledged": self.privacy_warning_acknowledged,
            "non_training_acknowledgement": self.non_training_acknowledgement,
            "feedback_is_training": False, "feedback_is_command": False,
        }
