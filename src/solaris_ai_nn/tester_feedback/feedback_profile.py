"""Tester feedback profile -- bounded, local, non-training QA-ledger config.

:class:`TesterFeedbackProfile` describes a bounded feedback run. The default profile
(``tester_feedback_v0``) keeps all feedback local and append-only, never trains on it,
never modifies Solaris behaviour, never creates remote issues or uploads, elevates
safety concerns to release blockers, makes unsupported-claim reports visible, and
requires a privacy warning and a non-training acknowledgement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class TesterFeedbackMode:
    TESTER_FEEDBACK_FORMS_ONLY = "tester_feedback_forms_only"
    TESTER_FEEDBACK_INTAKE = "tester_feedback_intake"
    TESTER_FEEDBACK_LEDGER = "tester_feedback_ledger"
    TESTER_FEEDBACK_BUNDLE = "tester_feedback_bundle"
    TESTER_FEEDBACK_REPORT_ONLY = "tester_feedback_report_only"
    DOCTOR_ONLY = "doctor_only"

    ALL = (TESTER_FEEDBACK_FORMS_ONLY, TESTER_FEEDBACK_INTAKE,
           TESTER_FEEDBACK_LEDGER, TESTER_FEEDBACK_BUNDLE,
           TESTER_FEEDBACK_REPORT_ONLY, DOCTOR_ONLY)


class TesterFeedbackConstraint:
    LOCAL_ONLY = "local_only"
    APPEND_ONLY_LEDGER = "append_only_ledger"
    NO_TRAINING = "no_training"
    NO_RLHF = "no_rlhf"
    NO_AUTO_BEHAVIOR_CHANGE = "no_automatic_behavior_change"
    NO_AUTO_ISSUE_CREATION = "no_automatic_issue_creation"
    NO_UPLOAD = "no_upload"
    NO_NETWORK_SHELL_GIT = "no_network_shell_browser_os_git_github"
    NO_COMMAND_EXECUTION = "no_command_execution"
    NO_FEEDER_CONTROL = "no_feeder_control"
    NO_HARDWARE_CONTROL = "no_hardware_control"
    FEEDBACK_NOT_COMMAND = "feedback_text_is_not_command"
    FEEDBACK_NOT_GROUND_TRUTH = "feedback_text_is_not_ground_truth"
    LABELS_NOT_ONTOLOGY = "tester_labels_are_not_ontology"
    SAFETY_CONCERNS_ELEVATED = "safety_concerns_elevated_as_release_blockers"
    UNSUPPORTED_CLAIM_VISIBLE = "unsupported_claim_reports_must_be_visible"
    PRIVACY_WARNING_REQUIRED = "privacy_warning_required"
    BOUNDED_RUNTIME = "bounded_runtime"
    CLAIMGUARD_IF_AVAILABLE = "claimguard_or_equivalent_scan_if_available"

    ALL = (LOCAL_ONLY, APPEND_ONLY_LEDGER, NO_TRAINING, NO_RLHF,
           NO_AUTO_BEHAVIOR_CHANGE, NO_AUTO_ISSUE_CREATION, NO_UPLOAD,
           NO_NETWORK_SHELL_GIT, NO_COMMAND_EXECUTION, NO_FEEDER_CONTROL,
           NO_HARDWARE_CONTROL, FEEDBACK_NOT_COMMAND, FEEDBACK_NOT_GROUND_TRUTH,
           LABELS_NOT_ONTOLOGY, SAFETY_CONCERNS_ELEVATED,
           UNSUPPORTED_CLAIM_VISIBLE, PRIVACY_WARNING_REQUIRED, BOUNDED_RUNTIME,
           CLAIMGUARD_IF_AVAILABLE)


DEFAULT_PROFILE_ID = "tester_feedback_v0"


@dataclass
class TesterFeedbackProfile:
    """A bounded, local, non-training tester feedback profile."""

    profile_id: str
    purpose: str
    mode: str = TesterFeedbackMode.TESTER_FEEDBACK_INTAKE
    constraints: List[str] = field(default_factory=list)
    max_runtime_s: float = 60.0
    generate_forms: bool = True
    ingest_enabled: bool = True
    build_bundle: bool = False
    privacy_redact: bool = True
    require_non_training_ack: bool = True
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in TesterFeedbackMode.ALL:
            self.mode = TesterFeedbackMode.TESTER_FEEDBACK_INTAKE
        m = self.mode
        if m == TesterFeedbackMode.TESTER_FEEDBACK_FORMS_ONLY:
            self.ingest_enabled = False
        elif m == TesterFeedbackMode.TESTER_FEEDBACK_BUNDLE:
            self.build_bundle = True
        elif m in (TesterFeedbackMode.TESTER_FEEDBACK_REPORT_ONLY,
                   TesterFeedbackMode.DOCTOR_ONLY):
            self.generate_forms = False
            self.ingest_enabled = False

    @property
    def is_forms_only(self) -> bool:
        return self.mode == TesterFeedbackMode.TESTER_FEEDBACK_FORMS_ONLY

    @property
    def is_doctor_only(self) -> bool:
        return self.mode == TesterFeedbackMode.DOCTOR_ONLY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode, "constraints": list(self.constraints),
            "max_runtime_s": self.max_runtime_s,
            "generate_forms": self.generate_forms,
            "ingest_enabled": self.ingest_enabled,
            "build_bundle": self.build_bundle,
            "privacy_redact": self.privacy_redact,
            "require_non_training_ack": self.require_non_training_ack,
            "local_only": True, "trains_on_feedback": False,
            "limitations": list(self.limitations),
        }


def default_feedback_profile() -> TesterFeedbackProfile:
    """The default local, non-training tester feedback profile."""
    return TesterFeedbackProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("a local, append-only tester QA ledger: generate feedback "
                 "forms, ingest local feedback (bugs, safety concerns, "
                 "confusion, suggestions), classify release blockers, and build "
                 "local reports/bundles for developer review -- feedback is QA "
                 "evidence only, never training, RLHF, ground truth, or a "
                 "command, and it never modifies Solaris behaviour"),
        mode=TesterFeedbackMode.TESTER_FEEDBACK_INTAKE,
        constraints=list(TesterFeedbackConstraint.ALL),
        max_runtime_s=60.0,
        limitations=[
            "local QA evidence only; feedback is never training, RLHF, ground "
            "truth, or a command, and it never modifies Solaris behaviour",
            "the ledger is append-only and local; feedback is never uploaded, "
            "published, or turned into a remote issue automatically",
            "safety concerns are elevated as release blockers; unsupported "
            "consciousness/life/agency claim concerns are release blockers until "
            "reviewed",
            "secrets/credentials/private messages must not be included; the "
            "system warns and redacts obvious markers",
            "this is NOT the Human Feedback / Teaching Loop and is NOT RLHF",
            "release blockers are developer review items, not automatic actions"])


def _profile_for_mode(mode: str) -> TesterFeedbackProfile:
    p = default_feedback_profile()
    p.profile_id = f"{mode}_v0"
    p.mode = mode
    p.__post_init__()
    purposes = {
        TesterFeedbackMode.TESTER_FEEDBACK_FORMS_ONLY:
            "generate the local feedback forms only",
        TesterFeedbackMode.TESTER_FEEDBACK_LEDGER:
            "rebuild the feedback ledger index only",
        TesterFeedbackMode.TESTER_FEEDBACK_BUNDLE:
            "build the local feedback bundle",
        TesterFeedbackMode.TESTER_FEEDBACK_REPORT_ONLY:
            "rebuild the feedback reports from the existing ledger only",
        TesterFeedbackMode.DOCTOR_ONLY:
            "validate feedback prerequisites only",
    }
    if mode in purposes:
        p.purpose = purposes[mode]
    return p


def get_feedback_profile(profile_id: Optional[str] = None,
                         ) -> TesterFeedbackProfile:
    """Return the named profile, defaulting to ``tester_feedback_v0``."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_feedback_profile()
    for mode in TesterFeedbackMode.ALL:
        if profile_id in (mode, f"{mode}_v0"):
            return _profile_for_mode(mode)
    p = default_feedback_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using the "
                         "default tester feedback profile")
    return p


def available_profiles() -> List[str]:
    return [DEFAULT_PROFILE_ID] + [f"{m}_v0" for m in TesterFeedbackMode.ALL]
