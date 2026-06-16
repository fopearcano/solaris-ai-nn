"""Diagram builder -- Mermaid diagrams of the Solaris-AI-NN architecture.

:class:`DiagramBuilder` generates the architecture diagrams in Mermaid Markdown
(system map, organismic core loop, evidence lifecycle, research cycle, alpha CLI
flow, safety boundary map, claim governance flow, review feedback loop, module
dependency map, artifact/state directory map). Diagrams are Markdown-compatible,
imply no autonomous code modification, and include safety boundaries where
relevant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class DiagramKind:
    SYSTEM_MAP = "high_level_system_map"
    CORE_LOOP = "organismic_core_loop"
    EVIDENCE_LIFECYCLE = "evidence_lifecycle"
    RESEARCH_CYCLE = "research_cycle"
    ALPHA_CLI_FLOW = "alpha_cli_flow"
    SAFETY_BOUNDARY_MAP = "safety_boundary_map"
    CLAIM_GOVERNANCE_FLOW = "claim_governance_flow"
    REVIEW_FEEDBACK_LOOP = "review_feedback_loop"
    MODULE_DEPENDENCY_MAP = "module_dependency_map"
    ARTIFACT_STATE_MAP = "artifact_state_directory_map"

    ALL = (SYSTEM_MAP, CORE_LOOP, EVIDENCE_LIFECYCLE, RESEARCH_CYCLE,
           ALPHA_CLI_FLOW, SAFETY_BOUNDARY_MAP, CLAIM_GOVERNANCE_FLOW,
           REVIEW_FEEDBACK_LOOP, MODULE_DEPENDENCY_MAP, ARTIFACT_STATE_MAP)


_MERMAID: Dict[str, str] = {
    DiagramKind.SYSTEM_MAP: """flowchart TD
  Sensorium[Plural Sensorium] --> Metabolism[Perceptual Metabolism]
  Metabolism --> Ontogenesis[Ontogenesis]
  Ontogenesis --> Semiogenesis[Semiogenesis]
  Semiogenesis --> Cognition[Cognition]
  Cognition --> Boundary[Self-Boundary]
  Boundary --> Desire[Desire / Valence]
  Desire --> Action[Action-Reaction]
  Action --> Development[Long-Horizon Development]
  Development --> Soak[Soak Protocol]
  Soak --> Replication[Replication / Falsification]
  Replication --> Evolution[Architecture Evolution]
  Evolution --> Compiler[Experiment Compiler]
  Compiler --> Intake[Implementation Intake]
  Intake --> Baseline[Research Baseline]
  Baseline --> Cycle[Research Cycle]
  Cycle --> Claims[Scientific Claims]
  Claims --> Review[Independent Review]
  Review --> Assimilation[Review Assimilation]
  Assimilation --> Evolution""",
    DiagramKind.CORE_LOOP: """flowchart LR
  Stimulus --> Push
  Push --> Desire
  Desire --> InternalAction
  InternalAction --> Reaction
  Reaction --> Consequence
  Consequence --> Memory
  Memory --> Habit
  Habit --> FuturePerception
  FuturePerception --> Stimulus""",
    DiagramKind.RESEARCH_CYCLE: """flowchart TD
  Baseline --> Roadmap
  Roadmap --> ArchitectureProposal
  ArchitectureProposal --> ExperimentPack
  ExperimentPack --> ExternalImplementation
  ExternalImplementation --> IntakeAudit
  IntakeAudit --> HumanMerge
  HumanMerge --> PostMergeAssimilation
  PostMergeAssimilation --> NewBaseline
  NewBaseline --> SoakReplication
  SoakReplication --> ClaimsReview
  ClaimsReview --> NextExperiment""",
    DiagramKind.EVIDENCE_LIFECYCLE: """flowchart LR
  FixtureInput[Fixture / Read-Only Input] --> ModuleRun[Bounded Module Run]
  ModuleRun --> Evidence[Evidence Artifacts]
  Evidence --> Soak[Soak / Replication / Falsification]
  Soak --> Baseline[Research Baseline]
  Baseline --> Claims[Scientific Claim Registry]
  Claims --> Review[Independent Review]
  Review --> Assimilation[Reviewer Feedback Assimilation]
  Assimilation --> Claims""",
    DiagramKind.ALPHA_CLI_FLOW: """flowchart TD
  Init[init: state layout] --> Doctor[doctor: system check]
  Doctor --> Modules[modules: registry]
  Modules --> RunDemo[run-demo: fixture e2e]
  RunDemo --> ArtifactIndex[artifact-index]
  ArtifactIndex --> CycleStatus[cycle-status]
  CycleStatus --> BuildReport[build-report]
  BuildReport --> BuildDocs[build-docs: whitepaper / book]""",
    DiagramKind.SAFETY_BOUNDARY_MAP: """flowchart TD
  Operator[Operator] --> CLI[Local CLI]
  CLI --> Runtime[Bounded Local Runtime]
  Runtime -. blocked .-> NoNetwork[No Network / Shell / OS]
  Runtime -. blocked .-> NoGit[No Git / GitHub]
  Runtime -. blocked .-> NoPublish[No Publish / Upload]
  Runtime -. blocked .-> NoFeeders[No Feeder / Hardware Control]
  Runtime -. blocked .-> NoActuation[No Real-World Actuation]
  Runtime -. blocked .-> NoClaims[No Consciousness / Life / Agency Claim]
  Runtime --> Docs[Local Documentation / Reports]""",
    DiagramKind.CLAIM_GOVERNANCE_FLOW: """flowchart LR
  Evidence --> Claim[Claim Registry]
  Claim --> Strength[Claim Strength]
  Strength --> Counter[Counterevidence]
  Counter --> Forbidden[Forbidden Claim Detector]
  Forbidden --> ClaimGuard[ClaimGuard Scan]
  ClaimGuard --> Dossier[Publication Dossier - draft only]""",
    DiagramKind.REVIEW_FEEDBACK_LOOP: """flowchart TD
  ReviewerPack[Reviewer Pack] --> Objections[Reviewer Objections]
  Objections --> Classify[Objection Classifier]
  Classify --> ClaimImpact[Claim Impact]
  ClaimImpact --> Gaps[Evidence Gap Map]
  Gaps --> Recommendations[Experiment Recommendations]
  Recommendations --> Compiler[Experiment Compiler]
  ClaimImpact --> ClaimRegistry[Claim Registry - proposals only]""",
    DiagramKind.MODULE_DEPENDENCY_MAP: """flowchart TD
  Sensorium --> Cognition
  Cognition --> Claims
  Claims --> Review
  Review --> Assimilation
  Assimilation --> Cycle[Research Cycle]
  Cycle --> Alpha[Alpha System]
  Alpha --> Book[Architecture Book]
  InnerMAP[Inner MAP] --- Alpha
  Evaluation --- Alpha""",
    DiagramKind.ARTIFACT_STATE_MAP: """flowchart TD
  Root[.solaris_ai_nn_alpha/] --> Reports[reports/]
  Root --> Artifacts[artifacts/]
  Root --> Index[index/]
  Claims[.solaris_ai_nn_claims/] --> ClaimReports[claim reports]
  Review[.solaris_ai_nn_review/] --> ReviewReports[review reports]
  Docs[.solaris_ai_nn_docs/] --> DocManifest[DOC_MANIFEST.json]
  Whitepaper[docs/whitepaper/] --> Book[architecture book + whitepaper]""",
}

_TITLES = {
    DiagramKind.SYSTEM_MAP: "Full Architecture (high-level system map)",
    DiagramKind.CORE_LOOP: "Organismic Core Loop",
    DiagramKind.EVIDENCE_LIFECYCLE: "Evidence Lifecycle",
    DiagramKind.RESEARCH_CYCLE: "Research Governance Loop",
    DiagramKind.ALPHA_CLI_FLOW: "Alpha CLI Flow",
    DiagramKind.SAFETY_BOUNDARY_MAP: "Safety Boundary Map",
    DiagramKind.CLAIM_GOVERNANCE_FLOW: "Claim Governance Flow",
    DiagramKind.REVIEW_FEEDBACK_LOOP: "Review Feedback Loop",
    DiagramKind.MODULE_DEPENDENCY_MAP: "Module Dependency Map",
    DiagramKind.ARTIFACT_STATE_MAP: "Artifact / State Directory Map",
}


@dataclass
class ArchitectureDiagram:
    """One Mermaid diagram."""

    kind: str
    title: str
    mermaid: str

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "title": self.title, "mermaid": self.mermaid}

    def render_md(self) -> str:
        return (f"### {self.title}\n\n```mermaid\n{self.mermaid}\n```\n\n"
                "_Diagram is descriptive only; it implies no autonomous code "
                "modification and no real-world actuation._\n")


@dataclass
class DiagramBuilder:
    """Builds the architecture Mermaid diagrams."""

    def build(self, kind: str) -> ArchitectureDiagram:
        if kind not in DiagramKind.ALL:
            kind = DiagramKind.SYSTEM_MAP
        return ArchitectureDiagram(kind=kind, title=_TITLES[kind],
                                   mermaid=_MERMAID[kind])

    def build_all(self) -> List[ArchitectureDiagram]:
        return [self.build(k) for k in DiagramKind.ALL]

    def summary(self) -> Dict[str, Any]:
        diagrams = self.build_all()
        return {
            "generated_diagram_count": len(diagrams),
            "diagram_kinds": [d.kind for d in diagrams],
            "note": "Mermaid diagrams are Markdown-compatible and imply no "
                    "autonomous code modification",
        }

    def render_md(self) -> str:
        lines = ["## Architecture Diagrams", ""]
        for d in self.build_all():
            lines.append(d.render_md())
        return "\n".join(lines)
