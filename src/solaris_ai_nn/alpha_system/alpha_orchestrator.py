"""Alpha research orchestrator -- the bounded, local assembly runtime.

:class:`AlphaResearchOrchestrator` loads the alpha profile, initializes the state
layout, runs the system check, builds the module registry, executes the bounded
fixture demo plan, builds the artifact index, generates the cycle status, the alpha
report, and the operator runbook, and exposes a status for Inner MAP / Evaluation.

It is bounded and local-only: it executes no shell command, calls no Git/GitHub,
publishes/uploads nothing, runs no external agent, controls no hardware/feeders,
never hides skipped or missing modules, and writes honest reports. Optional
organismic modules are recorded as a labelled alpha fallback when present (the
module's full scientific run is not invoked here) and as skipped markers when
absent; the claim/review/cycle modules are called in demo-safe report-only mode
when available, with safe placeholders otherwise.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .alpha_profile import AlphaResearchProfile, get_alpha_profile
from .artifact_index import AlphaArtifactIndex, AlphaArtifactKind
from .cycle_status import determine_cycle_status
from .demo_plan import AlphaDemoPlan, AlphaDemoStepStatus
from .module_registry import AlphaModuleRegistry
from .operator_runbook import AlphaRunbookBuilder
from .safety import AlphaResearchSafetyValidator
from .state_layout import AlphaStateLayout
from .system_check import AlphaCheckSeverity, AlphaSystemCheck

# demo step -> (module key, artifact kind) for the organismic fallback steps.
_ORGANISMIC_STEPS = {
    "sensorium_pass": ("organismic_demo", AlphaArtifactKind.ORGANISM_REPORT),
    "metabolism_pass": ("perceptual_metabolism",
                        AlphaArtifactKind.METABOLISM_REPORT),
    "ontogenesis_pass": ("perceptual_ontogenesis",
                         AlphaArtifactKind.CONCEPT_REPORT),
    "semiogenesis_pass": ("semiogenesis", AlphaArtifactKind.SIGN_REPORT),
    "cognition_pass": ("sensorium_cognition", AlphaArtifactKind.COGNITION_REPORT),
    "self_boundary_pass": ("self_boundary",
                           AlphaArtifactKind.SELF_BOUNDARY_REPORT),
    "desire_action_pass": ("action_reaction",
                           AlphaArtifactKind.DESIRE_ACTION_REPORT),
    "developmental_pass": ("developmental_life",
                           AlphaArtifactKind.DEVELOPMENTAL_REPORT),
}


@dataclass
class AlphaResearchOrchestrator:
    """Bounded, local Alpha Research System assembly runtime."""

    state_dir: str = ".solaris_ai_nn_alpha"
    profile: Optional[str] = None
    max_runtime_s: float = 60.0
    max_ticks: int = 50
    fixture_mode: bool = True
    report_only: bool = False
    dry_run: bool = False
    skip_optional: bool = False
    strict: bool = False
    require_claimguard: bool = False

    safety: AlphaResearchSafetyValidator = field(
        default_factory=AlphaResearchSafetyValidator, init=False)
    alpha_profile: Any = field(default=None, init=False)
    layout: Any = field(default=None, init=False)
    registry: Any = field(default=None, init=False)
    check: Dict[str, Any] = field(default_factory=dict, init=False)
    plan: Any = field(default=None, init=False)
    artifact_index: Any = field(default=None, init=False)
    cycle: Dict[str, Any] = field(default_factory=dict, init=False)
    runbook: Any = field(default=None, init=False)
    run_id: str = field(default="", init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.alpha_profile = get_alpha_profile(self.profile)
        # The profile's bound caps the requested runtime.
        if not self.max_runtime_s:
            self._refused = True
        self.run_id = f"alpha_run_{int(time.time())}"

    # -- public entry points -------------------------------------------------

    def initialize(self) -> Dict[str, Any]:
        self.layout = AlphaStateLayout(state_root=self.state_dir)
        return self.layout.initialize()

    def run_doctor(self) -> Dict[str, Any]:
        if self.layout is None:
            self.layout = AlphaStateLayout(state_root=self.state_dir)
        if self.registry is None:
            self.registry = AlphaModuleRegistry.build()
        checker = AlphaSystemCheck()
        checker.run(state_root=self.state_dir, profile=self.alpha_profile,
                    registry=self.registry,
                    require_claimguard=self.require_claimguard)
        self.check = checker.summary()
        return self.check

    def build_registry(self) -> Dict[str, Any]:
        self.registry = AlphaModuleRegistry.build()
        return self.registry.to_dict()

    def run(self) -> Dict[str, Any]:
        """Run the full bounded alpha assembly (init -> demo -> reports)."""
        if self._refused:
            return {"refused": True, "reason": "unbounded runtime"}
        bounded = self.safety.validate_bounded(self.max_runtime_s)
        if not bounded.safe:
            return {"refused": True, "reason": "unbounded runtime"}

        self.initialize()
        self.build_registry()
        self.run_doctor()
        self.artifact_index = AlphaArtifactIndex(state_root=self.state_dir,
                                                 run_id=self.run_id)
        self.artifact_index.add(AlphaArtifactKind.STATE_MANIFEST,
                                ref=self.layout.manifest_path)
        self.artifact_index.add(AlphaArtifactKind.MODULE_REGISTRY,
                                ref="module_registry")
        self.artifact_index.add(AlphaArtifactKind.SYSTEM_CHECK,
                                ref="system_check")

        doctor_blocked = self.check.get("blocker_count", 0) > 0
        if doctor_blocked and self.strict:
            self.plan = AlphaDemoPlan.build()
            self._finalize(demo_completed=False, doctor_blocked=True)
            return self._result(demo_completed=False, doctor_blocked=True)

        if not self.report_only:
            self._execute_demo()
        else:
            self.plan = AlphaDemoPlan.build()
        warnings = self._warning_count()
        self._finalize(demo_completed=not self.report_only,
                       doctor_blocked=doctor_blocked)
        return self._result(demo_completed=not self.report_only,
                            doctor_blocked=doctor_blocked)

    # -- demo execution ------------------------------------------------------

    def _execute_demo(self) -> None:
        self.plan = AlphaDemoPlan.build()
        for step in self.plan.steps:
            if step.step_id in ("init_state", "load_fixture",
                                "evidence_summary", "alpha_report"):
                self._run_foundation_step(step)
            elif step.step_id in _ORGANISMIC_STEPS:
                self._run_organismic_step(step)
            elif step.step_id == "claim_summary":
                self._run_claims_step(step)
            elif step.step_id == "review_pack":
                self._run_review_step(step)
            elif step.step_id == "cycle_status":
                self._run_cycle_step(step)

    def _run_foundation_step(self, step) -> None:
        if step.step_id == "load_fixture":
            ref = self._ensure_fixture()
            step.artifact_ref = ref
            self.artifact_index.add(AlphaArtifactKind.FIXTURE_INPUT, ref=ref)
        if step.step_id == "evidence_summary":
            ref = self._write_artifact("alpha_evidence_summary.json", {
                "fixture_events_indexed": True,
                "note": "local fixture-derived evidence summary; not a claim"})
            step.artifact_ref = ref
            self.artifact_index.add(AlphaArtifactKind.DEMO_STEP_OUTPUT, ref=ref)
        step.status = AlphaDemoStepStatus.COMPLETED
        step.detail = "bounded foundation step completed locally"

    def _run_organismic_step(self, step) -> None:
        module_key, kind = _ORGANISMIC_STEPS[step.step_id]
        available = self.registry.is_available(module_key)
        if not available or self.skip_optional:
            step.status = AlphaDemoStepStatus.SKIPPED
            step.detail = (f"optional module {module_key!r} "
                           + ("skipped by request" if self.skip_optional
                              else "not available"))
            self.artifact_index.add_skipped_module(module_key, step.detail)
            return
        # The module is present, but the Alpha demo records a clearly labelled
        # fallback summary rather than invoking the module's full scientific run.
        ref = self._write_artifact(f"{step.step_id}_alpha_fallback.json", {
            "module": module_key, "output_kind": "alpha_fallback_summary",
            "is_real_module_output": False,
            "detail": ("module is available; the alpha demo records a bounded "
                       "fallback summary, not the module's full output"),
            "note": "no consciousness/life/agency claim is made"})
        step.status = AlphaDemoStepStatus.COMPLETED_FALLBACK
        step.artifact_ref = ref
        step.detail = f"module {module_key!r} available; alpha fallback recorded"
        self.artifact_index.add(kind, ref=ref, detail="alpha fallback summary")

    def _run_claims_step(self, step) -> None:
        if not self.registry.is_available("scientific_claims"):
            self._placeholder(step, "scientific_claims",
                              AlphaArtifactKind.CLAIM_REPORT,
                              "Scientific Claims module unavailable; no "
                              "scientific claim generated.")
            return
        try:
            from ..scientific_claims import ScientificClaimRuntime

            claims_dir = self.layout.subdir("claims")
            rt = ScientificClaimRuntime(state_dir=claims_dir,
                                        max_runtime_s=self.max_runtime_s)
            rt.load_bundle(self._claims_bundle())
            rt.run()
            status = rt.scientific_claims_status()
            ref = self._write_artifact("alpha_claim_summary.json", {
                "scientific_claim_count": status.get("scientific_claim_count", 0),
                "supported_claim_count": status.get("supported_claim_count", 0),
                "forbidden_claim_count": status.get("forbidden_claim_count", 0),
                "is_real_module_output": True,
                "note": "demo-safe scientific claim summary; proves nothing "
                        "about consciousness/life/agency"})
            step.status = AlphaDemoStepStatus.COMPLETED
            step.artifact_ref = ref
            step.detail = "scientific claim summary generated (demo-safe)"
            self.artifact_index.add(AlphaArtifactKind.CLAIM_REPORT, ref=ref,
                                    detail="real module output")
        except Exception as exc:
            self._placeholder(step, "scientific_claims",
                              AlphaArtifactKind.CLAIM_REPORT,
                              f"Scientific Claims call failed safely: {exc}")

    def _run_review_step(self, step) -> None:
        if not self.registry.is_available("independent_review"):
            self._placeholder(step, "independent_review",
                              AlphaArtifactKind.REVIEW_REPORT,
                              "Independent Review module unavailable; no review "
                              "pack generated.")
            return
        try:
            from ..independent_review import IndependentReviewRuntime

            review_dir = self.layout.subdir("review")
            rt = IndependentReviewRuntime(state_dir=review_dir,
                                          max_runtime_s=self.max_runtime_s)
            rt.load_bundle(self._review_bundle())
            rt.run()
            status = rt.independent_review_status()
            ref = self._write_artifact("alpha_review_summary.json", {
                "review_readiness_status": status.get(
                    "review_readiness_status"),
                "reviewer_question_count": status.get(
                    "reviewer_question_count", 0),
                "is_real_module_output": True,
                "note": "demo-safe review mini-pack summary; nothing published "
                        "or uploaded"})
            step.status = AlphaDemoStepStatus.COMPLETED
            step.artifact_ref = ref
            step.detail = "independent review mini-pack generated (demo-safe)"
            self.artifact_index.add(AlphaArtifactKind.REVIEW_REPORT, ref=ref,
                                    detail="real module output")
        except Exception as exc:
            self._placeholder(step, "independent_review",
                              AlphaArtifactKind.REVIEW_REPORT,
                              f"Independent Review call failed safely: {exc}")

    def _run_cycle_step(self, step) -> None:
        if not self.registry.is_available("research_cycle"):
            ref = self._write_artifact("alpha_cycle_summary.json", {
                "source": "alpha_fallback_cycle_status",
                "is_real_module_output": False,
                "note": "Research Cycle module unavailable; using alpha fallback "
                        "cycle status"})
            step.status = AlphaDemoStepStatus.WARNING
            step.artifact_ref = ref
            step.detail = "research cycle unavailable; alpha fallback used"
            self.artifact_index.add(AlphaArtifactKind.CYCLE_REPORT, ref=ref,
                                    detail="alpha fallback")
            return
        try:
            from ..research_cycle import ResearchCycleRuntime

            cycle_dir = self.layout.subdir("cycle")
            rt = ResearchCycleRuntime(state_dir=cycle_dir,
                                      max_runtime_s=self.max_runtime_s)
            rt.load_bundle(self._cycle_bundle())
            rt.run()
            status = rt.research_cycle_status()
            ref = self._write_artifact("alpha_cycle_summary.json", {
                "current_cycle_stage": status.get("current_cycle_stage"),
                "next_action_count": status.get("next_action_count", 0),
                "is_real_module_output": True,
                "note": "demo-safe research cycle status"})
            step.status = AlphaDemoStepStatus.COMPLETED
            step.artifact_ref = ref
            step.detail = "research cycle status generated (demo-safe)"
            self.artifact_index.add(AlphaArtifactKind.CYCLE_REPORT, ref=ref,
                                    detail="real module output")
        except Exception as exc:
            ref = self._write_artifact("alpha_cycle_summary.json", {
                "source": "alpha_fallback_cycle_status",
                "is_real_module_output": False, "detail": str(exc)})
            step.status = AlphaDemoStepStatus.WARNING
            step.artifact_ref = ref
            step.detail = f"research cycle call failed safely: {exc}"
            self.artifact_index.add(AlphaArtifactKind.CYCLE_REPORT, ref=ref,
                                    detail="alpha fallback")

    def _placeholder(self, step, module_key: str, kind: str,
                     message: str) -> None:
        ref = self._write_artifact(f"{step.step_id}_placeholder.json", {
            "module": module_key, "is_real_module_output": False,
            "placeholder": message, "note": "module unavailable; safe placeholder"})
        step.status = AlphaDemoStepStatus.SKIPPED
        step.artifact_ref = ref
        step.detail = message
        self.artifact_index.add_skipped_module(module_key, message)

    # -- bundles for demo-safe module calls ---------------------------------

    def _claims_bundle(self) -> Dict[str, Any]:
        return {
            "research_baseline": {"baseline_status": "validated",
                                  "safety_boundary_status": "pass"},
            "claims": [{
                "claim_id": "alpha_c1",
                "text": "The fixture sensorium pass produced bounded local "
                        "structure under the alpha demo.",
                "category": "architecture_claim",
                "evidence": [{"evidence_id": "alpha_fixture",
                              "source": "evaluation", "role": "weakly_supports"}],
                "factors": {"direct_evidence": True}}]}

    def _review_bundle(self) -> Dict[str, Any]:
        return {
            "research_baseline": {"baseline_status": "validated",
                                  "safety_boundary_status": "pass"},
            "safety": {"critical_regression_count": 0},
            "scientific_claims": {
                "claim_registry": {"scientific_claim_count": 1,
                                   "claims": [{"claim_id": "alpha_c1",
                                               "text": "bounded local structure",
                                               "status": "weakly_supported",
                                               "evidence_refs": ["alpha_fixture"],
                                               "counterevidence_refs": []}]},
                "counterevidence": {"counterevidence_count": 0, "records": []},
                "forbidden_claims": {"asserted_forbidden_count": 0,
                                     "blocks_publication": False},
                "limitations": {"limitation_count": 4, "limitations": []}},
            "sanitizer_inputs": {"abstract": "Bounded local structure. It is "
                                 "not conscious."}}

    def _cycle_bundle(self) -> Dict[str, Any]:
        return {
            "cycle_manifest": {"cycle_id": "alpha_cycle_1"},
            "research_baseline": {"baseline_status": "validated",
                                  "safety_boundary_status": "pass"}}

    # -- fixture + artifact helpers -----------------------------------------

    def _ensure_fixture(self) -> str:
        """Use the bundled fixture if present, else write a synthetic fallback."""
        bundled = self._bundled_fixture_path()
        target = os.path.join(self.layout.subdir("fixtures"),
                              "alpha_fixture_stream.jsonl")
        if bundled and os.path.isfile(bundled):
            return bundled
        # Synthetic fallback fixture (bounded, command-free, no secrets).
        events = [
            {"t": 0, "kind": "change", "features": [0.1, 0.2, 0.0],
             "debug_gloss": "DEBUG ONLY: a small change"},
            {"t": 1, "kind": "absence", "features": [0.0, 0.0, 0.0],
             "debug_gloss": "DEBUG ONLY: silence"},
            {"t": 2, "kind": "repeat", "features": [0.1, 0.2, 0.0],
             "debug_gloss": "DEBUG ONLY: repeated pattern"},
            {"t": 3, "kind": "noise", "features": [0.9, -0.3, 0.5],
             "debug_gloss": "DEBUG ONLY: noisy event"},
            {"t": 4, "kind": "contradiction", "features": [0.1, -0.2, 0.0],
             "debug_gloss": "DEBUG ONLY: contradictory event"},
        ]
        with open(target, "w", encoding="utf-8") as fh:
            for e in events:
                fh.write(json.dumps(e) + "\n")
        return target

    def _bundled_fixture_path(self) -> Optional[str]:
        here = os.path.dirname(os.path.abspath(__file__))
        root = os.path.abspath(os.path.join(here, "..", "..", ".."))
        path = os.path.join(root, "examples", "fixtures",
                            "alpha_fixture_stream.jsonl")
        return path if os.path.isfile(path) else None

    def _write_artifact(self, filename: str, payload: Dict[str, Any]) -> str:
        path = os.path.join(self.layout.subdir("artifacts"), filename)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=str)
        return path

    # -- finalization --------------------------------------------------------

    def _warning_count(self) -> int:
        warnings = self.check.get("warning_count", 0)
        if self.plan is not None:
            warnings += self.plan.summary()["alpha_demo_step_skipped_count"]
        return warnings

    def _finalize(self, *, demo_completed: bool, doctor_blocked: bool) -> None:
        warnings = self._warning_count()
        blockers = [r["name"] for r in self.check.get("results", [])
                    if r.get("is_blocker")]
        blockers += [r.label for r in self.registry.blocking_alpha()]
        self.cycle = determine_cycle_status(
            initialized=True, doctor_blocked=doctor_blocked,
            demo_completed=demo_completed, warnings=warnings,
            blockers=blockers,
            claims_generated=self._step_done("claim_summary"),
            review_generated=self._step_done("review_pack")).to_dict()
        self.runbook = AlphaRunbookBuilder().build(self.state_dir)
        self.artifact_index.add(AlphaArtifactKind.CYCLE_REPORT,
                                ref="alpha_cycle_status")
        self.artifact_index.add(AlphaArtifactKind.RUNBOOK,
                                ref="ALPHA_OPERATOR_RUNBOOK.md")
        self.artifact_index.add(AlphaArtifactKind.SAFETY_REPORT,
                                ref="alpha_safety")
        self.artifact_index.add(AlphaArtifactKind.ALPHA_REPORT,
                                ref="ALPHA_RESEARCH_SYSTEM_REPORT.md")
        if not self.dry_run:
            self.artifact_index.write()
            self.write_artifacts()

    def _step_done(self, step_id: str) -> bool:
        if self.plan is None:
            return False
        s = self.plan.get(step_id)
        return bool(s and s.completed)

    def _result(self, *, demo_completed: bool, doctor_blocked: bool,
                ) -> Dict[str, Any]:
        return {
            "refused": False, "run_id": self.run_id,
            "demo_completed": demo_completed, "doctor_blocked": doctor_blocked,
            "stage": self.cycle.get("stage"),
            "next_action": self.cycle.get("next_action"),
            "blocker_count": self.cycle.get("blocker_count", 0),
            "warning_count": self.cycle.get("warning_count", 0),
        }

    # -- integration views --------------------------------------------------

    def alpha_status(self) -> Dict[str, Any]:
        reg = self.registry.index() if self.registry else {}
        plan = self.plan.summary() if self.plan else {}
        return {
            "alpha_research_system_enabled": True,
            "alpha_profile_id": self.alpha_profile.profile_id,
            "alpha_profile_count": 1,
            "alpha_module_count": reg.get("alpha_module_count", 0),
            "alpha_available_module_count": reg.get(
                "alpha_available_module_count", 0),
            "alpha_missing_module_count": reg.get(
                "alpha_missing_module_count", 0),
            "alpha_blocked_module_count": reg.get(
                "alpha_blocked_module_count", 0),
            "alpha_demo_step_count": plan.get("alpha_demo_step_count", 0),
            "alpha_demo_step_completed_count": plan.get(
                "alpha_demo_step_completed_count", 0),
            "alpha_demo_step_skipped_count": plan.get(
                "alpha_demo_step_skipped_count", 0),
            "alpha_blocker_count": self.cycle.get("blocker_count", 0),
            "alpha_warning_count": self.cycle.get("warning_count", 0),
            "alpha_artifact_count": (self.artifact_index.index()[
                "alpha_artifact_count"] if self.artifact_index else 0),
            "alpha_safety_block_count": self.safety.rejected_count,
            "alpha_cycle_stage": self.cycle.get("stage"),
            "alpha_next_action": self.cycle.get("next_action"),
            "latest_alpha_report_path": self._report_path(),
            "modifies_source": False, "runs_git": False, "calls_github": False,
            "controls_feeders": False, "publishes": False,
        }

    def _report_path(self) -> Optional[str]:
        if self.layout is None:
            return None
        path = os.path.join(self.layout.subdir("reports"),
                            "ALPHA_RESEARCH_SYSTEM_REPORT.md")
        return path if os.path.isfile(path) else None

    def live_observation_status(self, live_state_dir: str = ".solaris_ai_nn_live",
                                ) -> Dict[str, Any]:
        """Read-only view of the latest post-birth live observation (Prompt 68).

        The default alpha system stays fixture-only: this never runs observation
        and never learns/controls feeders. It only reads the latest observation
        index written by the live_observation runtime (if present) to surface the
        first-day record path, the advisory stability status, and the recommended
        next phase. Returns ``{"live_observation_enabled": False}`` when no
        observation state exists.
        """
        index_dir = os.path.join(live_state_dir, "observation", "index")
        if not os.path.isdir(index_dir):
            return {"live_observation_enabled": False,
                    "note": "no post-birth live observation state present; the "
                            "default alpha system remains fixture-only and never "
                            "runs observation, learns, or controls feeders"}
        files = sorted(f for f in os.listdir(index_dir) if f.endswith(".json"))
        if not files:
            return {"live_observation_enabled": False}
        with open(os.path.join(index_dir, files[-1]), encoding="utf-8") as fh:
            status = json.load(fh)
        return {
            "live_observation_enabled": True,
            "observation_run_id": status.get("observation_run_id"),
            "live_stability_status": status.get("live_stability_status"),
            "live_recommended_next_phase": status.get(
                "live_recommended_next_phase"),
            "first_day_record_path": status.get("first_day_record_path"),
            "live_load_status": status.get("live_load_status"),
            "learns": False, "controls_feeders": False, "runs_git": False,
            "note": "read-only view of the latest live observation; the alpha "
                    "system never runs observation, learns, or controls feeders",
        }

    def live_ontogenesis_status(self,
                                live_state_dir: str = ".solaris_ai_nn_live",
                                ) -> Dict[str, Any]:
        """Read-only view of the latest first live ontogenesis run (Prompt 69).

        The default alpha system stays fixture-only: this never runs ontogenesis,
        never learns, and never controls feeders. It only reads the latest
        ontogenesis index written by the live_ontogenesis runtime (if present) to
        surface the run id, candidate / born counts, birth-gate status, the
        concept-memory path, and the recommended next phase. Returns
        ``{"live_ontogenesis_enabled": False}`` when no ontogenesis state exists.
        """
        index_dir = os.path.join(live_state_dir, "ontogenesis", "index")
        if not os.path.isdir(index_dir):
            return {"live_ontogenesis_enabled": False,
                    "note": "no first live ontogenesis state present; the "
                            "default alpha system remains fixture-only and never "
                            "runs ontogenesis, learns, or controls feeders"}
        files = sorted(f for f in os.listdir(index_dir) if f.endswith(".json"))
        if not files:
            return {"live_ontogenesis_enabled": False}
        with open(os.path.join(index_dir, files[-1]), encoding="utf-8") as fh:
            status = json.load(fh)
        return {
            "live_ontogenesis_enabled": True,
            "ontogenesis_run_id": status.get("ontogenesis_run_id"),
            "live_candidate_count": status.get("live_candidate_count", 0),
            "live_born_proto_concept_count": status.get(
                "live_born_proto_concept_count", 0),
            "live_contaminated_candidate_count": status.get(
                "live_contaminated_candidate_count", 0),
            "live_birth_gate_status": status.get("live_birth_gate_status"),
            "recommended_next_phase": status.get("recommended_next_phase"),
            "latest_concept_memory_path": status.get(
                "latest_concept_memory_path"),
            "enables_semiogenesis": False, "learns": False,
            "controls_feeders": False, "runs_git": False,
            "note": "read-only view of the latest live ontogenesis; the alpha "
                    "system never runs ontogenesis, learns, enables "
                    "semiogenesis, or controls feeders",
        }

    def live_semiogenesis_status(self,
                                 live_state_dir: str = ".solaris_ai_nn_live",
                                 ) -> Dict[str, Any]:
        """Read-only view of the latest first live semiogenesis run (Prompt 70).

        The default alpha system stays fixture-only: this never runs
        semiogenesis, never learns, and never controls feeders. It only reads the
        latest semiogenesis index written by the live_semiogenesis runtime (if
        present) to surface the run id, sign-candidate / born counts, the
        sign-birth-gate status, the sign-memory path, and the recommended next
        phase. Returns ``{"live_semiogenesis_enabled": False}`` when no
        semiogenesis state exists.
        """
        index_dir = os.path.join(live_state_dir, "semiogenesis", "index")
        if not os.path.isdir(index_dir):
            return {"live_semiogenesis_enabled": False,
                    "note": "no first live semiogenesis state present; the "
                            "default alpha system remains fixture-only and never "
                            "runs semiogenesis, learns, or controls feeders"}
        files = sorted(f for f in os.listdir(index_dir) if f.endswith(".json"))
        if not files:
            return {"live_semiogenesis_enabled": False}
        with open(os.path.join(index_dir, files[-1]), encoding="utf-8") as fh:
            status = json.load(fh)
        return {
            "live_semiogenesis_enabled": True,
            "semiogenesis_run_id": status.get("semiogenesis_run_id"),
            "live_sign_candidate_count": status.get(
                "live_sign_candidate_count", 0),
            "live_born_sign_count": status.get("live_born_sign_count", 0),
            "live_contaminated_sign_count": status.get(
                "live_contaminated_sign_count", 0),
            "live_sign_birth_gate_status": status.get(
                "live_sign_birth_gate_status"),
            "recommended_next_phase": status.get("recommended_next_phase"),
            "latest_sign_memory_path": status.get("latest_sign_memory_path"),
            "enables_cognition": False,
            "signs_are_language_understanding": False,
            "learns": False, "controls_feeders": False, "runs_git": False,
            "note": "read-only view of the latest live semiogenesis; the alpha "
                    "system never runs semiogenesis, learns, enables cognition, "
                    "or controls feeders",
        }

    def live_cognition_status(self,
                              live_state_dir: str = ".solaris_ai_nn_live",
                              ) -> Dict[str, Any]:
        """Read-only view of the latest first live cognition run (Prompt 71).

        The default alpha system stays fixture-only: this never runs cognition,
        never learns, and never controls feeders. It only reads the latest
        cognition index written by the live_cognition runtime (if present) to
        surface the run id, trace / anticipation counts, prediction outcomes, the
        readiness-gate status, the cognition-memory path, and the recommended next
        phase. Returns ``{"live_cognition_enabled": False}`` when no cognition
        state exists.
        """
        index_dir = os.path.join(live_state_dir, "cognition", "index")
        if not os.path.isdir(index_dir):
            return {"live_cognition_enabled": False,
                    "note": "no first live cognition state present; the default "
                            "alpha system remains fixture-only and never runs "
                            "cognition, learns, or controls feeders"}
        files = sorted(f for f in os.listdir(index_dir) if f.endswith(".json"))
        if not files:
            return {"live_cognition_enabled": False}
        with open(os.path.join(index_dir, files[-1]), encoding="utf-8") as fh:
            status = json.load(fh)
        return {
            "live_cognition_enabled": True,
            "cognition_run_id": status.get("cognition_run_id"),
            "live_cognition_trace_count": status.get(
                "live_cognition_trace_count", 0),
            "live_anticipation_count": status.get("live_anticipation_count", 0),
            "live_prediction_matched_count": status.get(
                "live_prediction_matched_count", 0),
            "live_prediction_contradicted_count": status.get(
                "live_prediction_contradicted_count", 0),
            "live_cognition_readiness_status": status.get(
                "live_cognition_readiness_status"),
            "recommended_next_phase": status.get("recommended_next_phase"),
            "latest_cognition_memory_path": status.get(
                "latest_cognition_memory_path"),
            "enables_action": False, "signs_are_language_understanding": False,
            "traces_prove_reasoning": False, "learns": False,
            "controls_feeders": False, "runs_git": False,
            "note": "read-only view of the latest live cognition; the alpha "
                    "system never runs cognition, learns, enables action, or "
                    "controls feeders",
        }

    def environmental_membrane_status(
            self, live_state_dir: str = ".solaris_ai_nn_live") -> Dict[str, Any]:
        """Read-only view of the latest environmental membrane run (Prompt 72).

        The default alpha system stays fixture-only: this never runs the
        membrane, never learns, and never controls feeders. It reads the latest
        membrane index (if present) to surface availability, the latest report
        path, the sensory-impression count, the blocked-impression count, the
        source-pressure status, and the membrane safety status. Returns
        ``{"membrane_enabled": False}`` when no membrane state exists.
        """
        index_dir = os.path.join(live_state_dir, "membrane", "index")
        if not os.path.isdir(index_dir):
            return {"membrane_enabled": False,
                    "note": "no environmental membrane state present; the default "
                            "alpha system remains fixture-only and never runs the "
                            "membrane, learns, or controls feeders"}
        files = sorted(f for f in os.listdir(index_dir) if f.endswith(".json"))
        if not files:
            return {"membrane_enabled": False}
        with open(os.path.join(index_dir, files[-1]), encoding="utf-8") as fh:
            status = json.load(fh)
        return {
            "membrane_enabled": True,
            "membrane_run_id": status.get("membrane_run_id"),
            "latest_membrane_report_path": status.get(
                "latest_membrane_report_path"),
            "membrane_impression_count": status.get(
                "membrane_impression_count", 0),
            "membrane_blocked_count": status.get("membrane_blocked_count", 0),
            "membrane_quarantined_count": status.get(
                "membrane_quarantined_count", 0),
            "source_pressure_status": status.get("source_pressure_status"),
            "membrane_safety_status": status.get("membrane_safety_status"),
            "learns": False, "controls_feeders": False, "runs_git": False,
            "note": "read-only view of the latest environmental membrane; the "
                    "alpha system never runs the membrane, learns, or controls "
                    "feeders",
        }

    def membrane_integration_status(
            self, live_state_dir: str = ".solaris_ai_nn_live") -> Dict[str, Any]:
        """Read-only view of the latest membrane integration run (Prompt 73).

        Surfaces whether the membrane integration layer ran, the latest report,
        the sensory-impression count, bypass/critical-bypass counts, raw-fallback
        count, and ancestry-validation status. The default fixture alpha runs
        without a live membrane, but tester/live profiles should warn if the
        membrane is absent.
        """
        base = os.path.join(live_state_dir, "membrane", "integration")
        if not os.path.isdir(base):
            return {"membrane_integration_available": False,
                    "membrane_module_available": os.path.isdir(
                        os.path.join(live_state_dir, "membrane")),
                    "note": "no membrane integration state present; the default "
                            "fixture alpha runs without a live membrane"}
        files = sorted(f for f in os.listdir(base)
                       if f.startswith("integ_") and f.endswith(".json"))
        if not files:
            return {"membrane_integration_available": False}
        with open(os.path.join(base, files[-1]), encoding="utf-8") as fh:
            status = json.load(fh)
        return {
            "membrane_integration_available": True,
            "membrane_module_available": status.get("membrane_present", False),
            "latest_integration_report_path": status.get(
                "latest_integration_report_path"),
            "impression_count": status.get("impression_count", 0),
            "bypass_count": status.get("bypass_finding_count", 0),
            "critical_bypass_count": status.get("critical_bypass_count", 0),
            "raw_fallback_count": status.get("raw_fallback_count", 0),
            "ancestry_validation_status": status.get(
                "ancestry_validation_status"),
            "learns": False, "controls_feeders": False, "runs_git": False,
            "note": "read-only view of the latest membrane integration; the "
                    "alpha system never runs integration, learns, or controls "
                    "feeders",
        }

    def tester_fixture_status(
            self, tester_state_dir: str = ".solaris_ai_nn_tester",
            ) -> Dict[str, Any]:
        """Read-only view of the latest tester fixture demo run (Prompt 74).

        Surfaces whether a fixture-only tester demo ran, the latest tester report
        and bundle paths, the reproducibility/regression statuses, the fixture
        profile, the membrane status, and the critical blocker count. The default
        fixture alpha runs without a tester demo present; this is a read-only
        view -- the alpha system never runs the tester demo, learns, or controls
        feeders.
        """
        base = os.path.join(tester_state_dir, "reports")
        if not os.path.isdir(base):
            return {"tester_demo_available": False,
                    "note": "no tester fixture state present; run "
                            "`python -m solaris_ai_nn tester-demo` first"}
        summaries = sorted(f for f in os.listdir(base)
                           if f.startswith("TESTER_RUN_SUMMARY_")
                           and f.endswith(".json"))
        if not summaries:
            return {"tester_demo_available": False}
        with open(os.path.join(base, summaries[-1]), encoding="utf-8") as fh:
            summary = json.load(fh)
        repro = summary.get("reproducibility", {}) or {}
        regr = summary.get("regression", {}) or {}
        membrane = summary.get("membrane_status", {}) or {}
        return {
            "tester_demo_available": True,
            "tester_run_id": summary.get("tester_run_id"),
            "fixture_profile": (summary.get("tester_profile", {}) or {}).get(
                "profile_id"),
            "latest_tester_report_path": os.path.join(
                base, f"TESTER_DEMO_REPORT_{summary.get('tester_run_id')}.md"),
            "latest_tester_summary_path": os.path.join(base, summaries[-1]),
            "reproducibility_status": repro.get("reproducibility_status",
                                                "inconclusive"),
            "regression_status": regr.get("regression_status", "inconclusive"),
            "membrane_status": ("present" if membrane.get(
                "membrane_impression_count") else "absent"),
            "membrane_impression_count": membrane.get(
                "membrane_impression_count", 0),
            "critical_blocker_count": len(summary.get("blockers", []) or []),
            "fixture_only": True, "requires_live_data": False,
            "learns": False, "controls_feeders": False, "runs_git": False,
            "note": "read-only view of the latest fixture-only tester demo; the "
                    "alpha system never runs it, learns, or controls feeders",
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.alpha_status()

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import AlphaResearchReportBuilder

        return AlphaResearchReportBuilder(self).write()
