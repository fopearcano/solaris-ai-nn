"""Operator-governed experiment compiler -- evidence to implementation docs.

Prompt 56 produced evidence-guided architecture proposals; Prompt 57 compiles
approved or candidate proposals into implementation-ready, human-reviewable
experiment packs:

    input manifest -> read proposals -> compiled experiment specs ->
    prompt packs + branch specs + test matrices + safety gates ->
    operator review packets + rollback plans + validation plans -> reports

This is *not* autonomous coding, self-improvement, or source mutation. It is a
compiler from research evidence to human-reviewable implementation instructions.
The runtime writes documents only: it modifies no source, creates no Git branch,
opens no pull request, runs no external coding agent, controls no hardware/
feeders/network/shell, and makes no claim of consciousness, sentience, life,
personhood, agency, free will, emotion, feeling, understanding, or subjective
experience. A spec is marked ready only when its critical safety gates pass, and
blocked/falsified/inconclusive evidence is always preserved.
"""

from __future__ import annotations

from .branch_spec import BranchSpecBuilder, BranchSpecStatus, PRReadyBranchSpec
from .compiler_runtime import CompiledExperiment, ExperimentCompilerRuntime
from .experiment_spec import (
    CompiledExperimentSpec,
    ExperimentSpecStatus,
    ExperimentSpecType,
    compile_spec,
)
from .input_manifest import (
    CompilerInputSource,
    CompilerInputStatus,
    ExperimentCompilerInputManifest,
)
from .proposal_reader import (
    ArchitectureProposalReader,
    ProposalDisposition,
    ProposalPriority,
    ProposalReadResult,
)
from .prompt_pack import (
    ImplementationPromptPack,
    PromptPackBuilder,
    PromptPackSection,
)
from .reports import ExperimentCompilerReportBuilder
from .review_packet import (
    OperatorReviewPacket,
    ReviewDecision,
    ReviewPacketBuilder,
    ReviewQuestion,
)
from .rollback_plan import (
    ExperimentRollbackPlan,
    RollbackStep,
    RollbackTrigger,
    build_rollback_plan,
)
from .safety import HARD_RULES, ExperimentCompilerSafetyValidator
from .safety_gates import (
    ExperimentSafetyGate,
    SafetyGateEvaluator,
    SafetyGateResult,
    SafetyGateType,
)
from .test_matrix import (
    ExperimentTestMatrix,
    TestCategory,
    TestMatrixRow,
    TestRequirement,
    build_test_matrix,
)
from .validation_plan import (
    PostImplementationValidationPlan,
    ValidationExitCriteria,
    ValidationStage,
    ValidationStageId,
    build_validation_plan,
)

__all__ = [
    "ExperimentCompilerInputManifest", "CompilerInputSource",
    "CompilerInputStatus",
    "ArchitectureProposalReader", "ProposalReadResult", "ProposalPriority",
    "ProposalDisposition",
    "CompiledExperimentSpec", "ExperimentSpecType", "ExperimentSpecStatus",
    "compile_spec",
    "ImplementationPromptPack", "PromptPackSection", "PromptPackBuilder",
    "PRReadyBranchSpec", "BranchSpecBuilder", "BranchSpecStatus",
    "ExperimentTestMatrix", "TestMatrixRow", "TestRequirement", "TestCategory",
    "build_test_matrix",
    "ExperimentSafetyGate", "SafetyGateResult", "SafetyGateEvaluator",
    "SafetyGateType",
    "OperatorReviewPacket", "ReviewQuestion", "ReviewDecision",
    "ReviewPacketBuilder",
    "ExperimentRollbackPlan", "RollbackTrigger", "RollbackStep",
    "build_rollback_plan",
    "PostImplementationValidationPlan", "ValidationStage",
    "ValidationExitCriteria", "ValidationStageId", "build_validation_plan",
    "ExperimentCompilerRuntime", "CompiledExperiment",
    "ExperimentCompilerReportBuilder",
    "HARD_RULES", "ExperimentCompilerSafetyValidator",
]
