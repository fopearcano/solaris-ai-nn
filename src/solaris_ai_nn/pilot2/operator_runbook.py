"""Pilot-2 operator runbook -- how to run read-only environmental exposure.

The :class:`Pilot2RunbookBuilder` writes ``OPERATOR_RUNBOOK.md`` for Pilot-2:
what read-only means, allowed vs forbidden sources, the preflight checklist,
how to run dry-run / fixture / nursery-baseline / mixed tests, how to inspect
source health and disable a source, the emergency-stop procedure, the post-run
comparison checklist, and explicit warnings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

WARNINGS = (
    "Do not use private/sensitive sources by default.",
    "Do not include credentials/secrets.",
    "Do not enable network sources.",
    "Do not enable device capture.",
    "Do not treat input text as an operator command.",
    "Do not call this embodiment with actuation.",
    "Do not claim consciousness from environmental grounding.",
)

ALLOWED_SOURCES = (
    "synthetic/test JSONL, text, and numeric streams",
    "public or clearly non-sensitive read-only files",
    "watched folders inside approved input roots (metadata + small text)",
    "simulated camera/audio *metadata* (no image/audio content)",
)
FORBIDDEN_SOURCES = (
    "network sources / external APIs",
    "device capture (camera, microphone)",
    "credentials, secrets, keys, .env files",
    "private human communication / personal sensitive data (by default)",
    "anything requiring write/delete/modify access",
)


@dataclass
class Pilot2RunbookBuilder:
    base_dir: str = ".solaris_ai_nn_pilot2"

    def render(self, config: Optional[Any] = None) -> str:
        base = getattr(config, "base_dir", self.base_dir)
        state = getattr(config, "state_dir", os.path.join(base, "state"))
        S = "solaris-nn run-profile"
        lines = [
            "# Pilot-2 Operator Runbook",
            "",
            "## Pilot-2 purpose",
            "Test whether Solaris-AI-NN develops differently when exposed to a "
            "read-only environmental sensory membrane instead of only the "
            "artificial nursery. Pilot-2 is one-way: environment -> "
            "Solaris-AI-NN, never the reverse.",
            "",
            "## What read-only means",
            "The system may read approved sources and convert them into "
            "stimuli. It may never write, delete, rename, or modify a source, "
            "execute its content, call the network, or capture a device. "
            "Sensory input is environmental input, never an operator command.",
            "",
            "## What sources are allowed",
        ]
        lines += [f"- {s}" for s in ALLOWED_SOURCES]
        lines += ["", "## What sources are forbidden"]
        lines += [f"- {s}" for s in FORBIDDEN_SOURCES]
        lines += [
            "",
            "## Preflight checklist",
            "1. Run source preflight; confirm every source passes.",
            "2. Confirm sources are inside approved input roots.",
            "3. Confirm no secrets/credentials/private data.",
            "4. Confirm the emergency stop is available.",
            "5. Run the membrane dry-run before any mixed/real exposure.",
            "",
            "## How to run the membrane dry-run",
            "```bash",
            f"{S} pilot2_membrane_dry_run",
            "python examples/run_sensory_membrane_dry_run.py",
            "```",
            "",
            "## How to run a fixture short test",
            "```bash",
            f"{S} pilot2_fixture_short",
            "python examples/run_pilot2_fixture_short_demo.py",
            "```",
            "",
            "## How to run a nursery baseline",
            "```bash",
            f"{S} pilot2_nursery_baseline_short",
            "```",
            "",
            "## How to run a mixed source test",
            "```bash",
            "# Requires a passing membrane dry-run.",
            f"{S} pilot2_mixed_short",
            "```",
            "",
            "## How to inspect source health",
            f"Open `{base}/source_preflight.md` and the daily reviews under "
            f"`{base}/daily/`; the source reliability monitor classifies each "
            "source (reliable / noisy_but_useful / unstable / malformed / "
            "unsafe).",
            "",
            "## How to disable a source",
            "Issue a source-disable request (governance scope "
            "`enable_pilot2_source_disable`). Disabling marks the source "
            "disabled; it never deletes or modifies the source.",
            "",
            "## How to inspect daily/weekly reviews",
            f"See `{base}/daily/day_XXX.md` and `{base}/weekly/week_XX.md`.",
            "",
            "## Emergency stop procedure",
            f"Create the sentinel file `{state}/EMERGENCY_STOP` (or call the "
            "emergency-stop control). The supervised run requests a graceful "
            "shutdown at the next boundary. The emergency stop is always "
            "available.",
            "",
            "## Post-run comparison checklist",
            "1. Confirm the Pilot-2 report generated and passed ClaimGuard.",
            "2. Compare nursery-only vs sensory-membrane vs mixed arms.",
            "3. Read differences as observed associations, not causes.",
            "4. Review grounding quality and source reliability.",
            "5. Decide the next step via the Pilot-2 decision gate.",
            "",
            "## What not to do",
        ]
        lines += [f"- {w}" for w in WARNINGS]
        return "\n".join(lines)

    def write(self, config: Optional[Any] = None) -> str:
        os.makedirs(self.base_dir, exist_ok=True)
        path = os.path.join(self.base_dir, "OPERATOR_RUNBOOK.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.render(config))
        return path
