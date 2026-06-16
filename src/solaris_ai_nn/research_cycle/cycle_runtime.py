"""Research cycle runtime -- the bounded, read-only closed-cycle tracker.

:class:`ResearchCycleRuntime` loads the cycle manifest and the available
artifacts from the prior layers (research baseline, post-merge, intake, compiler,
architecture, soak/replication/falsification), updates the evidence ledger,
builds the artifact graph, evaluates decision gates, determines the cycle state,
proposes transitions, detects blocked states, generates next actions, and may
archive the cycle on an explicit local operator artifact -- writing local
metadata/reports only. It runs no Git, calls no GitHub, creates no branch/tag/
release/PR, modifies no source, executes no validation, runs no external agent,
controls no feeders/hardware/network/shell, and never approves itself.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .artifact_graph import ArtifactGraphBuilder
from .blocked_states import BlockedStateResolver
from .cycle_archive import ResearchCycleArchive
from .cycle_manifest import ResearchCycleManifest
from .cycle_state import (
    ResearchCycleStage,
    ResearchCycleStageStatus,
    determine_state,
)
from .cycle_transitions import CycleTransitionEngine
from .decision_gates import ResearchCycleDecisionGate
from .evidence_ledger import EvidenceContinuityLedger, EvidenceLedgerEntryType
from .next_action import NextActionPlanner
from .operator_decisions import (
    load_operator_decisions,
    required_decisions,
)
from .safety import ResearchCycleSafetyValidator

# bundle key -> evidence-ledger entry type for ingestion.
_LEDGER_MAP = (
    ("research_baseline", EvidenceLedgerEntryType.BASELINE),
    ("roadmap", EvidenceLedgerEntryType.ROADMAP),
    ("architecture_evolution", EvidenceLedgerEntryType.ARCHITECTURE_PROPOSAL),
    ("experiment_compiler", EvidenceLedgerEntryType.COMPILED_EXPERIMENT),
    ("implementation_intake", EvidenceLedgerEntryType.IMPLEMENTATION_AUDIT),
    ("post_merge", EvidenceLedgerEntryType.POST_MERGE),
    ("soak", EvidenceLedgerEntryType.SOAK),
    ("replication", EvidenceLedgerEntryType.REPLICATION),
    ("falsification", EvidenceLedgerEntryType.FALSIFICATION),
)


@dataclass
class ResearchCycleRuntime:
    """Bounded, read-only closed research-cycle tracker."""

    state_dir: str = ".solaris_ai_nn_research_cycle"
    cycle_manifest_path: Optional[str] = None
    artifact_roots: List[str] = field(default_factory=list)
    report_only: bool = True
    dry_run: bool = False
    max_runtime_s: float = 30.0
    require_operator_decisions: bool = True
    require_safety_gate_pass: bool = True
    allow_archive: bool = False

    safety: ResearchCycleSafetyValidator = field(
        default_factory=ResearchCycleSafetyValidator, init=False)
    manifest: Any = field(default=None, init=False)
    ledger: Any = field(default=None, init=False)
    archive: Any = field(default_factory=ResearchCycleArchive, init=False)
    state: Dict[str, Any] = field(default_factory=dict, init=False)
    graph: Dict[str, Any] = field(default_factory=dict, init=False)
    gates: Dict[str, Any] = field(default_factory=dict, init=False)
    operator_required: List[Dict] = field(default_factory=list, init=False)
    blocked: Dict[str, Any] = field(default_factory=dict, init=False)
    transitions: Dict[str, Any] = field(default_factory=dict, init=False)
    next_actions: Dict[str, Any] = field(default_factory=dict, init=False)
    _bundle: Dict[str, Any] = field(default_factory=dict, init=False)
    _state_obj: Any = field(default=None, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.ledger = EvidenceContinuityLedger(state_dir=self.state_dir,
                                               persist=not self.dry_run)
        bounded = self.safety.validate_bounded(self.max_runtime_s)
        self._refused = not bounded.safe

    def load_bundle(self, bundle: Optional[Dict[str, Any]] = None) -> None:
        self._bundle = dict(bundle or {})
        self.manifest = ResearchCycleManifest.from_dict(
            self._bundle.get("cycle_manifest", {}))

    # -- run ----------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        if self._refused:
            return {"refused": True, "reason": "unbounded runtime"}
        bundle = self._bundle
        cycle_id = self.manifest.identity.cycle_id if self.manifest else "cycle_1"
        operator_records = load_operator_decisions(
            bundle.get("operator_decisions"))
        operator_dicts = [d.to_dict() for d in operator_records]

        # 1. Evidence ledger (append-only; negatives/falsified/missing kept).
        self._ingest_evidence(bundle, cycle_id)

        # 2. Artifact graph (contradictions + missing nodes visible).
        self.graph = ArtifactGraphBuilder().build(bundle).to_dict()

        # 3. Decision gates (advisory; operator gates not auto-approved).
        gate_results = ResearchCycleDecisionGate().evaluate_all(
            bundle, operator_decisions=operator_dicts)
        self.gates = ResearchCycleDecisionGate.summary(gate_results)

        # 4. Operator decisions still required.
        self.operator_required = [r.to_dict() for r in required_decisions(
            bundle, operator_records)]

        # 5. Cycle state.
        self._state_obj = determine_state(bundle)
        self.state = self._state_obj.to_dict()

        # 6. Blocked states.
        blocked_states = BlockedStateResolver().detect(
            bundle, operator_decisions=operator_dicts)
        self.blocked = BlockedStateResolver.summary(blocked_states)
        is_blocked = self.blocked["blocked_state_count"] > 0 or \
            self._state_obj.blocked
        if is_blocked and self._state_obj.stage != ResearchCycleStage.BLOCKED:
            self.ledger.add(EvidenceLedgerEntryType.BLOCKED,
                            summary="cycle has unresolved blocker(s)",
                            cycle_id=cycle_id)

        # 7. Proposed transitions (gate-checked; advisory).
        gates_passed = self.gates["all_critical_passed"] and \
            self.gates["waiting_for_operator_count"] == 0
        transitions = CycleTransitionEngine().propose(
            self._state_obj.stage, gates_passed=gates_passed,
            blocked=is_blocked)
        self.transitions = CycleTransitionEngine().to_dict(transitions)

        # 8. Next actions.
        actions = NextActionPlanner().plan(
            stage=self._state_obj.stage, blocked=is_blocked,
            blocked_states=self.blocked["states"])
        self.next_actions = NextActionPlanner.summary(actions)

        # 9. Archive only on an explicit local operator artifact.
        self._maybe_archive(bundle, cycle_id, operator_records)

        # Persist the manifest state.
        self.manifest.current_cycle_state = self._state_obj.stage
        if not self.dry_run:
            self.manifest.persist(self.state_dir)
        return {"refused": False, "stage": self._state_obj.stage,
                "blocked": is_blocked}

    def _ingest_evidence(self, bundle: Dict[str, Any], cycle_id: str) -> None:
        for key, entry_type in _LEDGER_MAP:
            if bundle.get(key):
                self.ledger.add(entry_type, summary=f"{key} evidence present",
                                artifact_ref=key, cycle_id=cycle_id)
            else:
                self.ledger.add(EvidenceLedgerEntryType.MISSING,
                                summary=f"{key} evidence missing",
                                artifact_ref=key, cycle_id=cycle_id)
        # Negative / falsified evidence (preserved).
        intake = bundle.get("implementation_intake", {}) or {}
        if int(intake.get("critical_safety_regression_count", 0) or 0) > 0:
            self.ledger.add(EvidenceLedgerEntryType.NEGATIVE,
                            summary="intake critical safety regression",
                            artifact_ref="implementation_intake",
                            cycle_id=cycle_id)
        fals = bundle.get("falsification", {}) or {}
        if int(fals.get("falsified_claim_count", 0) or 0) > 0:
            self.ledger.add(EvidenceLedgerEntryType.FALSIFICATION,
                            summary="falsified claim(s) present",
                            artifact_ref="falsification", cycle_id=cycle_id)
        for d in (bundle.get("operator_decisions") or []):
            self.ledger.add(EvidenceLedgerEntryType.OPERATOR_DECISION,
                            summary=f"operator decision: "
                                    f"{d.get('decision_type')} -> "
                                    f"{d.get('status')}",
                            cycle_id=cycle_id)

    def _maybe_archive(self, bundle: Dict[str, Any], cycle_id: str,
                       operator_records: List[Any]) -> None:
        from .cycle_archive import ArchiveReason

        archive_requested = any(
            d.decision_type == "archive_cycle" and d.approved
            for d in operator_records)
        if not (self.allow_archive and archive_requested):
            return
        reason = (ArchiveReason.OPERATOR_ABANDONED
                  if self._state_obj.blocked else ArchiveReason.COMPLETED)
        self.archive.archive(cycle_id, reason,
                             final_stage=self._state_obj.stage,
                             detail="archived on explicit operator decision")

    # -- integration views --------------------------------------------------

    def research_cycle_status(self) -> Dict[str, Any]:
        ledger = self.ledger.index()
        return {
            "research_cycle_enabled": True,
            "current_cycle_id": self.manifest.identity.cycle_id
            if self.manifest else None,
            "parent_cycle_id": self.manifest.identity.parent_cycle_id
            if self.manifest else "",
            "current_cycle_stage": self.state.get("stage"),
            "current_cycle_status": self.state.get("status"),
            "current_baseline_id": self.manifest.identity.baseline_id
            if self.manifest else "",
            "research_cycle_count": 1,
            "cycle_stage_count": len(ResearchCycleStage.ORDER),
            "completed_cycle_count": 1 if self.state.get("stage") ==
            ResearchCycleStage.CYCLE_COMPLETE else 0,
            "archived_cycle_count": self.archive.to_dict()[
                "archived_cycle_count"],
            "decision_gate_count": self.gates.get("decision_gate_count", 0),
            "failed_decision_gate_count": self.gates.get(
                "failed_decision_gate_count", 0),
            "operator_decision_required_count": len(self.operator_required),
            "blocked_state_count": self.blocked.get("blocked_state_count", 0),
            "unresolved_blocker_count": self.blocked.get(
                "unresolved_blocker_count", 0),
            "evidence_ledger_entry_count": ledger.get(
                "evidence_ledger_entry_count", 0),
            "missing_evidence_entry_count": ledger.get(
                "missing_evidence_entry_count", 0),
            "negative_evidence_entry_count": ledger.get(
                "negative_evidence_entry_count", 0),
            "falsified_evidence_entry_count": ledger.get(
                "falsified_evidence_entry_count", 0),
            "artifact_graph_node_count": self.graph.get(
                "artifact_graph_node_count", 0),
            "artifact_graph_contradiction_count": self.graph.get(
                "artifact_graph_contradiction_count", 0),
            "next_action_count": self.next_actions.get("next_action_count", 0),
            "research_cycle_safety_block_count": self.safety.rejected_count,
            "latest_research_cycle_report_path": self._report_path(),
            "modifies_source": False, "runs_git": False, "calls_github": False,
            "approves_itself": False,
        }

    def _report_path(self) -> Optional[str]:
        path = os.path.join(self.state_dir, "RESEARCH_CYCLE_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.research_cycle_status()

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import ResearchCycleReportBuilder

        return ResearchCycleReportBuilder(self).write()
