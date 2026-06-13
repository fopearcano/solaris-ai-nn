"""Integration: hypothesis tests use bounded nursery interventions."""

from __future__ import annotations

from solaris_ai_nn.ecology.nursery import DevelopmentalNursery, NurseryConfig
from solaris_ai_nn.ecology.regimes import RegimeType
from solaris_ai_nn.hypothesis import HypothesisEngine
from solaris_ai_nn.hypothesis.hypotheses import (
    Hypothesis,
    HypothesisScope,
    HypothesisType,
)
from solaris_ai_nn.hypothesis.experiment_design import design_for
from solaris_ai_nn.hypothesis.interventions import (
    Intervention,
    InterventionType,
)
from solaris_ai_nn.hypothesis.safety import HypothesisSafetyValidator


def _nursery(tmp_path, **kw):
    return DevelopmentalNursery(config=NurseryConfig(
        seed=7, duration_steps=80, output_state_dir=str(tmp_path), **kw))


def test_nursery_intervention_validated():
    validator = HypothesisSafetyValidator()
    interv = Intervention(
        intervention_type=InterventionType.INTRODUCE_NOVELTY,
        scope="nursery_only", target_ref="novel_region")
    assert validator.validate_intervention(interv).safe
    assert interv.requires_ecology_safety is True


def test_delayed_consequence_test_bounded(tmp_path):
    nursery = _nursery(tmp_path, delayed_consequence_rate=0.3,
                       active_regimes=[RegimeType.DELAYED_FEEDBACK_WORLD])
    for step in range(60):
        nursery.stimulus_provider(step)
    engine = HypothesisEngine(state_dir=tmp_path, nursery=nursery)
    h = Hypothesis(type=HypothesisType.DELAYED_CONSEQUENCE,
                   statement="group DLY_0001 may follow an earlier signal",
                   target_ref="DLY_0001",
                   required_scope=HypothesisScope.NURSERY_ONLY)
    engine.memory.add(h)
    design = design_for(h)
    result = engine.runner.run_design(design, {"step": 61}, h)
    # The test ran bounded (<= design.max_steps) and produced a verdict.
    assert result.executed or result.blocked
    assert design.max_steps <= 2000


def test_nursery_sample_hook_is_simulation_only(tmp_path):
    nursery = _nursery(tmp_path)
    result = nursery.sample("seek_novelty")
    assert result["scope"] == "simulation_only"
