"""Pilot-2 -- read-only environmental soak protocol and comparative grounding.

Pilot-2 tests whether Solaris-AI-NN develops differently when exposed to a
read-only environmental sensory membrane instead of only the artificial
nursery. It is strictly one-way -- environment -> Solaris-AI-NN, never the
reverse. This package plans and preflights read-only exposure, curates safe
sources, schedules nursery/sensory/mixed windows, tracks source reliability,
compares arms cautiously, analyzes environmental grounding quality, writes
daily/weekly reviews and a Pilot-2 report, and gates the next step -- without
granting environmental actuation or confusing sensory input with commands.
"""

from __future__ import annotations

from .comparative_design import (
    ComparativeRunDesign,
    ComparisonArm,
    ComparisonMetric,
    ComparisonResult,
)
from .exposure_schedule import (
    ExposureCondition,
    ExposureSchedule,
    ExposureWindow,
)
from .grounding_analysis import (
    GroundingAnalysis,
    GroundingEvidence,
    GroundingQuality,
)
from .operator_runbook import Pilot2RunbookBuilder
from .pilot2_config import (
    DEFAULT_PILOT2_DIR,
    Pilot2Authority,
    Pilot2Config,
    Pilot2Mode,
    Pilot2SourceMode,
)
from .pilot2_decision_gate import (
    Pilot2DecisionGate,
    Pilot2DecisionOption,
    Pilot2DecisionResult,
)
from .pilot2_protocol import (
    Pilot2Phase,
    Pilot2PhaseRecord,
    Pilot2PhaseStatus,
    Pilot2Protocol,
    Pilot2ProtocolState,
)
from .pilot2_report import Pilot2Report, Pilot2ReportBuilder
from .safety import HARD_RULES, Pilot2SafetyReport, Pilot2SafetyValidator
from .sensory_daily_review import (
    Pilot2DailyRecommendation,
    Pilot2DailyReview,
    Pilot2DailyReviewBuilder,
)
from .sensory_weekly_review import Pilot2WeeklyReview, Pilot2WeeklyReviewBuilder
from .source_curation import (
    CuratedSourceSet,
    SourceCurationReport,
    SourceCurationRule,
)
from .source_preflight import (
    SourcePreflightCheck,
    SourcePreflightResult,
    SourcePreflightRunner,
)
from .source_reliability import (
    ReliabilityClass,
    SourceReliabilityMonitor,
    SourceReliabilityRecord,
)

__all__ = [
    # config / safety / protocol
    "Pilot2Config", "Pilot2Mode", "Pilot2Authority", "Pilot2SourceMode",
    "DEFAULT_PILOT2_DIR", "Pilot2SafetyValidator", "Pilot2SafetyReport",
    "HARD_RULES", "Pilot2Protocol", "Pilot2Phase", "Pilot2PhaseStatus",
    "Pilot2ProtocolState", "Pilot2PhaseRecord",
    # preflight / curation / schedule / reliability
    "SourcePreflightRunner", "SourcePreflightResult", "SourcePreflightCheck",
    "CuratedSourceSet", "SourceCurationReport", "SourceCurationRule",
    "ExposureSchedule", "ExposureWindow", "ExposureCondition",
    "SourceReliabilityMonitor", "SourceReliabilityRecord", "ReliabilityClass",
    # comparative / grounding
    "ComparativeRunDesign", "ComparisonArm", "ComparisonMetric",
    "ComparisonResult", "GroundingAnalysis", "GroundingEvidence",
    "GroundingQuality",
    # reviews / report / decision / runbook
    "Pilot2DailyReview", "Pilot2DailyReviewBuilder", "Pilot2DailyRecommendation",
    "Pilot2WeeklyReview", "Pilot2WeeklyReviewBuilder",
    "Pilot2Report", "Pilot2ReportBuilder",
    "Pilot2DecisionGate", "Pilot2DecisionResult", "Pilot2DecisionOption",
    "Pilot2RunbookBuilder",
]
