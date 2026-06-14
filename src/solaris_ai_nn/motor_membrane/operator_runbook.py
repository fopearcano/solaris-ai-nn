"""Pilot-3 operator runbook -- how to run simulated/dry-run embodiment safely.

The :class:`Pilot3RunbookBuilder` writes ``OPERATOR_RUNBOOK.md``: what the
motor membrane and actuation firewall mean, what is allowed vs forbidden, how
to run the firewall preflight / dry-run trace / gridworld short, how to inspect
the action ledger and vetoes, how to prove non-actuation, and explicit
warnings. Real-world actuation is out of scope.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

WARNINGS = (
    "Do not connect robots/devices.",
    "Do not enable browser/OS automation.",
    "Do not grant network action.",
    "Do not treat simulated actions as real actions.",
    "Do not treat action selection as free will.",
    "Do not claim consciousness from simulated embodiment.",
)

ALLOWED = (
    "simulated GridWorld actions (move/look/wait/inspect/touch/pick/drop)",
    "internal actions (request consolidation/replay/report/checkpoint)",
    "dry-run action proposals (recorded, no simulation change)",
)
FORBIDDEN = (
    "real-world actuation of any kind",
    "device / robotics control",
    "browser control / OS automation",
    "network action",
    "command execution",
    "modifying sensory sources or files outside the sandbox",
)


@dataclass
class Pilot3RunbookBuilder:
    base_dir: str = ".solaris_ai_nn_pilot3"

    def render(self, config: Optional[Any] = None) -> str:
        S = "solaris-nn run-profile"
        lines = [
            "# Pilot-3 Operator Runbook",
            "",
            "## Pilot-3 purpose",
            "Pilot-3 adds the *outbound* boundary: a motor membrane that lets "
            "Solaris-AI-NN form action intentions and run them only inside a "
            "sandbox. It is the mirror of Pilot-2's read-only input membrane.",
            "",
            "## What the motor membrane means",
            "Solaris-AI-NN may form action intentions, simulate their "
            "consequences, write action traces, and act inside sandbox worlds "
            "-- but it may not act on the real world.",
            "",
            "## What the actuation firewall means",
            "Every motor action passes through an always-on firewall before "
            "any (simulated) execution. The firewall blocks all real-world "
            "effects and cannot be disabled by runtime modules; any blocked "
            "real-world attempt becomes a safety incident.",
            "",
            "## What is allowed",
        ]
        lines += [f"- {a}" for a in ALLOWED]
        lines += ["", "## What is forbidden"]
        lines += [f"- {f}" for f in FORBIDDEN]
        lines += [
            "",
            "## How to run the firewall preflight",
            "```bash",
            f"{S} motor_firewall_preflight",
            "python examples/run_motor_firewall_preflight_demo.py",
            "```",
            "",
            "## How to run a dry-run motor trace",
            "```bash",
            f"{S} dry_run_motor_trace",
            "python examples/run_dry_run_motor_trace_demo.py",
            "```",
            "",
            "## How to run a gridworld short",
            "```bash",
            f"{S} gridworld_motor_short",
            "python examples/run_gridworld_motor_demo.py",
            "```",
            "",
            "## How to inspect the action ledger",
            f"Open `{self.base_dir}/../.solaris_ai_nn_state/motor_actions.jsonl`"
            " (every proposal), `motor_action_results.jsonl` (simulated "
            "results), and `actuation_firewall.jsonl` (firewall decisions).",
            "",
            "## How to inspect vetoes",
            "Vetoes appear in the action ledger, the Pilot-3 report, and the "
            "Inner MAP; a forbidden real-world veto is final.",
            "",
            "## How to prove non-actuation",
            "The Pilot-3 report's 'proof of non-actuation' section shows "
            "real_world_authority=false, blocked real-world attempts, and zero "
            "real-world actions executed.",
            "",
            "## How to safe shutdown",
            "Request safe shutdown / set the emergency-stop sentinel; emergency "
            "mode stops all action execution except internal report/rest.",
            "",
            "## What not to do",
        ]
        lines += [f"- {w}" for w in WARNINGS]
        lines += [
            "",
            "## Future real-world actuation is out of scope",
            "Whether Solaris-AI-NN should ever act on a real environment is a "
            "separate question this prompt does not open. Pilot-3 measures "
            "only whether simulated action/reaction changes development.",
        ]
        return "\n".join(lines)

    def write(self, config: Optional[Any] = None) -> str:
        os.makedirs(self.base_dir, exist_ok=True)
        path = os.path.join(self.base_dir, "OPERATOR_RUNBOOK.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.render(config))
        return path
