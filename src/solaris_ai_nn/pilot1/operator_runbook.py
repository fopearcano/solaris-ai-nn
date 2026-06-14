"""Pilot-1 operator runbook -- the human-facing how-to for a long-horizon run.

The :class:`OperatorRunbookBuilder` writes ``OPERATOR_RUNBOOK.md``: what
Pilot-1 is (and is not), the preflight checklist, how to start each mode
(plan-only through 30-day real), how to read the dashboard, pause/resume,
perform restart drills, inspect reports/incidents, trigger safe shutdown and
the emergency stop, plus explicit warnings and artifact locations. It writes
guidance only; it starts nothing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .pilot_config import PilotConfig

WARNINGS = (
    "Do not call a simulated month a real month.",
    "Do not enable real-world actuation.",
    "Do not delete evidence manually during a run.",
    "Do not disable the emergency stop.",
    "Do not treat proto-language as human language.",
    "Do not treat a successful pilot as proof of consciousness.",
)


@dataclass
class OperatorRunbookBuilder:
    """Builds the Markdown operator runbook for Pilot-1."""

    base_dir: str = ".solaris_ai_nn_pilot1"

    def render(self, config: Optional[PilotConfig] = None) -> str:
        cfg = config or PilotConfig(base_dir=self.base_dir)
        env = cfg.environment()
        S = "solaris-nn run-profile"
        lines = [
            "# Pilot-1 Operator Runbook",
            "",
            "## Pilot-1 purpose",
            "Pilot-1 is the first serious long-horizon test frame for "
            "Solaris-AI-NN. Its goal is to find out whether, after a month of "
            "continuous bounded runtime, the system is structurally different "
            "for traceable reasons derived from its own runtime -- not merely "
            "accumulating logs.",
            "",
            "## What this test is NOT",
            "- It is not a claim of consciousness, sentience, or personhood.",
            "- It is not a real-world agent; there is no real-world actuation.",
            "- A simulated-time dry-run is not a real month and is never "
            "presented as one.",
            "- Operational success means a complete, analyzable developmental "
            "trace -- nothing more.",
            "",
            "## Preflight checklist",
            "1. Run the preflight profile and confirm it passes.",
            "2. Confirm governance scopes for the intended real mode.",
            "3. Confirm emergency stop is available and not disabled.",
            "4. Confirm disk/memory budget headroom.",
            "5. Confirm pilot directories exist and are writable.",
            "6. Review the simulated month dry-run before any real soak.",
            "",
            "## How to start plan-only mode",
            "```bash",
            "python examples/run_pilot1_plan.py "
            f"--output-dir {cfg.base_dir}/plan",
            f"{S} pilot1_plan_only   # via the conscience CLI",
            "```",
            "Plan-only writes the runbook, resource budget, and config "
            "template. It does not start a run.",
            "",
            "## How to start a 24h real soak",
            "```bash",
            "# Requires governance scope enable_pilot1_24h_real and a passing "
            "preflight.",
            f"{S} pilot1_24h_soak --governance-approved",
            "```",
            "",
            "## How to start a 7d real soak",
            "```bash",
            "# Requires governance scope enable_pilot1_7d_real.",
            f"{S} pilot1_7d_soak --governance-approved",
            "```",
            "",
            "## How to start a 30d real soak",
            "```bash",
            "# Requires governance scope enable_pilot1_30d_real, a passing "
            "preflight, a passed restart drill, and an operator decision.",
            f"{S} pilot1_30d_soak --governance-approved",
            "```",
            "",
            "## How to check the dashboard",
            f"Open `{cfg.base_dir}/dashboard.md` (or `dashboard.json`). It "
            "shows the current phase, uptime, module health, budgets, "
            "checkpoint status, and the latest incidents/signals.",
            "",
            "## How to pause safely",
            "Request a pause through the supervisor / safe-shutdown manager; "
            "the run halts at the next segment boundary. Never kill the "
            "process directly.",
            "",
            "## How to resume",
            "Restart the pilot; protocol state is restored from "
            f"`{cfg.base_dir}/pilot_protocol_state.json` and the restart "
            "counter is incremented. Identity continuity is checked.",
            "",
            "## How to perform a restart drill",
            "Use the restart-drill demo, or follow the manual steps: take a "
            "graceful checkpoint, stop the run, restart, and confirm identity "
            "continuity and checkpoint restore before resuming.",
            "",
            "## How to inspect the daily report",
            f"See `{cfg.base_dir}/daily/day_XXX.md` for the day's summary and "
            "recommended action.",
            "",
            "## How to inspect incidents",
            f"See `{cfg.base_dir}/incidents.jsonl` and the ops incident log. "
            "Safety incidents are always retained.",
            "",
            "## How to trigger a safe shutdown",
            "Ask the supervisor to request shutdown; it stops gracefully at "
            "the next segment boundary and writes a final snapshot.",
            "",
            "## Emergency stop procedure",
            f"Create the sentinel file `{env.state_dir}/EMERGENCY_STOP` (or "
            "call the emergency-stop control). The supervised run requests a "
            "graceful shutdown at the next boundary, records an incident and "
            "audit event, and writes a final health snapshot. The emergency "
            "stop is always available and is never permission-gated.",
            "",
            "## What NOT to do",
        ]
        lines += [f"- {w}" for w in WARNINGS]
        lines += [
            "",
            "## Artifact locations",
            f"- base: `{cfg.base_dir}`",
            f"- state: `{env.state_dir}`",
            f"- artifacts: `{env.artifact_dir}`",
            f"- logs: `{env.log_dir}`",
            f"- reports: `{env.report_dir}`",
            f"- observability: `{cfg.base_dir}/observability.jsonl`",
            f"- dashboard: `{cfg.base_dir}/dashboard.md`",
            f"- daily: `{cfg.base_dir}/daily/`",
            f"- weekly: `{cfg.base_dir}/weekly/`",
            f"- pilot report: `{cfg.base_dir}/PILOT_REPORT.md`",
            "",
            "## Post-run analysis checklist",
            "1. Confirm the pilot report generated and passed ClaimGuard.",
            "2. Compare day 1 vs day 7, week 1 vs week 4, baseline vs final.",
            "3. Separate structural change from mere accumulation.",
            "4. Review all safety/governance incidents and restart drills.",
            "5. Decide the next pilot recommendation.",
            "6. Remember: operational success is not consciousness proof.",
        ]
        return "\n".join(lines)

    def write(self, config: Optional[PilotConfig] = None) -> str:
        os.makedirs(self.base_dir, exist_ok=True)
        path = os.path.join(self.base_dir, "OPERATOR_RUNBOOK.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.render(config))
        return path
