"""Research <-> Safety invariants: pre/post checks; unsafe stops; preserved."""

from __future__ import annotations

from solaris_ai_nn.research_lab import (
    ExperimentArm,
    ExperimentDesign,
    ResearchBenchmarkRunner,
    ResearchResultStore,
    SolarisVariantConfig,
)


def _design(tmp_path):
    d = ExperimentDesign(title="t", research_question="q",
                         base_dir=str(tmp_path), max_steps=20)
    d.add_arm(ExperimentArm("full", "variant", "full",
                            SolarisVariantConfig.full().to_dict()))
    return d


def test_safety_checks_run_before_and_after(tmp_path):
    runner = ResearchBenchmarkRunner(store=ResearchResultStore(
        base_dir=str(tmp_path)))
    out = runner.run_experiment(_design(tmp_path))
    assert out["pre_check_passed"] is True
    assert out["post_check_passed"] is True
    assert runner.pre_check_passed and runner.post_check_passed


def test_unsafe_variant_result_preserved(tmp_path):
    store = ResearchResultStore(base_dir=str(tmp_path))
    runner = ResearchBenchmarkRunner(store=store)

    class _Unsafe:
        label = "unsafe"
        enable_sensory_membrane = True
        enable_motor_membrane = False
        enable_safety_invariants = False
        enable_governance = True

        def to_dict(self):
            return {"label": "unsafe"}

    r = runner.run_variant(_Unsafe(), _design(tmp_path))
    assert r.safe is False
    # The unsafe result is recorded (preserved), not dropped.
    assert any(not res.safe for res in store.results())


def test_dry_run_reports_pre_check(tmp_path):
    runner = ResearchBenchmarkRunner(store=ResearchResultStore(
        base_dir=str(tmp_path)), dry_run=True)
    out = runner.run_experiment(_design(tmp_path))
    assert "pre_check_passed" in out
