"""Tester live-read-only profile -- the safe bridge from fixtures to live testing.

Prompt 74 created a fixture-only tester demo. Prompt 75 (this package) creates the safe
bridge from fixture testing to trusted live-read-only testing: a tester live-read-only
profile, governance + feeder registry templates, a safe/unsafe/mixed external event
pack, external feeder script templates (under ``tools/external_feeders/``), a live
tester doctor, a non-executing checklist, a bounded local runtime, a local live tester
bundle, and reports.

The central architectural rule: **Solaris does not run feeders.** Feeders are dumb
external scripts or manual files created by the tester/operator; the external scripts
may read simple local/public-safe signals and write JSONL events, but the Solaris
runtime never starts, stops, schedules, controls, or edits them. The correct path is:
tester/operator manually runs or writes feeder events -> JSONL files appear in
``.solaris_ai_nn_live/inbox/`` -> Solaris validates events -> the Environmental
Membrane creates sensory impressions -> observation/reporting consume impressions ->
the tester bundle records what happened.

The runtime is bounded and local-only; it never controls feeders/hardware, accesses
the network/shell/browser/OS/Git/GitHub, runs external services, publishes/uploads,
executes commands, treats feeder/sensory text as a command, treats human labels/debug
gloss as ground truth or the operator pulse as teaching, trains on tester feedback, or
claims consciousness, sentience, biological life, personhood, agency, free will,
emotion, feeling, understanding, self-awareness, autonomous self-improvement, or
subjective experience.
"""

from __future__ import annotations

from .feeder_templates import (
    TesterFeederRegistryTemplate,
    TesterFeederTemplateBuilder,
    TesterFeederTemplateRecord,
)
from .governance_templates import (
    GovernanceTemplateBuilder,
    GovernanceTemplateStatus,
    TesterLiveGovernanceTemplate,
)
from .live_tester_bundle import (
    TesterLiveBundle,
    TesterLiveBundleBuilder,
    TesterLiveBundleManifest,
)
from .live_tester_checklist import (
    TesterChecklistItem,
    TesterChecklistStatus,
    TesterLiveChecklist,
)
from .live_tester_doctor import (
    TesterLiveDoctor,
    TesterLiveDoctorFinding,
    TesterLiveDoctorResult,
    TesterLiveDoctorStatus,
)
from .live_tester_profile import (
    DEFAULT_PROFILE_ID,
    TesterLiveConstraint,
    TesterLiveMode,
    TesterLiveReadOnlyProfile,
    available_profiles,
    default_live_tester_profile,
    get_live_tester_profile,
)
from .live_tester_report import TesterLiveReport, TesterLiveReportBuilder
from .live_tester_runtime import TesterLiveReadOnlyRuntime
from .reports import TesterLiveReadOnlyReportBuilder
from .safe_event_pack import (
    SafeEventExample,
    SafeEventPackBuilder,
    SafeEventPackValidator,
    TesterSafeEventPack,
    UnsafeEventExample,
)
from .safety import HARD_RULES, TesterLiveReadOnlySafetyValidator

__all__ = [
    "HARD_RULES", "TesterLiveReadOnlySafetyValidator",
    "TesterLiveReadOnlyProfile", "TesterLiveMode", "TesterLiveConstraint",
    "default_live_tester_profile", "get_live_tester_profile",
    "available_profiles", "DEFAULT_PROFILE_ID",
    "TesterLiveGovernanceTemplate", "GovernanceTemplateBuilder",
    "GovernanceTemplateStatus",
    "TesterFeederRegistryTemplate", "TesterFeederTemplateRecord",
    "TesterFeederTemplateBuilder",
    "TesterSafeEventPack", "SafeEventExample", "UnsafeEventExample",
    "SafeEventPackBuilder", "SafeEventPackValidator",
    "TesterLiveDoctor", "TesterLiveDoctorResult", "TesterLiveDoctorFinding",
    "TesterLiveDoctorStatus",
    "TesterLiveChecklist", "TesterChecklistItem", "TesterChecklistStatus",
    "TesterLiveReadOnlyRuntime",
    "TesterLiveBundle", "TesterLiveBundleBuilder", "TesterLiveBundleManifest",
    "TesterLiveReport", "TesterLiveReportBuilder",
    "TesterLiveReadOnlyReportBuilder",
]
