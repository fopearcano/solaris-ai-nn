"""Runbooks -- the written procedure a human follows for each experiment type.

A runbook is a deterministic Markdown document: purpose, required permissions,
risk level, pre-run checklist, launch command, monitoring, expected artifacts,
emergency stop procedure, post-run review, rollback (where plasticity is
involved), and known limitations. Generating one is free; running without one
shouldn't be.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from .checklists import (
    long_soak_checklist,
    plasticity_checklist,
    post_run_checklist,
    pre_run_checklist,
    sidecar_checklist,
)
from .permissions import PermissionScope as S
from .risk import RiskLevel

RUNBOOK_TYPES = ("bounded", "plasticity", "sidecar", "sensorimotor",
                 "soak24", "soak30",
                 # Pilot-0 deployment profiles (Prompt 13).
                 "pilot_simulated", "pilot_stream", "pilot_sidecar")

_EMERGENCY_PROCEDURE = [
    "Create the sentinel file `<state_dir>/EMERGENCY_STOP` (any content). "
    "The supervisor requests safe shutdown at the next segment boundary.",
    "Alternatively call `EmergencyStop.request(reason, operator)` and "
    "`perform(supervisor)` from a Python shell.",
    "Never kill the process: the stop path checkpoints first and records "
    "why it stopped.",
    "After the run has stopped, read `incidents.jsonl` and the governance "
    "audit, then remove the sentinel deliberately "
    "(`EmergencyStop.clear_sentinel()`).",
]

_ROLLBACK_PROCEDURE = [
    "Identify the step to undo in `plasticity_audit.jsonl` (event_type "
    "`applied`).",
    "Call `engine.rollback(step_id)` (or `engine.rollback_last()`); the "
    "rollback is verified and audited.",
    "For a stopped run, rebuild rollback records first with "
    "`engine.load_history_from_audit()`.",
    "Confirm the restored value in `engine.snapshot()['current_parameters']`.",
]


@dataclass
class Runbook:
    """One generated runbook document."""

    runbook_type: str
    title: str
    sections: List[Tuple[str, List[str]]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_markdown(self) -> str:
        lines = [f"# Runbook: {self.title}", "",
                 f"Type: `{self.runbook_type}` -- generated, deterministic; "
                 "edit deliberately or regenerate.", ""]
        for heading, rows in self.sections:
            lines.append(f"## {heading}")
            for row in rows:
                lines.append(f"- {row}")
            lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "runbook_type": self.runbook_type,
            "title": self.title,
            "created_at": self.created_at,
            "sections": [{"heading": h, "items": list(rows)}
                         for h, rows in self.sections],
        }

    def save(self, path: Union[str, Path]) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_markdown(), encoding="utf-8")
        return path


@dataclass
class RunbookBuilder:
    """Builds the canonical runbook for each experiment type."""

    def build(self, runbook_type: str) -> Runbook:
        if runbook_type not in RUNBOOK_TYPES:
            raise ValueError(f"unknown runbook type {runbook_type!r}; "
                             f"choose from {RUNBOOK_TYPES}")
        builder = getattr(self, f"_build_{runbook_type}")
        return builder()

    # -- shared pieces ---------------------------------------------------------

    @staticmethod
    def _checklist_rows(checklist) -> List[str]:
        return [f"[ ] {item.description}" for item in checklist.items]

    @staticmethod
    def _monitoring_rows() -> List[str]:
        return [
            "Watch `health.jsonl` between segments; warnings name the "
            "domain that crossed a threshold.",
            "Watch `incidents.jsonl`; every entry has a suggested debug "
            "step.",
            "Check the watchdog snapshot in `status.json` "
            "(stop_requested / recent decisions).",
            "If the optional status server is enabled, poll "
            "`http://127.0.0.1:<port>/status` (read-only).",
        ]

    @staticmethod
    def _artifact_rows(extra: List[str] = ()) -> List[str]:
        rows = [
            "`<artifact_dir>/runs/<run_id>/manifest.json`, `status.json`, "
            "`status.md`, `health.jsonl`, `incidents.jsonl`, "
            "`shutdown.json`, `final_report.md`",
            "`<state_dir>/latest_checkpoint.json` (and the continuity log)",
            "`.solaris_ai_nn_governance/` -- governance audit, approvals, "
            "risk assessment, checklists, post-run review",
        ]
        rows.extend(extra)
        return rows

    def _runbook(self, runbook_type: str, title: str, purpose: List[str],
                 permissions: List[str], risk: str, launch: List[str],
                 extra_pre: List[str] = (),
                 extra_artifacts: List[str] = (),
                 include_rollback: bool = False,
                 limitations: List[str] = ()) -> Runbook:
        sections: List[Tuple[str, List[str]]] = [
            ("Purpose", purpose),
            ("Required permissions",
             [f"`{p}`" for p in permissions] or ["defaults only"]),
            ("Risk level", [f"expected overall level: **{risk}**",
                            "prohibited blocks; high needs approval; medium "
                            "needs operator acknowledgement; low is logged"]),
            ("Pre-run checklist",
             list(extra_pre) + self._checklist_rows(pre_run_checklist())),
            ("Launch command", [f"`{cmd}`" for cmd in launch]),
            ("Monitoring checklist", self._monitoring_rows()),
            ("Expected artifacts", self._artifact_rows(list(extra_artifacts))),
            ("Emergency stop procedure", list(_EMERGENCY_PROCEDURE)),
            ("Post-run review checklist",
             self._checklist_rows(post_run_checklist())
             + ["Write the PostRunReview and pick a next-run "
                "recommendation."]),
        ]
        if include_rollback:
            sections.append(("Rollback procedure (plasticity)",
                             list(_ROLLBACK_PROCEDURE)))
        sections.append(("Known limitations", list(limitations) + [
            "This is a research instrument; no consciousness claim is made "
            "or supported.",
            "Approvals are local research records, not security controls.",
        ]))
        return Runbook(runbook_type=runbook_type, title=title,
                       sections=sections)

    # -- per-type builders --------------------------------------------------------

    def _build_bounded(self) -> Runbook:
        return self._runbook(
            "bounded", "Bounded experiment",
            ["Run a short, fully bounded supervised session to validate "
             "learning, continuity, and health under governance."],
            [S.RUN_BOUNDED], RiskLevel.LOW,
            ["python examples/run_governed_bounded_experiment.py "
             "--steps 100 --operator <name>"],
            limitations=["Short runs say little about long-run stability; "
                         "use the soak runbooks for that."])

    def _build_plasticity(self) -> Runbook:
        return self._runbook(
            "plasticity", "Plasticity experiment",
            ["Let the controlled plasticity engine adapt runtime parameters "
             "under safety validation, audit, and rollback."],
            [S.RUN_BOUNDED, S.ENABLE_PLASTICITY,
             S.ENABLE_PLASTICITY_DRY_RUN,
             f"{S.ENABLE_PLASTICITY_APPLY} (approval required for active "
             "mutations)"],
            RiskLevel.HIGH,
            ["python examples/run_governed_plasticity_request.py",
             "python examples/run_governed_bounded_experiment.py --steps 200 "
             "--enable-plasticity-dry-run"],
            extra_pre=self._checklist_rows(plasticity_checklist()),
            extra_artifacts=["`<state_dir>/plasticity_audit.jsonl` -- every "
                             "proposal, rejection, application, rollback"],
            include_rollback=True,
            limitations=["Plasticity only tunes whitelisted numeric "
                         "parameters within SAFE_BOUNDS; it never edits "
                         "code."])

    def _build_sidecar(self) -> Runbook:
        return self._runbook(
            "sidecar", "Sidecar observation",
            ["Attach the NN sidecar beside a Solaris_Ai runtime, observe its "
             "bus, and (only with approval) publish suggestions."],
            [S.RUN_BOUNDED, S.ENABLE_SIDECAR_OBSERVE,
             f"{S.ENABLE_SIDECAR_SUGGESTIONS} (approval required to "
             "publish)"],
            RiskLevel.MEDIUM,
            ["python examples/run_solaris_sidecar_observation.py",
             "python examples/run_fake_solaris_integration.py"],
            extra_pre=self._checklist_rows(sidecar_checklist()),
            extra_artifacts=["`<state_dir>/integration_state.json`, "
                             "`suggestions.jsonl`, `mirrored_signals.jsonl`"],
            limitations=["The sidecar never commits Actions and never "
                         "touches the Solaris_Ai lifecycle; Solaris_Ai "
                         "remains the action authority."])

    def _build_sensorimotor(self) -> Runbook:
        return self._runbook(
            "sensorimotor", "Sensorimotor simulation",
            ["Run the simulated body in the bounded GridWorld and study the "
             "perceive/act/learn loop. Simulation-only, always."],
            [S.RUN_BOUNDED, S.ENABLE_EMBODIMENT_SIMULATION],
            RiskLevel.MEDIUM,
            ["python examples/run_governed_bounded_experiment.py --steps 200 "
             "--embodied",
             "python examples/run_sensorimotor_gridworld.py --steps 300"],
            extra_artifacts=["embodiment state inside the session "
                             "checkpoint (body, world, energy)"],
            limitations=["The body exists only in the GridWorld; every "
                         "action passes EmbodimentSafety, which forbids "
                         "anything real-world shaped."])

    def _soak(self, runbook_type: str, label: str, scope: str,
              mode: str) -> Runbook:
        return self._runbook(
            runbook_type, f"{label} soak",
            [f"Run a supervised {label} soak to study long-run continuity, "
             "health, and artifact growth. Long soaks are opt-in and "
             "approval-gated."],
            [scope, S.PERFORM_ARTIFACT_ROTATION], RiskLevel.HIGH,
            [f"python - <<'PY'  # soaks are launched from code, deliberately",
             "from solaris_ai_nn.ops import OperationalRunManifest, "
             "OperationalSupervisor",
             f"manifest = OperationalRunManifest(mode='{mode}', "
             "soak_acknowledged=True, max_steps=None)",
             "OperationalSupervisor(manifest=manifest).run()", "PY"],
            extra_pre=self._checklist_rows(long_soak_checklist()),
            extra_artifacts=["rotated archives under the artifact "
                             "directory (rotation keeps incident "
                             "evidence)"],
            limitations=["Tests must simulate soak durations; never block a "
                         "test suite on real days.",
                         "Storage and operator availability must be "
                         "confirmed before launch."])

    def _build_soak24(self) -> Runbook:
        return self._soak("soak24", "24-hour", S.RUN_SOAK_24H, "soak_24h")

    def _build_soak30(self) -> Runbook:
        return self._soak("soak30", "30-day", S.RUN_SOAK_30D, "soak_30d")

    # -- Pilot-0 deployment runbooks (Prompt 13) -------------------------------

    def _build_pilot_simulated(self) -> Runbook:
        return self._runbook(
            "pilot_simulated", "Pilot-0 simulated deployment",
            ["Run a governed, supervised, bounded pilot entirely inside the "
             "GridWorld sandbox. The safe default profile: nothing external "
             "is read or touched."],
            [S.RUN_BOUNDED, S.ENABLE_EMBODIMENT_SIMULATION],
            RiskLevel.MEDIUM,
            ["python examples/run_pilot_simulated.py --steps 100 "
             "--operator <name>"],
            extra_pre=["[ ] readiness report generated "
                       "(examples/run_pilot_readiness.py --profile "
                       "simulated)",
                       "[ ] medium risks acknowledged by the named operator"],
            extra_artifacts=["`.solaris_ai_nn_pilots/runs/<pilot_id>/` -- "
                             "pilot manifest, safety contract, readiness "
                             "report, input summary, pilot report, "
                             "artifacts.json",
                             "`.solaris_ai_nn_pilots/pilot_registry.json`"],
            limitations=["A simulated pilot says nothing about behaviour on "
                         "external data; graduate to the read-only stream "
                         "profile for that."])

    def _build_pilot_stream(self) -> Runbook:
        return self._runbook(
            "pilot_stream", "Pilot-0 read-only stream deployment",
            ["Ingest explicitly-named local JSONL/text files as sensory "
             "stimuli. The external world is read, validated line by line, "
             "and never acted on -- no execution, no URLs, no writes "
             "outside approved directories."],
            [S.RUN_BOUNDED], RiskLevel.MEDIUM,
            ["python examples/run_pilot_stream.py --input <file.jsonl> "
             "--format jsonl --steps 100 --operator <name>"],
            extra_pre=["[ ] every input file named explicitly (no globs, no "
                       "recursive directories)",
                       "[ ] input files reviewed: data only, no "
                       "command-shaped content expected",
                       "[ ] readiness report generated for the "
                       "read_only_stream profile"],
            extra_artifacts=["`input_summary.json` -- per-sensor ingestion "
                             "counts, validity rate, rejected-line reasons"],
            limitations=["Rejected lines are skipped and recorded, never "
                         "partially trusted; a high rejection rate means "
                         "the stream does not fit the sensory contract."])

    def _build_pilot_sidecar(self) -> Runbook:
        return self._runbook(
            "pilot_sidecar", "Pilot-0 Solaris sidecar observation",
            ["Attach the NN sidecar beside a Solaris_Ai-like runtime and "
             "observe its bus for a bounded window. Suggestions stay local; "
             "publishing them is a separate, approval-gated decision; "
             "Actions are never committed."],
            [S.RUN_BOUNDED, S.ENABLE_SIDECAR_OBSERVE,
             f"{S.ENABLE_SIDECAR_SUGGESTIONS} (only if publishing, with "
             "approval)"],
            RiskLevel.MEDIUM,
            ["python examples/run_pilot_sidecar_fake.py --steps 100 "
             "--operator <name>"],
            extra_pre=["[ ] compatibility report reviewed (probe level "
                       "bus_observable or better)",
                       "[ ] detach tested against the target runtime",
                       "[ ] publishing OFF unless a matching approval "
                       "record exists"],
            extra_artifacts=["sidecar integration summary inside the pilot "
                             "report (mirrored signals, suggestions "
                             "produced vs published)"],
            limitations=["The sidecar never calls stimulate/react/death on "
                         "the observed runtime; Solaris_Ai remains the "
                         "action authority throughout."])
