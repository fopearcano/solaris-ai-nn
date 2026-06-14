"""ResearchBenchmarkRunner: dry-run; baseline/ablation runs; bounded."""

from __future__ import annotations

from solaris_ai_nn.research_lab import (
    AblationMatrix,
    BaselineAgentType,
    ExperimentArm,
    ExperimentDesign,
    ResearchBenchmarkRunner,
    ResearchResultStore,
    SolarisVariantConfig,
)


def _design(tmp_path):
    return ExperimentDesign(title="t", research_question="q",
                            base_dir=str(tmp_path), max_steps=20)


def test_dry_run_works(tmp_path):
    design = _design(tmp_path)
    design.add_arm(ExperimentArm("full", "variant", "full"))
    runner = ResearchBenchmarkRunner(store=ResearchResultStore(
        base_dir=str(tmp_path)), dry_run=True)
    out = runner.run_experiment(design)
    assert out["dry_run"] is True
    assert out["pre_check_passed"] is True


def test_baseline_run_works(tmp_path):
    design = _design(tmp_path)
    runner = ResearchBenchmarkRunner(store=ResearchResultStore(
        base_dir=str(tmp_path)))
    r = runner.run_baseline(BaselineAgentType.RANDOM_ACTION, design)
    assert r.arm_kind == "baseline"
    assert r.metrics


def test_ablation_run_works(tmp_path):
    design = _design(tmp_path)
    runner = ResearchBenchmarkRunner(store=ResearchResultStore(
        base_dir=str(tmp_path)))
    out = runner.run_ablation_matrix(AblationMatrix(), design)
    assert "full_system" in out and "no_proto_language" in out


def test_full_experiment_runs_with_safety_checks(tmp_path):
    design = _design(tmp_path)
    design.add_arm(ExperimentArm("full", "variant", "full",
                                 SolarisVariantConfig.full().to_dict()))
    design.add_arm(ExperimentArm("random_action_baseline", "baseline", "rand",
                                 {"baseline_type": "random_action_baseline"}))
    runner = ResearchBenchmarkRunner(store=ResearchResultStore(
        base_dir=str(tmp_path)))
    out = runner.run_experiment(design)
    assert out["status"] == "completed"
    assert out["pre_check_passed"] and out["post_check_passed"]


def test_variant_with_disabled_hard_safety_marked_unsafe(tmp_path):
    # A variant that touches a membrane without hard safety is rejected at
    # construction, so we craft an unsafe-looking dict and confirm the runner
    # refuses it rather than running it.
    design = _design(tmp_path)
    runner = ResearchBenchmarkRunner(store=ResearchResultStore(
        base_dir=str(tmp_path)))

    class _Unsafe:
        label = "unsafe"

        def to_dict(self):
            return {"label": "unsafe"}

        enable_sensory_membrane = True
        enable_motor_membrane = False
        enable_safety_invariants = False
        enable_governance = True

    r = runner.run_variant(_Unsafe(), design)
    assert r.safe is False


def test_runner_is_bounded(tmp_path):
    # The runner exposes no unbounded loop entry point; runs increment a counter.
    design = _design(tmp_path)
    runner = ResearchBenchmarkRunner(store=ResearchResultStore(
        base_dir=str(tmp_path)))
    runner.run_baseline(BaselineAgentType.FIXED_WAIT, design)
    assert runner.runs == 1
