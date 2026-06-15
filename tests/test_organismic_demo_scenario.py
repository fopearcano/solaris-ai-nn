"""OrganismicDemoScenario: phases exist; bounded; uncertain; debug excluded."""

from __future__ import annotations

from solaris_ai_nn.organismic_demo import (
    OrganismicDemoConfig,
    OrganismicDemoPhase,
    OrganismicDemoScenario,
)
from solaris_ai_nn.organismic_demo.scenario import DEBUG_TRUTH_FILE, FEEDER_FILES


def test_phases_exist():
    for phase in ("baseline_exposure", "rhythm_establishment",
                  "cross_modal_coupling", "absence_disruption",
                  "novelty_injection", "recovery", "changed_perception_probe",
                  "report_only"):
        assert phase in OrganismicDemoPhase.ALL


def test_scenario_bounded():
    scenario = OrganismicDemoScenario(config=OrganismicDemoConfig(ticks=40))
    streams, _debug = scenario.generate()
    total = sum(len(v) for v in streams.values())
    # Bounded by ticks * a small per-tick fan-out.
    assert total < 40 * 30


def test_uncertainty_and_jitter_included():
    # Two different seeds produce different worlds (not perfectly scripted).
    a, _ = OrganismicDemoScenario(OrganismicDemoConfig(ticks=60, seed=1)
                                  ).generate()
    b, _ = OrganismicDemoScenario(OrganismicDemoConfig(ticks=60, seed=2)
                                  ).generate()
    assert a["rf_feature_stream.jsonl"] != b["rf_feature_stream.jsonl"]


def test_replayable_by_seed():
    a, _ = OrganismicDemoScenario(OrganismicDemoConfig(ticks=60, seed=7)
                                  ).generate()
    b, _ = OrganismicDemoScenario(OrganismicDemoConfig(ticks=60, seed=7)
                                  ).generate()
    assert a == b


def test_debug_truth_excluded_from_feeders():
    # The debug-truth file is not one of the sensory feeder files.
    assert DEBUG_TRUTH_FILE not in FEEDER_FILES
    _streams, debug = OrganismicDemoScenario(
        OrganismicDemoConfig(ticks=60, seed=7)).generate()
    # Debug truth records exist but are returned separately, never as a stream.
    assert isinstance(debug, list)
