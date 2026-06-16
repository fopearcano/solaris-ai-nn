"""Experiment compiler runtime -- evidence -> human-reviewable documents.

:class:`ExperimentCompilerRuntime` loads an input manifest, reads architecture
proposals, compiles experiment specs, and builds prompt packs, branch specs, test
matrices, safety gates, operator review packets, rollback plans, and validation
plans -- writing *documents only*. It modifies no source, creates no branch,
opens no PR, runs no external coding agent, runs no unbounded experiment, and
controls no hardware/feeders/network/shell.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .branch_spec import BranchSpecBuilder
from .experiment_spec import ExperimentSpecStatus, compile_spec
from .input_manifest import ExperimentCompilerInputManifest
from .proposal_reader import ArchitectureProposalReader
from .prompt_pack import PromptPackBuilder
from .review_packet import ReviewPacketBuilder
from .rollback_plan import build_rollback_plan
from .safety import ExperimentCompilerSafetyValidator
from .safety_gates import SafetyGateEvaluator
from .test_matrix import build_test_matrix
from .validation_plan import build_validation_plan


@dataclass
class CompiledExperiment:
    """One spec plus all its compiled companion documents (in memory)."""

    spec: Any
    prompt_pack: Any = None
    branch_spec: Any = None
    test_matrix: Any = None
    gate_results: List[Any] = field(default_factory=list)
    gate_summary: Dict[str, Any] = field(default_factory=dict)
    review_packet: Any = None
    rollback_plan: Any = None
    validation_plan: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spec": self.spec.to_dict(),
            "prompt_pack": self.prompt_pack.to_dict() if self.prompt_pack
            else None,
            "branch_spec": self.branch_spec.to_dict() if self.branch_spec
            else None,
            "test_matrix": self.test_matrix.to_dict() if self.test_matrix
            else None,
            "gate_summary": dict(self.gate_summary),
            "review_packet": self.review_packet.to_dict() if self.review_packet
            else None,
            "rollback_plan": self.rollback_plan.to_dict() if self.rollback_plan
            else None,
            "validation_plan": self.validation_plan.to_dict()
            if self.validation_plan else None,
        }


@dataclass
class ExperimentCompilerRuntime:
    """Bounded compiler: research evidence -> implementation documents only."""

    state_dir: str = ".solaris_ai_nn_experiments"
    input_manifest_path: Optional[str] = None
    proposal_ids: Optional[List[str]] = None
    max_specs: int = 25
    max_prompt_packs: int = 25
    report_only: bool = False
    dry_run: bool = False
    require_operator_review: bool = True
    require_safety_gate_pass: bool = True

    manifest: ExperimentCompilerInputManifest = field(default=None, init=False)
    reader: ArchitectureProposalReader = field(
        default_factory=ArchitectureProposalReader, init=False)
    gate_evaluator: SafetyGateEvaluator = field(
        default_factory=SafetyGateEvaluator, init=False)
    safety: ExperimentCompilerSafetyValidator = field(
        default_factory=ExperimentCompilerSafetyValidator, init=False)
    compiled: List[CompiledExperiment] = field(default_factory=list, init=False)
    blocked: List[CompiledExperiment] = field(default_factory=list, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.manifest = ExperimentCompilerInputManifest()
        bounded = self.safety.validate_bounded(self.max_specs,
                                               self.max_prompt_packs)
        self._refused = not bounded.safe

    # -- input --------------------------------------------------------------

    def load_manifest(self, *, proposals: Optional[List[Dict]] = None,
                      operator_note: Any = None,
                      discover_state_dir: Optional[str] = None,
                      ) -> ExperimentCompilerInputManifest:
        if discover_state_dir:
            self.manifest.discover(discover_state_dir)
        if proposals:
            self.manifest.add_proposals(proposals)
        if operator_note is not None:
            self.manifest.provide("operator_note", operator_note,
                                  detail="operator note (advisory only)")
        return self.manifest

    # -- compile ------------------------------------------------------------

    def compile(self) -> Dict[str, Any]:
        if self._refused:
            return {"refused": True, "reason": "unbounded compiler"}
        proposals = list(self.manifest.proposals)
        if self.proposal_ids:
            proposals = [p for p in proposals
                         if str(p.get("proposal_id") or p.get("id"))
                         in set(self.proposal_ids)]
        proposals = proposals[: self.max_specs]
        reads = self.reader.read_all(proposals)

        for read in reads:
            compiled = self._compile_one(read)
            if compiled.spec.blocked:
                self.blocked.append(compiled)
            else:
                self.compiled.append(compiled)
        return {"refused": False, "compiled": len(self.compiled),
                "blocked": len(self.blocked)}

    def _compile_one(self, read) -> CompiledExperiment:
        spec = compile_spec(read)
        compiled = CompiledExperiment(spec=spec)

        if spec.blocked:
            # Blocked specs still get a review packet + rollback (for the record)
            # but no prompt pack / branch spec implementation artifacts.
            spec_d = spec.to_dict()
            compiled.gate_results = self.gate_evaluator.evaluate(spec_d)
            compiled.gate_summary = self.gate_evaluator.summary(
                compiled.gate_results)
            compiled.review_packet = ReviewPacketBuilder().build(
                spec_d, gate_summary=compiled.gate_summary)
            compiled.rollback_plan = build_rollback_plan(spec_d)
            return compiled

        spec_d = spec.to_dict()
        # Evaluate constitutional safety gates against the spec.
        compiled.gate_results = self.gate_evaluator.evaluate(spec_d)
        compiled.gate_summary = self.gate_evaluator.summary(
            compiled.gate_results)

        compiled.test_matrix = build_test_matrix(spec_d)
        spec.safety_gates = [g.gate_type for g in self.gate_evaluator.gates()]

        # A critical gate failure (or missing blocking tests) blocks readiness.
        critical_fail = not compiled.gate_summary["all_critical_passed"]
        missing_tests = compiled.test_matrix.blocks_ready
        if self.require_safety_gate_pass and critical_fail:
            spec.status = ExperimentSpecStatus.BLOCKED_BY_SAFETY
            spec.block_reason = ("critical safety gate(s) failed: "
                                 + ", ".join(
                                     compiled.gate_summary["critical_failures"]))
            self._fill_support(compiled, spec_d)
            return compiled

        # Build the full implementation artifact set.
        compiled.prompt_pack = PromptPackBuilder().build(spec_d)
        compiled.branch_spec = BranchSpecBuilder().build(spec_d)
        spec.validation_plan = [s.stage_id for s in
                                build_validation_plan(spec_d).stages]
        spec.rollback_plan = [t for t in
                              build_rollback_plan(spec_d).triggers]

        if missing_tests:
            spec.status = ExperimentSpecStatus.DRAFT
        elif self.require_operator_review:
            spec.status = ExperimentSpecStatus.READY_FOR_OPERATOR_REVIEW
        else:
            spec.status = ExperimentSpecStatus.READY_FOR_EXTERNAL_CODING_AGENT
        self._fill_support(compiled, spec.to_dict())
        return compiled

    def _fill_support(self, compiled: CompiledExperiment,
                      spec_d: Dict[str, Any]) -> None:
        compiled.review_packet = ReviewPacketBuilder().build(
            spec_d, gate_summary=compiled.gate_summary)
        compiled.rollback_plan = build_rollback_plan(spec_d)
        compiled.validation_plan = build_validation_plan(spec_d)

    # -- integration views --------------------------------------------------

    def all_experiments(self) -> List[CompiledExperiment]:
        return list(self.compiled) + list(self.blocked)

    def compiler_status(self) -> Dict[str, Any]:
        all_exp = self.all_experiments()
        ready = [c for c in self.compiled if c.spec.ready]
        ready_for_agent = [c for c in self.compiled if c.spec.status ==
                           ExperimentSpecStatus.READY_FOR_EXTERNAL_CODING_AGENT]
        gate_failures = sum(c.gate_summary.get("critical_failure_count", 0)
                            for c in all_exp)
        return {
            "experiment_compiler_enabled": True,
            "compiler_input_source_count": len(self.manifest.sources),
            "proposal_read_count": len(self.manifest.proposals),
            "compiled_spec_count": len(all_exp),
            "ready_spec_count": len(ready),
            "ready_for_external_agent_count": len(ready_for_agent),
            "blocked_spec_count": len(self.blocked),
            "prompt_pack_count": sum(1 for c in self.compiled
                                     if c.prompt_pack is not None),
            "branch_spec_count": sum(1 for c in self.compiled
                                     if c.branch_spec is not None),
            "test_matrix_count": sum(1 for c in all_exp
                                     if c.test_matrix is not None),
            "safety_gate_count": sum(len(c.gate_results) for c in all_exp),
            "safety_gate_failure_count": gate_failures,
            "review_packet_count": sum(1 for c in all_exp
                                       if c.review_packet is not None),
            "rollback_plan_count": sum(1 for c in all_exp
                                       if c.rollback_plan is not None),
            "validation_plan_count": sum(1 for c in all_exp
                                         if c.validation_plan is not None),
            "missing_evidence_count": len(self.manifest.warnings())
            + len(self.manifest.blockers()),
            "compiler_safety_block_count": self.safety.rejected_count,
            "latest_compiler_report_path": self._report_path(),
            "modifies_source": False, "creates_branch": False,
            "opens_pr": False, "runs_external_agent": False,
        }

    def _report_path(self) -> Optional[str]:
        path = os.path.join(self.state_dir, "EXPERIMENT_COMPILER_REPORT.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.compiler_status()

    def architecture_proposals(self) -> List[Dict[str, Any]]:
        # The compiler does not propose architecture changes; it documents them.
        return []

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import ExperimentCompilerReportBuilder

        return ExperimentCompilerReportBuilder(self).write()
