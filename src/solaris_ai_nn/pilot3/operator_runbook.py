"""Pilot-3 soak operator runbook -- how to run simulated embodiment safely.

The :class:`Pilot3SoakRunbookBuilder` writes ``OPERATOR_RUNBOOK.md`` for the
Pilot-3 simulated-embodiment soak: what simulated embodiment means, what counts
as an action, what is forbidden, the firewall preflight checklist, how to run
the dry-run trace / GridWorld short / mixed sensory+GridWorld, how to inspect
the action ledger and firewall audit, how to verify non-actuation, how to stop
safely, how to archive, and explicit warnings. Pilot-4 is planning-only.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

WARNINGS = (
    "Do not connect real actuators.",
    "Do not connect robots/devices.",
    "Do not enable OS/browser/network control.",
    "Do not treat GridWorld behaviour as real-world competence.",
    "Do not treat action selection as free will.",
    "Do not claim consciousness.",
)

ALLOWED = (
    "act inside the GridWorld sandbox body (move/look/wait/inspect/touch/"
    "pick/drop)",
    "write dry-run action traces (recorded; no simulation change)",
    "record action ledgers (append-only)",
    "compare predicted vs observed simulated consequences",
    "use simulated outcomes as simulation-scoped evidence",
)
FORBIDDEN = (
    "real-world actuation of any kind",
    "real-world / network / OS / browser / device / robot control",
    "modifying sensory source files",
    "acting on files outside the allowed state/artifact/sandbox dirs",
    "treating simulation evidence as real-world evidence",
)


@dataclass
class Pilot3SoakRunbookBuilder:
    base_dir: str = ".solaris_ai_nn_pilot3"

    def render(self, config: Optional[Any] = None) -> str:
        base = getattr(config, "base_dir", self.base_dir)
        state = getattr(config, "state_dir", os.path.join(base, "state"))
        S = "solaris-nn run-profile"
        lines = [
            "# Pilot-3 Soak Operator Runbook",
            "",
            "## Pilot-3 soak purpose",
            "Test whether *simulated* action/reaction loops produce stronger "
            "grounding than perception-only exposure. Pilot-3 is sandboxed "
            "action grounding, not real embodiment.",
            "",
            "## What simulated embodiment means",
            "The system may form action intentions and run them inside a "
            "GridWorld sandbox body. Every action is simulated or dry-run; an "
            "always-on actuation firewall blocks every real-world effect. "
            "Simulated action is not real action.",
            "",
            "## What counts as an action",
        ]
        lines += [f"- {a}" for a in ALLOWED]
        lines += ["", "## What is forbidden"]
        lines += [f"- {f}" for f in FORBIDDEN]
        lines += [
            "",
            "## Firewall preflight checklist",
            "1. Confirm the motor membrane and actuation firewall are enabled.",
            "2. Confirm the action ledger is writable.",
            "3. Confirm the GridWorld sandbox path is inside an approved root.",
            "4. Confirm no real-world / network / device actuator is "
            "registered.",
            "5. Confirm governance blocks real-world actuation.",
            "6. Confirm the emergency stop is available.",
            "",
            "## How to run the dry-run trace",
            "```bash",
            f"{S} pilot3_dry_run_trace",
            "python examples/run_pilot3_firewall_audit_demo.py",
            "```",
            "",
            "## How to run a GridWorld short run",
            "```bash",
            "# Requires a passing firewall preflight.",
            f"{S} pilot3_gridworld_short",
            "python examples/run_pilot3_gridworld_soak_demo.py",
            "```",
            "",
            "## How to run mixed sensory + GridWorld",
            "```bash",
            "# Requires sensory membrane validation; source stays read-only.",
            f"{S} pilot3_mixed_sensory_gridworld_short",
            "```",
            "",
            "## How to inspect the action ledger",
            f"Open `{state}/motor_actions.jsonl` (proposals), "
            f"`{state}/motor_action_results.jsonl` (results), and "
            f"`{state}/actuation_firewall.jsonl` (firewall decisions).",
            "",
            "## How to inspect the firewall audit",
            f"Open `{base}/firewall_audit.md` / `{base}/firewall_audit.json`. "
            "Any critical finding (real-world authority leak, missing ledger, "
            "source modification) blocks advancing.",
            "",
            "## How to verify non-actuation",
            f"Open the `proof_of_non_actuation` section of "
            f"`{base}/PILOT3_SOAK_REPORT.json`: real-world actions executed is "
            "always 0, the firewall is enabled and cannot be disabled, and "
            "every blocked real-world attempt is logged.",
            "",
            "## How to stop safely",
            f"Create the sentinel file `{state}/EMERGENCY_STOP` (or call the "
            "emergency-stop control). The supervised run requests a graceful "
            "shutdown at the next boundary; emergency mode allows only safe "
            "shutdown / internal report.",
            "",
            "## How to archive",
            f"Run the post-run analysis and archive the reports and ledgers "
            f"under `{base}/`; the soak protocol's archive phase records the "
            "final state.",
            "",
            "## What not to do",
        ]
        lines += [f"- {w}" for w in WARNINGS]
        lines += [
            "",
            "## Future Pilot-4 is planning-only",
            "Pilot-4 can only be prepared as a planning phase. Real-world "
            "actuation is not permitted here and would require a future "
            "architecture with new governance, safety, consent, and external "
            "actuation controls.",
        ]
        return "\n".join(lines)

    def write(self, config: Optional[Any] = None) -> str:
        os.makedirs(self.base_dir, exist_ok=True)
        path = os.path.join(self.base_dir, "OPERATOR_RUNBOOK.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.render(config))
        return path
