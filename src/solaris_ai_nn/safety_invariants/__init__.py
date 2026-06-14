"""System-wide safety invariants, red-team harness, and assurance case.

Solaris-AI-NN has many boundaries -- a read-only sensory membrane, a
simulation-only motor membrane, an always-on actuation firewall, governance
gates, Ego source/action classification, ClaimGuard, the Pilot-1/2/3/4
protocols, the conscience orchestrator, the emergency stop. This package makes
safety *executable*: a registry of safety invariants, a runner that checks them
read-only, an inert red-team scenario harness, a boundary regression suite, an
append-only safety evidence ledger, an assurance-case compiler, a failure triage,
a safety dashboard, and reports.

Core principle: safety must be executable, testable, repeatable, and auditable.
The safety layer itself runs no real actions, mutates nothing, starts no long
runs, hides no critical failure, and makes no claim of consciousness, free will,
agency, personhood, sentience, or life.
"""

from __future__ import annotations

from .adversarial_fixtures import AdversarialFixture, AdversarialFixtureFactory
from .assurance_case import (
    AssuranceCase,
    AssuranceCaseCompiler,
    AssuranceClaim,
    AssuranceEvidence,
    AssuranceStatus,
)
from .boundary_tests import (
    BoundaryRegressionSuite,
    BoundaryTestResult,
    BoundaryTestStatus,
)
from .dashboard import SafetyInvariantDashboard
from .evidence_ledger import (
    SafetyEvidenceKind,
    SafetyEvidenceLedger,
    SafetyEvidenceRecord,
)
from .failure_triage import (
    FailureTriageResult,
    SafetyFailure,
    SafetyFailureClass,
    SafetyFailureTriage,
    SafetyRecommendedAction,
)
from .invariant import (
    InvariantCategory,
    InvariantCheckResult,
    InvariantSeverity,
    InvariantStatus,
    SafetyInvariant,
)
from .red_team_scenarios import (
    RedTeamExpected,
    RedTeamHarness,
    RedTeamScenario,
    RedTeamScenarioResult,
    RedTeamScenarioType,
)
from .registry import SafetyInvariantRegistry
from .reports import SafetyInvariantReport, SafetyInvariantReportBuilder
from .runner import InvariantResultBundle, SafetyInvariantRunner
from .safety import HARD_RULES, SafetyInvariantSystemValidator

__all__ = [
    # invariant model / registry / runner
    "SafetyInvariant", "InvariantCategory", "InvariantSeverity",
    "InvariantStatus", "InvariantCheckResult", "SafetyInvariantRegistry",
    "SafetyInvariantRunner", "InvariantResultBundle",
    # red-team / fixtures / boundary
    "RedTeamScenario", "RedTeamScenarioType", "RedTeamScenarioResult",
    "RedTeamHarness", "RedTeamExpected", "AdversarialFixture",
    "AdversarialFixtureFactory", "BoundaryRegressionSuite",
    "BoundaryTestResult", "BoundaryTestStatus",
    # evidence / assurance / triage
    "SafetyEvidenceLedger", "SafetyEvidenceRecord", "SafetyEvidenceKind",
    "AssuranceCase", "AssuranceCaseCompiler", "AssuranceClaim",
    "AssuranceEvidence", "AssuranceStatus", "SafetyFailure",
    "FailureTriageResult", "SafetyFailureTriage", "SafetyFailureClass",
    "SafetyRecommendedAction",
    # dashboard / reports / safety
    "SafetyInvariantDashboard", "SafetyInvariantReport",
    "SafetyInvariantReportBuilder", "SafetyInvariantSystemValidator",
    "HARD_RULES",
]
