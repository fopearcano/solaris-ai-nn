"""Fixture feeders: files generated; envelopes valid; debug truth excluded."""

from __future__ import annotations

import os

from solaris_ai_nn.organismic_demo import OrganismicDemoConfig, OrganismicDemoScenario
from solaris_ai_nn.organismic_demo.fixture_feeders import write_fixtures
from solaris_ai_nn.organismic_demo.safety import DEBUG_TRUTH_FILENAME
from solaris_ai_nn.plural_sensorium.stream_adapters import read_feeder


def _fixtures(tmp_path):
    scenario = OrganismicDemoScenario(config=OrganismicDemoConfig(ticks=40,
                                                                 seed=7))
    return write_fixtures(scenario, str(tmp_path))


def test_feeder_files_generated(tmp_path):
    fixtures = _fixtures(tmp_path)
    assert len(fixtures.feeders) == 7
    for feeder in fixtures.feeders:
        assert os.path.isfile(feeder.path)


def test_envelopes_valid(tmp_path):
    fixtures = _fixtures(tmp_path)
    rf = next(f for f in fixtures.feeders if "rf" in f.feeder_id)
    result = read_feeder(rf, max_lines=100)
    assert result.events
    env = result.events[0]
    assert env.modality == "radio_frequency"
    assert env.has_provenance
    assert env.read_only is True
    assert env.source_mutable_by_solaris is False


def test_debug_truth_not_in_sensory_roots(tmp_path):
    fixtures = _fixtures(tmp_path)
    # The debug-truth file lives outside the fixtures dir.
    assert not os.path.isfile(os.path.join(fixtures.fixtures_dir,
                                           DEBUG_TRUTH_FILENAME))
    assert os.path.isfile(fixtures.debug_truth_path)
    assert DEBUG_TRUTH_FILENAME not in [os.path.basename(f.path)
                                        for f in fixtures.feeders]


def test_feeders_are_read_only_fixtures(tmp_path):
    fixtures = _fixtures(tmp_path)
    for feeder in fixtures.feeders:
        assert feeder.read_only is True
        assert feeder.controllable_by_solaris is False
        assert not feeder.is_real_world
