"""Minimal local operator console for the first tester release (Prompt 76).

A trusted tester should not need to read dozens of raw JSON/Markdown files by hand. This
package discovers the local artifacts produced by the alpha/live/tester runs and
generates a static, local, read-only dashboard -- static Markdown (the primary output)
and an optional static offline HTML page -- summarizing the tester release status,
latest runs, reports, artifact index, safety blockers, quarantine, membrane status,
membrane integration, sensory impressions, source pressure/diet, live birth/observation,
optional learning summaries, scientific-claim warnings, reproducibility/regression
status, bundle status, missing artifacts, skipped stages, next recommended action, and
known limitations.

It is a read-only console, not a control panel. It runs no server by default, opens no
browser, controls no feeders/hardware, accesses no network/shell/browser/OS/Git/GitHub,
runs no external services, publishes/uploads nothing, executes no artifact contents,
shows no raw private payloads by default, trains on no tester feedback, and makes no
claim of consciousness, sentience, biological life, personhood, agency, free will,
emotion, feeling, understanding, self-awareness, autonomous self-improvement, or
subjective experience.
"""

from __future__ import annotations

from .artifact_discovery import (
    ArtifactDiscoveryResult,
    ArtifactKind,
    ConsoleArtifactDiscovery,
    DiscoveredArtifact,
)
from .console_profile import (
    DEFAULT_PROFILE_ID,
    TesterConsoleConstraint,
    TesterConsoleMode,
    TesterConsoleProfile,
    available_profiles,
    default_console_profile,
    get_console_profile,
)
from .console_runtime import TesterConsoleRuntime
from .dashboard_builder import TesterDashboard, TesterDashboardBuilder
from .html_builder import TesterConsoleHtmlBuilder
from .markdown_builder import TesterConsoleMarkdownBuilder
from .next_actions import (
    ConsoleNextAction,
    NextActionBuilder,
    NextActionPriority,
)
from .reports import TesterConsoleReportBuilder
from .run_index import (
    RunIndexBuilder,
    RunType,
    TesterRunIndex,
    TesterRunRecord,
)
from .safety import HARD_RULES, TesterConsoleSafetyValidator
from .safety_panel import (
    ConsoleSafetyPanel,
    SafetyPanelBuilder,
    SafetyPanelFinding,
    SafetyPanelStatus,
)
from .status_model import (
    ConsoleBlocker,
    ConsoleWarning,
    StageHealth,
    StageStatus,
    StatusModelBuilder,
    TesterConsoleStatus,
)
from .summary_cards import (
    ConsoleSummaryCard,
    SummaryCardBuilder,
    SummaryCardKind,
    SummarySeverity,
)

__all__ = [
    "HARD_RULES", "TesterConsoleSafetyValidator",
    "TesterConsoleProfile", "TesterConsoleMode", "TesterConsoleConstraint",
    "default_console_profile", "get_console_profile", "available_profiles",
    "DEFAULT_PROFILE_ID",
    "ConsoleArtifactDiscovery", "DiscoveredArtifact", "ArtifactDiscoveryResult",
    "ArtifactKind",
    "TesterConsoleStatus", "StageStatus", "StageHealth", "ConsoleBlocker",
    "ConsoleWarning", "StatusModelBuilder",
    "ConsoleSummaryCard", "SummaryCardKind", "SummarySeverity",
    "SummaryCardBuilder",
    "TesterDashboard", "TesterDashboardBuilder",
    "TesterConsoleMarkdownBuilder", "TesterConsoleHtmlBuilder",
    "TesterRunIndex", "TesterRunRecord", "RunIndexBuilder", "RunType",
    "ConsoleSafetyPanel", "SafetyPanelFinding", "SafetyPanelStatus",
    "SafetyPanelBuilder",
    "ConsoleNextAction", "NextActionBuilder", "NextActionPriority",
    "TesterConsoleRuntime", "TesterConsoleReportBuilder",
]
