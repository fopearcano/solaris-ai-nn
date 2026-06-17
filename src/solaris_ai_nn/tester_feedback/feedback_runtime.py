"""Tester feedback runtime -- bounded, local-only QA-ledger intake.

:class:`TesterFeedbackRuntime` generates the local feedback forms, ingests local
feedback JSON (bugs, safety concerns, confusion, suggestions, general), validates and
redacts it, classifies release blockers, appends to the append-only ledger, and builds
the feedback reports/bundle. It writes only feedback artifacts; it never modifies
Solaris behaviour, trains on feedback, creates remote issues, uploads, accesses the
network/shell/Git/GitHub, controls feeders/hardware, or executes feedback contents.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .bug_report import BugReportBuilder
from .confusion_report import TesterConfusionReport
from .feedback_form import FeedbackSubmission, TesterFeedbackForm
from .feedback_ledger import FeedbackLedgerEntry, TesterFeedbackLedger
from .feedback_profile import get_feedback_profile
from .release_blocker_classifier import ReleaseBlockerClassifier
from .safety import TesterFeedbackSafetyValidator
from .safety_concern import TesterSafetyConcern
from .suggestion_report import TesterSuggestionReport

_FORM_FILES = ("BUG_REPORT_FORM.md", "SAFETY_CONCERN_FORM.md",
               "CONFUSION_REPORT_FORM.md", "SUGGESTION_FORM.md")


@dataclass
class TesterFeedbackRuntime:
    """Bounded, local-only tester feedback runtime (QA ledger)."""

    tester_state_dir: str = ".solaris_ai_nn_tester"
    feedback_dir: str = ""
    profile: Optional[str] = None
    max_runtime_s: float = 60.0
    strict: bool = False
    dry_run: bool = False
    report_only: bool = False
    forms_only: bool = False
    ingest_path: str = ""
    build_bundle: bool = False
    privacy_redact: bool = True
    require_non_training_ack: bool = True
    require_claimguard: bool = False

    safety: TesterFeedbackSafetyValidator = field(
        default_factory=TesterFeedbackSafetyValidator, init=False)
    feedback_profile: Any = field(default=None, init=False)
    run_id: str = field(default="", init=False)
    bundle_dir: str = field(default="", init=False)
    ledger: Any = field(default=None, init=False)
    classifier: Any = field(default=None, init=False)
    ingested: List[Dict[str, Any]] = field(default_factory=list, init=False)
    classifications: List[Any] = field(default_factory=list, init=False)
    redactions: List[Dict[str, Any]] = field(default_factory=list, init=False)
    warnings: List[str] = field(default_factory=list, init=False)
    blockers: List[str] = field(default_factory=list, init=False)
    reports: Dict[str, Any] = field(default_factory=dict, init=False)
    bundle: Any = field(default=None, init=False)
    _refused: bool = field(default=False, init=False)

    _SUBDIRS = ("forms", "submissions", "ledger", "reports", "bundles",
                "index", "safety")

    def __post_init__(self) -> None:
        self.feedback_profile = get_feedback_profile(self.profile)
        if not self.feedback_dir:
            self.feedback_dir = os.path.join(self.tester_state_dir, "feedback")
        self.privacy_redact = self.privacy_redact \
            and self.feedback_profile.privacy_redact
        self.run_id = f"feedback_{int(time.time() * 1000)}"
        self.bundle_dir = os.path.join(self.feedback_dir, "bundles",
                                       f"FEEDBACK_BUNDLE_{self.run_id}")
        self.ledger = TesterFeedbackLedger(
            ledger_dir=os.path.join(self.feedback_dir, "ledger"))
        self.classifier = ReleaseBlockerClassifier()
        if not self.max_runtime_s:
            self._refused = True

    def initialize(self) -> Dict[str, Any]:
        created = []
        for sub in self._SUBDIRS:
            path = os.path.join(self.feedback_dir, sub)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            created.append({"name": sub, "existed": existed})
        return {"feedback_dir": self.feedback_dir, "directories": created,
                "deletes_feedback": False, "local_only": True}

    def run_doctor(self) -> Dict[str, Any]:
        bounded = self.safety.validate_bounded(self.max_runtime_s).safe
        return {"feedback_profile": self.feedback_profile.profile_id,
                "bounded": bounded, "local_only": True, "trains": False,
                "passed": bounded,
                "note": "feedback doctor validates the profile + bounded "
                        "runtime; feedback is local QA evidence, never training"}

    def run(self) -> Dict[str, Any]:
        if self._refused or not self.safety.validate_bounded(
                self.max_runtime_s).safe:
            return {"refused": True, "reason": "unbounded runtime"}
        self.initialize()

        if self.feedback_profile.generate_forms and not self.report_only \
                and not self.dry_run:
            self._generate_forms()

        if self.ingest_path and self.feedback_profile.ingest_enabled \
                and not self.forms_only:
            self._ingest(self.ingest_path)

        # Always (re)build the ledger index + reports from the ledger.
        if not self.dry_run:
            self.ledger.write_index()
            self._build_reports()
            if (self.build_bundle or self.feedback_profile.build_bundle):
                self._build_bundle()

        if self.require_claimguard and not _claimguard_available():
            self.warnings.append("ClaimGuard required but unavailable")

        if self.strict and self.release_blocker_count() > 0:
            self.blockers.append(
                f"{self.release_blocker_count()} release blocker(s) in feedback")

        self._update_integrations()
        return self._result()

    # -- forms --------------------------------------------------------------

    def _generate_forms(self) -> None:
        forms_dir = os.path.join(self.feedback_dir, "forms")
        os.makedirs(forms_dir, exist_ok=True)
        form = TesterFeedbackForm.build()
        with open(os.path.join(forms_dir, "TESTER_FEEDBACK_FORM.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(form.to_markdown())
        with open(os.path.join(forms_dir, "TESTER_FEEDBACK_FORM.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(form.to_dict(), fh, indent=2)
        for name, title, note in (
                ("BUG_REPORT_FORM.md", "Bug Report Form",
                 "Local bug evidence; patches nothing and creates no GitHub "
                 "issue."),
                ("SAFETY_CONCERN_FORM.md", "Safety Concern Form",
                 "Safety concerns are elevated as release blockers and never "
                 "suppressed."),
                ("CONFUSION_REPORT_FORM.md", "Confusion Report Form",
                 "Documentation/UX evidence; not a teaching signal."),
                ("SUGGESTION_FORM.md", "Suggestion Form",
                 "Review item only; never auto-applied.")):
            with open(os.path.join(forms_dir, name), "w",
                      encoding="utf-8") as fh:
                fh.write(_form_md(title, note))

    # -- ingest -------------------------------------------------------------

    def _ingest(self, path: str) -> None:
        records = self._load_ingest(path)
        for data in records:
            if not isinstance(data, dict):
                self.warnings.append("ignored non-object feedback record")
                continue
            entry = self._process_record(data)
            if entry is not None and not self.dry_run:
                self.ledger.append(entry)

    def _load_ingest(self, path: str) -> List[Dict[str, Any]]:
        if not os.path.isfile(path):
            self.warnings.append(f"ingest path not found: {path}")
            return []
        # Markdown ingest is treated as a single free-text "other" submission.
        if path.endswith(".md"):
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            return [{"feedback_type": "feedback", "category": "other",
                     "actual_behavior": text[:4000],
                     "non_training_acknowledgement": True}]
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as exc:
            self.warnings.append(f"could not parse ingest JSON: {exc}")
            return []
        if isinstance(data, list):
            return [d for d in data if isinstance(d, dict)]
        return [data]

    def _process_record(self, data: Dict[str, Any]) -> Optional[
            FeedbackLedgerEntry]:
        ftype = str(data.get("feedback_type", "")).lower()
        # Privacy scan + redaction.
        redaction_status, data = self._redact(data)
        if self.require_non_training_ack and not data.get(
                "non_training_acknowledgement"):
            self.warnings.append(
                f"feedback {data.get('feedback_id', '?')} missing non-training "
                "acknowledgement (recorded, flagged)")

        if ftype == "bug_report" or data.get("bug_id"):
            obj = BugReportBuilder().build(data).to_dict()
            ftype = "bug_report"
        elif ftype == "safety_concern" or data.get("concern_type"):
            obj = TesterSafetyConcern.from_dict(data).to_dict()
            ftype = "safety_concern"
        elif ftype == "confusion_report" or data.get("area"):
            obj = TesterConfusionReport.from_dict(data).to_dict()
            ftype = "confusion_report"
        elif ftype == "suggestion" or data.get("suggestion_type"):
            obj = TesterSuggestionReport.from_dict(data).to_dict()
            ftype = "suggestion"
        else:
            obj = FeedbackSubmission.from_dict(data).to_dict()
            obj["feedback_type"] = ftype or "feedback"
            ftype = obj["feedback_type"]

        self.ingested.append(obj)
        classification = self.classifier.classify(obj)
        self.classifications.append(classification)

        return FeedbackLedgerEntry(
            feedback_id=classification.feedback_id,
            feedback_type=ftype,
            timestamp=str(obj.get("created_utc")
                          or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
            tester_alias=str(obj.get("tester_alias", "anonymous")),
            category=str(obj.get("category", "")),
            severity=str(obj.get("severity",
                                 obj.get("blocker_severity", ""))),
            affected_stage=str(obj.get("stage_affected", obj.get("area", ""))),
            affected_command=str(obj.get("command_run",
                                         obj.get("affected_command", ""))),
            affected_artifact_paths=list(obj.get("artifact_paths", []) or []),
            release_blocker_status=classification.status,
            release_blocker_reason=classification.reason,
            privacy_redaction_status=redaction_status,
            non_training_acknowledgement=bool(
                data.get("non_training_acknowledgement", False)),
            payload=obj)

    def _redact(self, data: Dict[str, Any]):
        if not self.privacy_redact:
            return "not_scanned", data
        blob = json.dumps(data, default=str)
        scan = self.safety.scan_private_data(blob)
        if scan.safe:
            return "clean", data
        # Record the redaction; replace flagged text fields with a marker.
        self.redactions.append({"feedback_id": data.get("feedback_id", "?"),
                                "markers": scan.violations})
        redacted = dict(data)
        for key in ("actual_behavior", "expected_behavior", "manual_notes",
                    "description", "error_message"):
            if key in redacted and isinstance(redacted[key], str):
                low = redacted[key].lower()
                if any(m in low for m in ("password", "secret", "token",
                                          "api key", "api_key", "credential",
                                          "bearer ", "private key")):
                    redacted[key] = "[REDACTED: possible secret/private data]"
        return "redacted", redacted

    # -- reports + bundle ---------------------------------------------------

    def _build_reports(self) -> None:
        from .reports import TesterFeedbackReportBuilder
        self.reports = TesterFeedbackReportBuilder(self).write()

    def _build_bundle(self) -> None:
        from .feedback_bundle import FeedbackBundleBuilder
        self.bundle = FeedbackBundleBuilder().build(self)

    def _update_integrations(self) -> None:
        try:
            from ..inner_map.model import InnerMapModel  # noqa: F401
            self._inner_map_record = self.inner_map_record()
        except Exception:
            self.warnings.append("inner map unavailable (record skipped)")

    # -- views --------------------------------------------------------------

    def ledger_index(self):
        return self.ledger.load()

    def release_blocker_count(self) -> int:
        return self.ledger_index().release_blocker_count

    def stop_testing_count(self) -> int:
        return self.ledger_index().stop_testing_count

    def feedback_status(self) -> Dict[str, Any]:
        index = self.ledger_index()
        d = index.to_dict()
        return {
            "feedback_available": True,
            "feedback_run_id": self.run_id,
            "feedback_profile": self.feedback_profile.profile_id,
            "local_only": True, "trains_on_feedback": False,
            "entry_count": d["entry_count"],
            "by_type": d["by_type"],
            "bug_report_count": d["by_type"].get("bug_report", 0),
            "safety_concern_count": d["safety_concern_count"],
            "confusion_report_count": d["by_type"].get("confusion_report", 0),
            "suggestion_count": d["by_type"].get("suggestion", 0),
            "release_blocker_count": d["release_blocker_count"],
            "stop_testing_count": d["stop_testing_count"],
            "redaction_count": d["redaction_count"],
            "feedback_form_path": os.path.join(
                self.feedback_dir, "forms", "TESTER_FEEDBACK_FORM.md"),
            "feedback_ledger_path": self.ledger.jsonl_path,
            "latest_feedback_report_path": self.reports.get("markdown"),
            "latest_feedback_bundle_path": self.bundle_dir
            if self.bundle else None,
            "feedback_safety_block_count": self.safety.rejected_count,
            "creates_github_issue": False, "uploads": False,
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.feedback_status()

    def inner_map_record(self) -> Dict[str, Any]:
        st = self.feedback_status()
        return {
            "feedback_system_initialized": True,
            "feedback_count": st["entry_count"],
            "safety_concern_count": st["safety_concern_count"],
            "release_blocker_count": st["release_blocker_count"],
            "latest_feedback_report_path": st["latest_feedback_report_path"],
            "latest_feedback_bundle_path": st["latest_feedback_bundle_path"],
            "local_only": True, "trains_on_feedback": False,
        }

    def recommended_next_action(self) -> str:
        if self.stop_testing_count():
            return ("STOP testing now: a stop-testing safety concern was "
                    "recorded. Escalate to the developer for review.")
        if self.release_blocker_count():
            return ("Review the release blockers with the developer before "
                    "proceeding.")
        index = self.ledger_index()
        if not index.entries:
            return ("Fill in a feedback form and ingest it with "
                    "`tester-feedback-ingest`.")
        return ("Feedback is recorded for developer review; continue testing.")

    def _run_summary(self) -> Dict[str, Any]:
        index = self.ledger_index()
        return {
            "feedback_run_id": self.run_id,
            "feedback_profile": self.feedback_profile.to_dict(),
            "feedback_status": self.feedback_status(),
            "ledger_index": index.to_dict(),
            "entries": [e.to_dict() for e in index.entries],
            "classifications": [c.to_dict() for c in self.classifications],
            "redactions": list(self.redactions),
            "warnings": list(self.warnings), "blockers": list(self.blockers),
            "recommended_next_action": self.recommended_next_action(),
            "safety_status": self.safety.snapshot(),
        }

    def _result(self) -> Dict[str, Any]:
        st = self.feedback_status()
        return {
            "refused": False, "run_id": self.run_id,
            "feedback_profile": st["feedback_profile"],
            "entry_count": st["entry_count"],
            "bug_report_count": st["bug_report_count"],
            "safety_concern_count": st["safety_concern_count"],
            "release_blocker_count": st["release_blocker_count"],
            "stop_testing_count": st["stop_testing_count"],
            "redaction_count": st["redaction_count"],
            "blocked": bool(self.blockers),
            "blockers": list(self.blockers), "warnings": list(self.warnings),
            "latest_feedback_report_path": st["latest_feedback_report_path"],
            "latest_feedback_bundle_path": st["latest_feedback_bundle_path"],
            "recommended_next_action": self.recommended_next_action(),
        }


def _form_md(title: str, note: str) -> str:
    return (f"# {title}\n\n> {note}\n\n"
            "> This feedback is LOCAL QA evidence only. It is NOT training, "
            "NOT RLHF, NOT ground truth, and NOT a command. Do NOT include "
            "secrets, credentials, API keys, tokens, private messages, or raw "
            "private payloads. Artifact references must be local paths only.\n\n"
            "Fill in the fields and ingest with `tester-feedback-ingest "
            "--ingest-path <file.json>`.\n")


def _claimguard_available() -> bool:
    try:
        from ..governance.compliance import ClaimGuard  # noqa: F401
        return True
    except Exception:
        return False
