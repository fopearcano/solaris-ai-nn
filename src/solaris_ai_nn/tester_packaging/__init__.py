"""Tester release packaging, install guide, environment doctor, clean-machine (P78).

This package makes Solaris-AI-NN ready for a first trusted tester installation: a local
editable install (``pip install -e .`` in a venv), a doctor command, the fixture tester
demo, the static console, live-read-only templates, safe/unsafe event packs, a local
tester bundle, and feedback forms. It is about installability, packaging hygiene,
environment checks, dependency clarity, command discovery, and clean-machine readiness.

It is **not** a public release, **not** a product installer, and **not** cloud
deployment. The packaging runtime is local and report-only: it installs nothing,
publishes/uploads nothing, creates no Git releases/tags/issues, opens no browser, starts
no background services, runs no shell, accesses no network/Git/GitHub, controls no
feeders/hardware, executes no commands from docs/feedback text, trains on no feedback,
and makes no claim of consciousness, sentience, biological life, personhood, agency,
free will, emotion, feeling, understanding, self-awareness, autonomous self-improvement,
or subjective experience.
"""

from __future__ import annotations

from .clean_machine_check import (
    CleanMachineChecklist,
    CleanMachineChecklistItem,
    CleanMachineReadinessCheck,
    CleanMachineReadinessResult,
    CleanMachineStatus,
)
from .command_registry_check import (
    CommandCheckResult,
    CommandRegistryCheck,
    RegisteredCommand,
)
from .dependency_check import (
    DependencyCheck,
    DependencyCheckResult,
    DependencyFinding,
    DependencyKind,
)
from .environment_doctor import (
    EnvironmentDoctorResult,
    EnvironmentFinding,
    EnvironmentHealth,
    TesterEnvironmentDoctor,
)
from .install_guide_builder import (
    InstallGuide,
    InstallStep,
    TesterInstallGuideBuilder,
)
from .packaging_profile import (
    DEFAULT_PROFILE_ID,
    TesterPackagingConstraint,
    TesterPackagingMode,
    TesterPackagingProfile,
    available_profiles,
    default_packaging_profile,
    get_packaging_profile,
)
from .packaging_runtime import TesterPackagingRuntime
from .platform_notes import PlatformKind, PlatformNote, PlatformNotesBuilder
from .release_manifest import (
    ReleaseArtifact,
    ReleaseManifestBuilder,
    ReleaseReadinessStatus,
    TesterReleaseManifest,
)
from .reports import TesterPackagingReportBuilder
from .safety import HARD_RULES, TesterPackagingSafetyValidator

__all__ = [
    "HARD_RULES", "TesterPackagingSafetyValidator",
    "TesterPackagingProfile", "TesterPackagingMode", "TesterPackagingConstraint",
    "default_packaging_profile", "get_packaging_profile", "available_profiles",
    "DEFAULT_PROFILE_ID",
    "DependencyCheck", "DependencyCheckResult", "DependencyFinding",
    "DependencyKind",
    "TesterEnvironmentDoctor", "EnvironmentDoctorResult", "EnvironmentFinding",
    "EnvironmentHealth",
    "CommandRegistryCheck", "RegisteredCommand", "CommandCheckResult",
    "TesterInstallGuideBuilder", "InstallStep", "InstallGuide",
    "TesterReleaseManifest", "ReleaseManifestBuilder", "ReleaseArtifact",
    "ReleaseReadinessStatus",
    "CleanMachineReadinessCheck", "CleanMachineChecklist",
    "CleanMachineChecklistItem", "CleanMachineReadinessResult",
    "CleanMachineStatus",
    "PlatformNotesBuilder", "PlatformNote", "PlatformKind",
    "TesterPackagingRuntime", "TesterPackagingReportBuilder",
]
