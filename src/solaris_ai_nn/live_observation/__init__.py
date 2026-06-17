"""Post-birth live observation -- live read-only stabilization, not learning.

Prompt 67 opened the first safe path from fixture-only Alpha to real, read-only
environmental input (the "birth" layer). Prompt 68 adds phases 2-3 of the post-birth
sequence: a bounded 2-6 hour live observation with **no learning**, and a 24-hour
report-only perceptual metabolism calibration.

The observation layer watches a bounded, local, read-only event stream to answer:
are the sources stable, noisy, or silent; which sources dominate the source diet;
is the event / quarantine rate safe; is there overload or deprivation; is the
operator pulse the only stimulus; is the field ready for metabolism (and, much
later and only with operator approval, narrow ontogenesis); and what should be
corrected next. It does not learn -- it is live read-only stabilization.

It never learns, forms concepts, births signs, runs developmental learning,
starts/stops/configures feeders, controls hardware, accesses the network/shell/
browser/OS/camera/microphone, calls Git/GitHub, executes commands, modifies source,
treats sensory text as a command, treats human labels or debug gloss as ground
truth, or claims consciousness, sentience, biological life, personhood, agency, free
will, emotion, feeling, understanding, self-awareness, or subjective experience.
"""

from __future__ import annotations

from .absence_analysis import (
    AbsenceFinding,
    AbsenceKind,
    AbsenceWindow,
    LiveAbsenceAnalysis,
    LiveAbsenceAnalyzer,
)
from .first_day_record import FirstDayRecordBuilder
from .metabolism_calibration import (
    MetabolismCalibrationResult,
    MetabolismThresholdRecommendation,
    PerceptualMetabolismCalibrator,
)
from .observation_profile import (
    DEFAULT_PROFILE_ID,
    LiveObservationConstraint,
    LiveObservationMode,
    LiveObservationProfile,
    available_profiles,
    default_observation_profile,
    get_observation_profile,
)
from .observation_runtime import PostBirthLiveObservationRuntime
from .observation_window import (
    LiveObservationWindow,
    ObservationWindowBuilder,
    ObservationWindowStatus,
    ObservationWindowSummary,
    parse_timestamp,
)
from .overload_deprivation import (
    DeprivationMarker,
    LiveOverloadDeprivationAssessment,
    LiveOverloadDeprivationAssessor,
    LoadStatus,
    OverloadMarker,
)
from .reports import LiveObservationReportBuilder
from .rhythm_analysis import (
    LiveRhythmAnalysis,
    LiveRhythmAnalyzer,
    RhythmFinding,
    RhythmKind,
    RhythmPattern,
    RhythmStrength,
)
from .safety import HARD_RULES, LiveObservationSafetyValidator
from .source_diet import (
    LiveSourceDiet,
    LiveSourceDietAnalyzer,
    SourceDietBalance,
    SourceDietFinding,
)
from .source_health import (
    LiveSourceHealth,
    LiveSourceHealthEvaluator,
    SourceHealthFinding,
    SourceHealthStatus,
)
from .stability_gate import (
    LiveStabilityBlocker,
    LiveStabilityGate,
    LiveStabilityGateResult,
    LiveStabilityStatus,
)

__all__ = [
    "HARD_RULES", "LiveObservationSafetyValidator",
    "LiveObservationProfile", "LiveObservationMode", "LiveObservationConstraint",
    "default_observation_profile", "get_observation_profile",
    "available_profiles", "DEFAULT_PROFILE_ID",
    "LiveObservationWindow", "ObservationWindowBuilder",
    "ObservationWindowStatus", "ObservationWindowSummary", "parse_timestamp",
    "LiveSourceHealth", "LiveSourceHealthEvaluator", "SourceHealthFinding",
    "SourceHealthStatus",
    "LiveSourceDiet", "LiveSourceDietAnalyzer", "SourceDietBalance",
    "SourceDietFinding",
    "LiveRhythmAnalysis", "LiveRhythmAnalyzer", "RhythmFinding", "RhythmKind",
    "RhythmPattern", "RhythmStrength",
    "LiveAbsenceAnalysis", "LiveAbsenceAnalyzer", "AbsenceFinding", "AbsenceKind",
    "AbsenceWindow",
    "LiveOverloadDeprivationAssessment", "LiveOverloadDeprivationAssessor",
    "OverloadMarker", "DeprivationMarker", "LoadStatus",
    "MetabolismCalibrationResult", "MetabolismThresholdRecommendation",
    "PerceptualMetabolismCalibrator",
    "LiveStabilityGate", "LiveStabilityGateResult", "LiveStabilityBlocker",
    "LiveStabilityStatus",
    "PostBirthLiveObservationRuntime",
    "FirstDayRecordBuilder", "LiveObservationReportBuilder",
]
