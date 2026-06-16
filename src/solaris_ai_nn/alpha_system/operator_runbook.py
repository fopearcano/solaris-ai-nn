"""Alpha operator runbook -- how to run the Alpha System, and what it is not.

:class:`AlphaRunbookBuilder` builds the operator runbook: what the Alpha Research
System is and is not, its safety boundaries, the step-by-step operator commands,
how to read the report and skipped modules, how to continue, the stop conditions,
and the forbidden interpretations. It states explicitly that alpha is local
research orchestration only -- not a product release, not consciousness/life
evidence, not autonomous self-improvement, and not hardware/feeder/Git/GitHub
control.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


_WHAT_IT_IS = (
    "Alpha is the unified local operator entry point that assembles the "
    "organismic, scientific, claim-governance, and review-governance modules "
    "into one bounded, fixture-only research run.",
)
_WHAT_IT_IS_NOT = (
    "alpha is not a product release",
    "alpha is not consciousness evidence",
    "alpha is not life evidence",
    "alpha is not autonomous self-improvement",
    "alpha does not control hardware or feeders",
    "alpha does not call Git or GitHub",
    "alpha is local research orchestration only",
)
_SAFETY_BOUNDARIES = (
    "no real-world actuation; no hardware/feeder control or auto-start",
    "no network/shell/browser/OS access",
    "no Git/GitHub call; no branch/tag/release/PR creation",
    "no upload; no publishing; no external agent execution",
    "bounded runtime; no unbounded loops; no source self-rewrite",
    "no consciousness/sentience/life/personhood/agency/free-will/emotion/"
    "feeling/understanding/self-awareness claim",
)
_STOP_CONDITIONS = (
    "doctor reports a blocker -> fix the blocker before running the demo",
    "a required alpha module is missing/blocked -> the command is blocked",
    "the state directory is not writable -> stop and choose another state dir",
    "an unsupported claim is detected in a report -> stop and review wording",
)
_FORBIDDEN_INTERPRETATIONS = (
    "do not read a completed demo as evidence of consciousness or life",
    "do not read sensorium-native signs as understanding or meaning",
    "do not read action-reaction traces as agency, intent, or free will",
    "do not read developmental growth as biological development",
    "do not treat the fixture debug gloss as ground truth",
    "do not treat any alpha output as a product release or a public claim",
)


@dataclass
class AlphaRunbookStep:
    """One runbook step (an operator instruction; never executed by the system)."""

    title: str
    command: str = ""
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"title": self.title, "command": self.command,
                "detail": self.detail, "executed": False}


@dataclass
class AlphaOperatorRunbook:
    """The assembled operator runbook."""

    state_root: str
    steps: List[AlphaRunbookStep] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state_root": self.state_root,
            "what_it_is": list(_WHAT_IT_IS),
            "what_it_is_not": list(_WHAT_IT_IS_NOT),
            "safety_boundaries": list(_SAFETY_BOUNDARIES),
            "steps": [s.to_dict() for s in self.steps],
            "stop_conditions": list(_STOP_CONDITIONS),
            "forbidden_interpretations": list(_FORBIDDEN_INTERPRETATIONS),
            "note": "the runbook is operator instructions only; the system "
                    "executes no command on the operator's behalf",
        }

    def render_md(self) -> str:
        d = self.to_dict()
        lines = ["# Alpha Operator Runbook", "",
                 "## What the Alpha Research System is", ""]
        lines += [f"- {x}" for x in d["what_it_is"]]
        lines += ["", "## What it is NOT", ""]
        lines += [f"- {x}" for x in d["what_it_is_not"]]
        lines += ["", "## Safety boundaries", ""]
        lines += [f"- {x}" for x in d["safety_boundaries"]]
        lines += ["", "## Operator steps", ""]
        for s in self.steps:
            lines.append(f"### {s.title}")
            if s.command:
                lines.append(f"```\n{s.command}\n```")
            if s.detail:
                lines.append(s.detail)
            lines.append("")
        lines += ["## How to interpret skipped modules", "",
                  "Skipped modules mean an optional module was not present; the "
                  "demo records them honestly and continues. A skipped module is "
                  "not a failure and is never hidden.", ""]
        lines += ["## How to read the alpha report", "",
                  "The alpha report lists the profile, the module registry, the "
                  "demo results (completed / skipped / blocked), the artifact "
                  "index, the cycle status, the next action, and the safety "
                  "boundaries. Read skipped modules and blockers first.", ""]
        lines += ["## Stop conditions", ""]
        lines += [f"- {x}" for x in d["stop_conditions"]]
        lines += ["", "## Forbidden interpretations", ""]
        lines += [f"- {x}" for x in d["forbidden_interpretations"]]
        lines += ["", "_Alpha is local research orchestration only: no product "
                  "release, no consciousness/life/agency evidence, no hardware/"
                  "feeder control, and no Git/GitHub operation._"]
        return "\n".join(lines)


@dataclass
class AlphaRunbookBuilder:
    """Builds the operator runbook for a given state root."""

    def build(self, state_root: str) -> AlphaOperatorRunbook:
        steps = [
            AlphaRunbookStep(
                "Initialize alpha state",
                f"python -m solaris_ai_nn init --state-dir {state_root}",
                "Creates the local alpha state directory tree (reuses existing; "
                "never deletes)."),
            AlphaRunbookStep(
                "Run doctor",
                f"python -m solaris_ai_nn doctor --state-dir {state_root}",
                "Runs the read-only system check; fix any blocker before "
                "continuing."),
            AlphaRunbookStep(
                "Inspect modules",
                f"python -m solaris_ai_nn modules --state-dir {state_root}",
                "Prints the module registry; missing optional modules warn."),
            AlphaRunbookStep(
                "Run the end-to-end fixture demo",
                f"python -m solaris_ai_nn run-demo --state-dir {state_root} "
                "--max-ticks 25",
                "Runs the bounded, fixture-only end-to-end demo."),
            AlphaRunbookStep(
                "Inspect the artifact index",
                f"python -m solaris_ai_nn artifact-index --state-dir "
                f"{state_root}",
                "Lists local artifacts and missing/skipped markers."),
            AlphaRunbookStep(
                "Read the cycle status",
                f"python -m solaris_ai_nn cycle-status --state-dir {state_root}",
                "Shows the current alpha stage and the advisory next action."),
            AlphaRunbookStep(
                "Continue to the next research cycle",
                "",
                "When ready, the operator may proceed to architecture evolution "
                "or the next prompt. No step is executed automatically."),
        ]
        return AlphaOperatorRunbook(state_root=state_root, steps=steps)
