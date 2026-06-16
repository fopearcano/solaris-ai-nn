"""Developmental replication runtime -- the bounded cross-run study manager.

:class:`DevelopmentalReplicationRuntime` loads a replication plan + run registry,
registers available developmental runs, indexes their soak/developmental
artifacts, aligns runs pairwise, computes structural similarity, detects
divergence, analyzes environmental dependency, runs bounded falsification tests,
builds the replication matrix, and produces reports. It is bounded, starts no
long soaks/feeders, controls no hardware, modifies no source artifacts, uses no
human teaching, and makes no unsupported claims.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Dict, List, Optional

from .cross_run_alignment import CrossRunAlignment
from .divergence import DivergenceDetector
from .environmental_dependency import EnvironmentalDependencyAnalyzer
from .falsification import FalsificationTest, FalsificationTestType
from .lineage import DevelopmentalLineage, LineageNode, LineageRelation
from .replication_matrix import ReplicationMatrixBuilder
from .replication_plan import ReplicationPlan
from .run_registry import DevelopmentalRunRegistry, RegisteredDevelopmentalRun
from .safety import DevelopmentalReplicationSafetyValidator
from .structural_similarity import StructuralSimilarity

# Falsification tests that need only the run profile (no null re-run).
_PROFILE_ONLY_TESTS = (
    FalsificationTestType.LOG_ACCUMULATION_NULL,
    FalsificationTestType.FIXTURE_OVERFIT_PROBE,
    FalsificationTestType.HUMAN_LABEL_OVERFIT_PROBE,
    FalsificationTestType.SIMULATION_AS_OBSERVATION_PROBE,
)


@dataclass
class DevelopmentalReplicationRuntime:
    """Bounded study manager that compares + falsifies developmental runs."""

    state_dir: str = ".solaris_ai_nn_replication"
    plan_path: Optional[str] = None
    registry_path: Optional[str] = None
    max_runtime_s: float = 30.0
    max_runs: int = 12
    max_falsification_tests: int = 24
    dry_run: bool = False
    report_only: bool = False
    allow_live_read_only: bool = False
    require_governance_for_live: bool = True
    governance_approved: bool = False

    plan: ReplicationPlan = field(default=None, init=False)
    registry: DevelopmentalRunRegistry = field(default=None, init=False)
    lineage: DevelopmentalLineage = field(default_factory=DevelopmentalLineage,
                                          init=False)
    safety: DevelopmentalReplicationSafetyValidator = field(
        default_factory=DevelopmentalReplicationSafetyValidator, init=False)

    alignments: List[Dict[str, Any]] = field(default_factory=list, init=False)
    similarities: List[Dict[str, Any]] = field(default_factory=list, init=False)
    divergences: List[Dict[str, Any]] = field(default_factory=list, init=False)
    dependencies: Dict[str, List[Dict]] = field(default_factory=dict, init=False)
    dependency_scores: Dict[str, Dict] = field(default_factory=dict, init=False)
    falsifications: List[Dict[str, Any]] = field(default_factory=list,
                                                 init=False)
    matrix: Any = field(default=None, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.plan = ReplicationPlan.default()
        self.registry = DevelopmentalRunRegistry(state_dir=self.state_dir,
                                                 persist=not self.dry_run)
        bounded = self.safety.validate_bounded(self.max_runs, self.max_runtime_s)
        self._refused = not bounded.safe

    # -- registration ---------------------------------------------------------

    def register_run(self, run_id: str, **fields) -> RegisteredDevelopmentalRun:
        run = self.registry.register_from_dict(run_id, **fields)
        self.lineage.add_node(LineageNode(
            run_id=run_id, sensorium_profile=run.sensorium_profile,
            seed=run.seed, fixture_live_replay=run.fixture_live_replay))
        return run

    def discover_run(self, run_id: str, state_dir: str, **fields,
                     ) -> RegisteredDevelopmentalRun:
        run = self.registry.discover(run_id, state_dir, **fields)
        self.lineage.add_node(LineageNode(
            run_id=run_id, sensorium_profile=run.sensorium_profile,
            seed=run.seed, fixture_live_replay=run.fixture_live_replay))
        return run

    def relate(self, parent: str, child: str, relation: str, **kw) -> None:
        self.lineage.relate(parent, child, relation, **kw)

    # -- bounded analysis pipeline --------------------------------------------

    def analyze(self) -> Dict[str, Any]:
        if self._refused:
            return {"refused": True, "reason": "unbounded run"}
        started = time.time()
        runs = [r.to_dict() for r in list(self.registry.runs.values())
                ][: self.max_runs]

        similarity = StructuralSimilarity()
        aligner = CrossRunAlignment()
        divergence = DivergenceDetector()
        for a, b in combinations(runs, 2):
            if time.time() - started > self.max_runtime_s:
                break
            self.alignments.append(aligner.align(a, b))
            sim = similarity.compare(a, b)
            self.similarities.append(sim.to_dict())
            self.divergences.extend(
                d.to_dict() for d in divergence.detect(
                    a, b, similarity=sim.overall))

        # Environmental dependency per run.
        analyzer = EnvironmentalDependencyAnalyzer()
        for run in runs:
            deps = analyzer.analyze(run)
            self.dependencies[run["run_id"]] = [d.to_dict() for d in deps]
            self.dependency_scores[run["run_id"]] = analyzer.overall_scores(deps)

        self._run_falsifications(runs)
        self.matrix = ReplicationMatrixBuilder().build(
            similarity_results=self.similarities, divergences=self.divergences,
            falsification_results=self.falsifications,
            unavailable_arms=self._unavailable_arms())
        return {"refused": False, "run_count": len(runs),
                "pair_count": len(self.similarities)}

    def _run_falsifications(self, runs: List[Dict[str, Any]]) -> None:
        lab = FalsificationTest()
        budget = self.max_falsification_tests
        for run in runs:
            profile = self._profile(run)
            nulls = run.get("falsification_nulls", {}) or {}
            tests = list(_PROFILE_ONLY_TESTS) + list(nulls.keys())
            for test_type in tests:
                if budget <= 0:
                    return
                if test_type not in FalsificationTestType.ALL:
                    continue
                result = lab.run(test_type, run_profile=profile,
                                 null_profile=nulls.get(test_type))
                d = result.to_dict()
                d["run_id"] = run.get("run_id")
                self.falsifications.append(d)
                budget -= 1

    @staticmethod
    def _profile(run: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten a run's comparison profile for falsification handlers."""
        merged: Dict[str, Any] = {}
        merged.update(run.get("developmental_profile", {}))
        merged.update(run.get("stack_metrics", {}))
        merged["world_signature"] = run.get("world_signature", {})
        merged.update(run.get("world_signature", {}))
        merged["human_label_exposure"] = run.get("human_label_exposure")
        return merged

    def _unavailable_arms(self) -> List[str]:
        unavailable: List[str] = []
        for aid, arm in self.plan.arms.items():
            if arm.requires_governance and not self.governance_approved:
                unavailable.append(aid)
        return unavailable

    # -- integration views ----------------------------------------------------

    def architecture_proposals(self) -> List[Dict[str, Any]]:
        from ..architecture_evolution import replication_revision_proposals

        return replication_revision_proposals(self.replication_status())

    def replication_status(self) -> Dict[str, Any]:
        matrix = self.matrix.to_dict() if self.matrix else {}
        sims = [s.get("overall", 0.0) for s in self.similarities]
        mean = (sum(sims) / len(sims)) if sims else 0.0
        var = (sum((s - mean) ** 2 for s in sims) / len(sims)) if sims else 0.0
        falsified = [f for f in self.falsifications
                     if f.get("outcome") == "falsified"]
        passed = [f for f in self.falsifications
                  if f.get("outcome") == "passed"]
        dep_score = (sum(d["environmental_dependency_score"]
                         for d in self.dependency_scores.values())
                     / len(self.dependency_scores)
                     ) if self.dependency_scores else 0.0
        return {
            "developmental_replication_enabled": True,
            "registered_run_count": len(self.registry.runs),
            "lineage_count": len({r.lineage_id
                                  for r in self.registry.runs.values()
                                  if r.lineage_id}),
            "aligned_run_pair_count": len(self.similarities),
            "replicated_claim_count": matrix.get("replicated_claim_count", 0),
            "partially_replicated_claim_count":
                matrix.get("partially_replicated_claim_count", 0),
            "diverged_claim_count": matrix.get("diverged_claim_count", 0),
            "falsified_claim_count": matrix.get("falsified_claim_count", 0),
            "inconclusive_claim_count":
                matrix.get("inconclusive_claim_count", 0),
            "structural_similarity_mean": round(mean, 4),
            "structural_similarity_variance": round(var, 4),
            "strongest_structural_similarity": round(max(sims), 4) if sims
            else 0.0,
            "strongest_divergence_reason": (self.divergences[0]["reason"]
                                            if self.divergences else None),
            "environmental_dependency_score": round(dep_score, 4),
            "fixture_overfit_score": round(max(
                (d["fixture_overfit_score"]
                 for d in self.dependency_scores.values()), default=0.0), 4),
            "human_label_dependency_score": round(max(
                (d["human_label_dependency_score"]
                 for d in self.dependency_scores.values()), default=0.0), 4),
            "falsification_test_count": len(self.falsifications),
            "falsification_pass_count": len(passed),
            "falsification_fail_count": len(falsified),
            "replication_safety_block_count": self.safety.rejected_count,
            "replication_matrix_path": self._matrix_path(),
            "latest_replication_report_path": self._report_path(),
            "is_biological_ancestry": False,
            "is_consciousness_or_personhood": False,
        }

    def _report_path(self) -> Optional[str]:
        path = os.path.join(self.state_dir, "REPLICATION_REPORT.md")
        return path if os.path.isfile(path) else None

    def _matrix_path(self) -> Optional[str]:
        path = os.path.join(self.state_dir, "REPLICATION_MATRIX.md")
        return path if os.path.isfile(path) else None

    def snapshot(self) -> Dict[str, Any]:
        return self.replication_status()

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import DevelopmentalReplicationReportBuilder

        return DevelopmentalReplicationReportBuilder(self).write()
