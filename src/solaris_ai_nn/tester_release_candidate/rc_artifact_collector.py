"""Tester RC artifact collector -- bounded, local references to release artifacts.

:class:`TesterRCArtifactCollector` resolves local references to the docs, reports, and
templates a trusted tester needs. It records whether each artifact is present, its tier
(required/recommended/optional), and a short label. Missing required artifacts block
readiness; missing recommended artifacts warn; missing optional artifacts are noted. It
reads file existence only; it never opens the network, executes anything, or includes
secrets/private payloads.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class RCArtifactTier:
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


@dataclass
class CollectedRCArtifact:
    """One resolved RC artifact reference (a path, not a copy)."""

    key: str
    label: str
    tier: str
    path: str = ""
    present: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"key": self.key, "label": self.label, "tier": self.tier,
                "path": self.path, "present": self.present}


@dataclass
class RCArtifactCollectionResult:
    """The result of collecting RC artifact references."""

    artifacts: List[CollectedRCArtifact] = field(default_factory=list)

    def by_tier(self, tier: str) -> List[CollectedRCArtifact]:
        return [a for a in self.artifacts if a.tier == tier]

    def present(self, key: str) -> bool:
        for a in self.artifacts:
            if a.key == key:
                return a.present
        return False

    def path(self, key: str) -> Optional[str]:
        for a in self.artifacts:
            if a.key == key and a.present:
                return a.path
        return None

    @property
    def missing_required(self) -> List[CollectedRCArtifact]:
        return [a for a in self.by_tier(RCArtifactTier.REQUIRED)
                if not a.present]

    @property
    def missing_recommended(self) -> List[CollectedRCArtifact]:
        return [a for a in self.by_tier(RCArtifactTier.RECOMMENDED)
                if not a.present]

    @property
    def missing_optional(self) -> List[CollectedRCArtifact]:
        return [a for a in self.by_tier(RCArtifactTier.OPTIONAL)
                if not a.present]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_count": len(self.artifacts),
            "present_count": sum(1 for a in self.artifacts if a.present),
            "missing_required_count": len(self.missing_required),
            "missing_recommended_count": len(self.missing_recommended),
            "missing_optional_count": len(self.missing_optional),
            "missing_required": [a.key for a in self.missing_required],
            "missing_recommended": [a.key for a in self.missing_recommended],
            "missing_optional": [a.key for a in self.missing_optional],
            "artifacts": [a.to_dict() for a in self.artifacts],
            "local_only": True, "uploaded": False, "published": False,
            "includes_private_payloads": False,
            "note": "local artifact references only; no secrets or raw private "
                    "payloads are collected, and nothing is uploaded",
        }


# (key, label, tier, [candidate relative paths]). The first existing candidate
# wins. ``{ts}`` is the tester state dir; ``{pkg}`` is <ts>/packaging;
# ``{sf}`` is <ts>/safety_freeze; ``{fb}`` is <ts>/feedback.
_SPECS = (
    # Required.
    ("readme", "README", "required", ["README.md"]),
    ("install_guide", "install guide", "required",
     ["{pkg}/install_guides/TESTER_INSTALL_GUIDE.md",
      "docs/TESTER_QUICKSTART.md"]),
    ("quickstart", "quickstart", "required",
     ["{pkg}/install_guides/TESTER_QUICKSTART.md", "docs/TESTER_QUICKSTART.md"]),
    ("packaging_report", "tester packaging report", "required",
     ["{pkg}/reports/PACKAGING_REPORT.md"]),
    ("environment_doctor_report", "environment doctor report", "required",
     ["{pkg}/reports/ENVIRONMENT_DOCTOR_REPORT.md",
      "{pkg}/reports/PACKAGING_REPORT.md"]),
    ("command_registry_report", "command registry report", "required",
     ["{pkg}/reports/COMMAND_REGISTRY_REPORT.md",
      "{pkg}/reports/PACKAGING_REPORT.md"]),
    ("clean_machine_report", "clean-machine readiness report", "required",
     ["{pkg}/reports/CLEAN_MACHINE_READINESS_REPORT.md",
      "{pkg}/reports/PACKAGING_REPORT.md"]),
    ("safety_freeze_report", "tester safety freeze report", "required",
     ["{sf}/reports/TESTER_SAFETY_FREEZE_REPORT.md"]),
    ("release_blocker_report", "release blocker report", "required",
     ["{sf}/reports/TESTER_RELEASE_BLOCKERS.md", "docs/RELEASE_BLOCKERS.md"]),
    ("forbidden_claims_doc", "forbidden claims doc", "required",
     ["docs/FORBIDDEN_CLAIMS.md"]),
    ("allowed_language_doc", "allowed operational language doc", "required",
     ["docs/ALLOWED_OPERATIONAL_LANGUAGE.md"]),
    ("feedback_form", "tester feedback form", "required",
     ["{fb}/forms/TESTER_FEEDBACK_FORM.md", "docs/TESTER_FEEDBACK_GUIDE.md"]),
    ("fixture_instructions", "tester fixture instructions", "required",
     ["docs/TESTER_RUNBOOK.md", "docs/EXPERIMENTS.md"]),
    ("live_readonly_instructions", "tester live-read-only instructions",
     "required", ["docs/TESTER_RUNBOOK.md"]),
    ("external_feeder_policy", "external feeder policy", "required",
     ["examples/tester_live_readonly/README.md", "docs/TESTER_RUNBOOK.md"]),
    ("console_instructions", "tester console instructions", "required",
     ["docs/TESTER_RUNBOOK.md"]),
    ("safety_boundaries_doc", "tester safety boundaries", "required",
     ["docs/TESTER_SAFETY_BOUNDARIES.md"]),
    # Recommended.
    ("fixture_demo_report", "fixture demo report", "recommended",
     ["{ts}/reports/TESTER_DEMO_REPORT.md"]),
    ("reproducibility_report", "reproducibility report", "recommended",
     ["{ts}/reproducibility/TESTER_REPRODUCIBILITY_REPORT.md"]),
    ("regression_report", "regression report", "recommended",
     ["{ts}/regression/TESTER_REGRESSION_REPORT.md"]),
    ("console_index", "tester console index", "recommended",
     ["{ts}/console/INDEX.md"]),
    ("live_doctor_report", "tester live doctor report", "recommended",
     ["{ts}/live/reports/TESTER_LIVE_DOCTOR_REPORT.md"]),
    ("membrane_report", "membrane report", "recommended",
     [".solaris_ai_nn_live/membrane/reports/ENVIRONMENTAL_MEMBRANE_REPORT.md"]),
    ("membrane_integration_report", "membrane integration report",
     "recommended",
     [".solaris_ai_nn_live/membrane/integration/"
      "MEMBRANE_INTEGRATION_REPORT.md"]),
    ("observation_report", "observation report", "recommended",
     [".solaris_ai_nn_live/observation/reports/LIVE_OBSERVATION_REPORT.md"]),
    ("feedback_report", "feedback report", "recommended",
     ["{fb}/reports/TESTER_FEEDBACK_REPORT.md"]),
    # Optional.
    ("ontogenesis_report", "ontogenesis report", "optional",
     [".solaris_ai_nn_live/ontogenesis/reports/LIVE_ONTOGENESIS_REPORT.md"]),
    ("semiogenesis_report", "semiogenesis report", "optional",
     [".solaris_ai_nn_live/semiogenesis/reports/LIVE_SEMIOGENESIS_REPORT.md"]),
    ("cognition_report", "cognition report", "optional",
     [".solaris_ai_nn_live/cognition/reports/LIVE_COGNITION_REPORT.md"]),
    ("scientific_claims_report", "scientific claims report", "optional",
     [".solaris_ai_nn_alpha/reports/SCIENTIFIC_CLAIM_REPORT.md"]),
    ("architecture_book", "architecture book", "optional",
     ["docs/whitepaper/ARCHITECTURE_BOOK.md", "docs/ARCHITECTURE.md"]),
    ("technical_whitepaper", "technical whitepaper", "optional",
     ["docs/whitepaper/TECHNICAL_WHITEPAPER.md"]),
    ("static_html_console", "static HTML console", "optional",
     ["{ts}/console/INDEX.html"]),
)


@dataclass
class TesterRCArtifactCollector:
    """Resolves bounded, local references to RC artifacts."""

    tester_state_dir: str = ".solaris_ai_nn_tester"
    include_optional: bool = True
    include_private_payloads: bool = False

    def collect(self) -> RCArtifactCollectionResult:
        ts = self.tester_state_dir
        subs = {"{ts}": ts, "{pkg}": os.path.join(ts, "packaging"),
                "{sf}": os.path.join(ts, "safety_freeze"),
                "{fb}": os.path.join(ts, "feedback")}
        result = RCArtifactCollectionResult()
        for key, label, tier, candidates in _SPECS:
            if tier == RCArtifactTier.OPTIONAL and not self.include_optional:
                continue
            resolved = ""
            present = False
            for cand in candidates:
                path = cand
                for token, value in subs.items():
                    path = path.replace(token, value)
                if os.path.isfile(path):
                    resolved, present = path, True
                    break
            if not resolved and candidates:
                # Record the canonical (first) candidate path even if absent.
                path = candidates[0]
                for token, value in subs.items():
                    path = path.replace(token, value)
                resolved = path
            result.artifacts.append(CollectedRCArtifact(
                key=key, label=label, tier=tier, path=resolved,
                present=present))
        return result
