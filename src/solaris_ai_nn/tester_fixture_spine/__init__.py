"""Tester fixture spine -- fixture-only golden runs and a reproducible demo bundle.

Prompt 74 creates the first tester-safe reproducible demo spine. The tester release
must not begin with live data; it begins with fixture-only golden runs. This package
provides a deterministic fixture input pack, expected membrane/observation/learning/
claim-safety output invariants, a one-command tester demo, a golden artifact manifest,
a reproducibility checker, a regression checker, a tester demo report, a local tester
bundle, clear failure messages, and no live-environment requirement -- a known-good
organismic rehearsal before real birth/live testing.

It is bounded and fixture-only by default; the environmental membrane is required and
downstream learning consumes sensory impressions, never raw events. It never requires
live data/governance/feeders, starts/stops/controls feeders, controls hardware,
accesses the network/shell/browser/OS/Git/GitHub, runs external services, publishes or
uploads anything, executes commands from fixture text, treats human labels/debug gloss
as ground truth, trains on tester feedback, or claims consciousness, sentience,
biological life, personhood, agency, free will, emotion, feeling, understanding,
self-awareness, autonomous self-improvement, or subjective experience.
"""

from __future__ import annotations

from .artifact_bundle import (
    TesterArtifactBundle,
    TesterBundleBuilder,
    TesterBundleManifest,
)
from .expected_outputs import (
    ExpectedArtifactShape,
    ExpectedMetricRange,
    ExpectedOutputSpec,
    ExpectedSafetyInvariant,
    default_expected_outputs,
)
from .fixture_pack import (
    FixtureEvent,
    FixturePackBuilder,
    FixturePackValidator,
    TesterFixturePack,
)
from .golden_manifest import (
    GoldenArtifact,
    GoldenArtifactStatus,
    GoldenExpectation,
    GoldenManifestBuilder,
    GoldenRunManifest,
)
from .golden_run import (
    GoldenRunBuilder,
    GoldenRunStatus,
    GoldenRunStep,
    TesterGoldenRun,
)
from .regression_check import (
    RegressionFinding,
    RegressionStatus,
    TesterRegressionCheck,
)
from .reports import TesterFixtureSpineReportBuilder
from .reproducibility_check import (
    ReproducibilityCheckResult,
    ReproducibilityFinding,
    ReproducibilityStatus,
    TesterReproducibilityCheck,
)
from .safety import HARD_RULES, TesterFixtureSafetyValidator
from .tester_demo_runtime import TesterFixtureDemoRuntime
from .tester_profile import (
    DEFAULT_PROFILE_ID,
    TesterFixtureConstraint,
    TesterFixtureMode,
    TesterFixtureProfile,
    available_profiles,
    default_tester_profile,
    get_tester_profile,
)
from .tester_report import TesterDemoReport, TesterDemoReportBuilder

__all__ = [
    "HARD_RULES", "TesterFixtureSafetyValidator",
    "TesterFixtureProfile", "TesterFixtureMode", "TesterFixtureConstraint",
    "default_tester_profile", "get_tester_profile", "available_profiles",
    "DEFAULT_PROFILE_ID",
    "FixtureEvent", "TesterFixturePack", "FixturePackBuilder",
    "FixturePackValidator",
    "GoldenRunManifest", "GoldenArtifact", "GoldenArtifactStatus",
    "GoldenExpectation", "GoldenManifestBuilder",
    "TesterGoldenRun", "GoldenRunStep", "GoldenRunStatus", "GoldenRunBuilder",
    "ExpectedOutputSpec", "ExpectedArtifactShape", "ExpectedMetricRange",
    "ExpectedSafetyInvariant", "default_expected_outputs",
    "TesterArtifactBundle", "TesterBundleBuilder", "TesterBundleManifest",
    "TesterReproducibilityCheck", "ReproducibilityCheckResult",
    "ReproducibilityFinding", "ReproducibilityStatus",
    "TesterRegressionCheck", "RegressionFinding", "RegressionStatus",
    "TesterFixtureDemoRuntime",
    "TesterDemoReport", "TesterDemoReportBuilder",
    "TesterFixtureSpineReportBuilder",
]
