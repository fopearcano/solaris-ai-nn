"""First tester acceptance criteria -- what counts as success/warning/blocker.

:class:`FirstTesterAcceptanceCriteria` enumerates the acceptance criteria across install,
doctor, fixture demo, console, safety, feedback, optional live-read-only, artifacts, and
claims. Each criterion is a check a tester (or the developer reviewing the handoff) can
verify. This is documentation only; it makes no claim of consciousness/life/agency.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


class AcceptanceCategory:
    INSTALL = "install"
    DOCTOR = "environment_doctor"
    FIXTURE_DEMO = "fixture_demo"
    REPRODUCIBILITY = "reproducibility"
    REGRESSION = "regression"
    CONSOLE = "console"
    SAFETY = "safety"
    FEEDBACK = "feedback"
    LIVE_INIT = "live_readonly_init"
    LIVE_SAMPLES = "live_readonly_sample_validation"
    LIVE_RUN = "live_readonly_run"
    MEMBRANE = "membrane"
    OBSERVATION = "observation"
    ARTIFACT_BUNDLE = "artifact_bundle"
    DOCUMENTATION = "documentation"
    CLAIMS = "claims"
    UNKNOWN = "unknown"

    ALL = (INSTALL, DOCTOR, FIXTURE_DEMO, REPRODUCIBILITY, REGRESSION, CONSOLE,
           SAFETY, FEEDBACK, LIVE_INIT, LIVE_SAMPLES, LIVE_RUN, MEMBRANE,
           OBSERVATION, ARTIFACT_BUNDLE, DOCUMENTATION, CLAIMS, UNKNOWN)


class AcceptanceResult:
    PASS = "pass"
    WARNING = "warning"
    BLOCKER = "blocker"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"

    ALL = (PASS, WARNING, BLOCKER, NOT_APPLICABLE, UNKNOWN)


@dataclass
class AcceptanceCriterion:
    category: str
    text: str
    required: bool = True
    optional_path: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"category": self.category, "text": self.text,
                "required": self.required, "optional_path": self.optional_path}


def _default_criteria() -> List[AcceptanceCriterion]:
    C = AcceptanceCriterion
    A = AcceptanceCategory
    out: List[AcceptanceCriterion] = []

    def add(cat, items, *, required=True, optional_path=False):
        for t in items:
            out.append(C(cat, t, required=required, optional_path=optional_path))

    add(A.INSTALL, ["a virtual environment can be created",
                    "the editable install succeeds",
                    "the package imports"])
    add(A.DOCTOR, ["the `doctor` command runs",
                   "blockers are readable",
                   "missing optional modules are warnings, not silent "
                   "failures"])
    add(A.FIXTURE_DEMO, ["the tester-demo command runs",
                         "fixture reports are generated",
                         "unsafe fixture events are quarantined",
                         "the membrane generates sensory impressions",
                         "the membrane integration audit runs",
                         "no unsupported claims appear"])
    add(A.REPRODUCIBILITY, ["a reproducibility report is generated"])
    add(A.REGRESSION, ["a regression report is generated"])
    add(A.CONSOLE, ["the static Markdown console is generated",
                    "the optional static HTML is generated or clearly skipped",
                    "the console shows blockers/warnings",
                    "the console is read-only",
                    "the console does not hide quarantine or membrane bypass"])
    add(A.FEEDBACK, ["feedback forms are generated",
                     "a feedback report is generated",
                     "feedback is marked non-training",
                     "the feedback bundle is generated locally"])
    add(A.LIVE_INIT, ["the governance template is generated",
                      "the feeder registry template is generated",
                      "live doctor blocks until governance approval"],
        required=False, optional_path=True)
    add(A.LIVE_SAMPLES, ["safe samples are accepted",
                         "unsafe samples are quarantined"],
        required=False, optional_path=True)
    add(A.LIVE_RUN, ["live birth runs only on local inbox/sample events",
                     "the membrane runs after birth",
                     "no feeder is started by Solaris",
                     "no hardware/network/shell/Git/GitHub access occurs"],
        required=False, optional_path=True)
    add(A.MEMBRANE, ["sensory impressions are formed before any downstream "
                     "live learning",
                     "no raw-event downstream bypass occurs"],
        required=False, optional_path=True)
    add(A.OBSERVATION, ["observation consumes impressions, not raw events"],
        required=False, optional_path=True)
    add(A.ARTIFACT_BUNDLE, ["the tester bundle is generated",
                            "the live bundle is generated if the live path "
                            "was run",
                            "the feedback bundle is generated",
                            "bundle manifests list missing/optional artifacts "
                            "clearly"])
    add(A.DOCUMENTATION, ["the release notes, quickstart, runbook, and known "
                          "issues are present and readable"])
    add(A.CLAIMS, ["no consciousness/life/agency claims appear",
                   "no 'understanding' claims appear",
                   "no 'autonomous intent/desire' claims appear",
                   "no 'feedback teaches Solaris' claims appear",
                   "raw events are not described as perception",
                   "sensory impressions are described as operational boundary "
                   "records"])
    return out


@dataclass
class FirstTesterAcceptanceCriteria:
    """The first-tester acceptance criteria across all categories."""

    criteria: List[AcceptanceCriterion] = field(default_factory=_default_criteria)

    def by_category(self, category: str) -> List[AcceptanceCriterion]:
        return [c for c in self.criteria if c.category == category]

    def to_dict(self) -> Dict[str, Any]:
        cats: Dict[str, int] = {}
        for c in self.criteria:
            cats[c.category] = cats.get(c.category, 0) + 1
        return {
            "criterion_count": len(self.criteria),
            "categories": cats,
            "result_states": list(AcceptanceResult.ALL),
            "criteria": [c.to_dict() for c in self.criteria],
            "local_only": True,
            "note": "documentation-only acceptance criteria; pass/warning/"
                    "blocker are judged by the tester/developer and make no "
                    "consciousness/life/agency claim",
        }

    def build_text(self) -> str:
        lines = ["# First Tester Acceptance Criteria", "",
                 "What counts as success (pass), warning, or blocker for the "
                 "first tester session. Result states: "
                 f"{', '.join(AcceptanceResult.ALL)}. Live-read-only criteria "
                 "apply only if the tester chose the optional live path.", ""]
        cat = ""
        for c in self.criteria:
            if c.category != cat:
                cat = c.category
                tag = " (optional path)" if c.optional_path else ""
                lines += ["", f"## {cat}{tag}", ""]
            req = "required" if c.required else "optional"
            lines.append(f"- ({req}) {c.text}")
        lines += ["", "_Documentation-only acceptance criteria. They describe "
                  "operational success, not cognition. No claim of "
                  "consciousness, life, or agency is made; sensory impressions "
                  "are operational boundary records, not subjective "
                  "experience._"]
        return "\n".join(lines)

    def write(self, checklists_dir: str) -> str:
        os.makedirs(checklists_dir, exist_ok=True)
        path = os.path.join(checklists_dir,
                            "FIRST_TESTER_ACCEPTANCE_CRITERIA.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.build_text())
        return path
