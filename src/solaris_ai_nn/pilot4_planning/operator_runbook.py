"""Pilot-4 planning operator runbook -- how to plan the door, not open it.

The :class:`Pilot4PlanningRunbookBuilder` writes ``OPERATOR_RUNBOOK.md`` for the
Pilot-4 planning window: what Pilot-4 is for, why it is planning-only, what
real-world actuation would mean, forbidden actions, how to run the risk
assessment / generate the dossier / review the consent boundary and forbidden
registry and threat model, how to verify no actuation is enabled, what not to
connect, and how to archive. Planning is not approval.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

WARNINGS = (
    "Do not connect devices.",
    "Do not connect robots.",
    "Do not grant OS/browser/network control.",
    "Do not treat planning as approval.",
    "Do not treat simulation success as real-world readiness.",
    "Do not claim consciousness/agency.",
)

FORBIDDEN = (
    "real-world actuation of any kind",
    "device / robotics control",
    "browser control / OS automation",
    "network action / external APIs",
    "hardware access / hardware drivers",
    "shell command execution",
    "writing outside planning/state/artifact directories",
)


@dataclass
class Pilot4PlanningRunbookBuilder:
    base_dir: str = ".solaris_ai_nn_pilot4"

    def render(self, config: Optional[Any] = None) -> str:
        base = getattr(config, "base_dir", self.base_dir)
        S = "solaris-nn run-profile"
        lines = [
            "# Pilot-4 Planning Operator Runbook",
            "",
            "## Pilot-4 purpose",
            "Answer one question: *what would be required before Solaris-AI-NN "
            "could ever be allowed to act on the external world?* The output is "
            "a readiness framework, not an actuator.",
            "",
            "## Why Pilot-4 is planning-only",
            "Pilot-4 plans the door; it does not open it. It produces planning "
            "artifacts only: a risk model, consent boundary, authority model, "
            "threat model, hardware-isolation and emergency requirements, an "
            "audit schema, and a readiness dossier. It enables no actuation.",
            "",
            "## What real-world actuation would mean",
            "Acting on the external world (devices, robots, the network, the "
            "OS, a browser, files outside approved dirs, or any physical "
            "effect) is prohibited here and would require a future architecture "
            "with new governance, safety, consent, and external actuation "
            "controls.",
            "",
            "## Forbidden actions",
        ]
        lines += [f"- {f}" for f in FORBIDDEN]
        lines += [
            "",
            "## How to run the risk assessment",
            "```bash",
            f"{S} pilot4_risk_assessment",
            "python examples/run_pilot4_risk_assessment_demo.py",
            "```",
            "",
            "## How to generate the readiness dossier",
            "```bash",
            f"{S} pilot4_readiness_dossier",
            "python examples/run_pilot4_readiness_dossier_demo.py",
            "```",
            "",
            "## How to review the consent boundary",
            "Inspect the `consent_boundary` section of the readiness dossier: "
            "consent is explicit, recorded, and revocable; there is no implied "
            "consent, sensory text is never consent, and operator feedback is "
            "consent only via an explicit future approval workflow.",
            "",
            "## How to inspect the forbidden actuator registry",
            f"Open the `forbidden_actuator_registry` section of "
            f"`{base}/PILOT4_READINESS_DOSSIER.json`; it is a deny-list that "
            "blocks readiness escalation.",
            "",
            "## How to inspect the threat model",
            "Read the `threat_model` section: each scenario carries its "
            "affected boundary, severity, likelihood, mitigation, detection "
            "signal, and required test.",
            "",
            "## How to verify no actuation is enabled",
            f"Confirm `real_world_actuation_enabled` is false in "
            f"`{base}/pilot4_planning_state.json` and the dossier; confirm the "
            "current authority is none / dry_run_only / simulation_only.",
            "",
            "## What not to connect",
        ]
        lines += [f"- {w}" for w in WARNINGS]
        lines += [
            "",
            "## How to archive planning artifacts",
            f"Archive the dossier, risk model, and planning state under "
            f"`{base}/`; planning artifacts are read-only records, never "
            "approvals.",
        ]
        return "\n".join(lines)

    def write(self, config: Optional[Any] = None) -> str:
        os.makedirs(self.base_dir, exist_ok=True)
        path = os.path.join(self.base_dir, "OPERATOR_RUNBOOK.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.render(config))
        return path
