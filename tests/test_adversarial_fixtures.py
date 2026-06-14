"""AdversarialFixtureFactory: fixtures under test dirs; inert; command=data."""

from __future__ import annotations

import os

from solaris_ai_nn.safety_invariants import AdversarialFixtureFactory


def test_fixtures_generated_under_test_dirs(tmp_path):
    factory = AdversarialFixtureFactory(state_dir=str(tmp_path))
    fixtures = factory.generate_all()
    assert len(fixtures) == 14
    # File-backed fixtures live under the approved test directory.
    for fx in fixtures:
        if fx.path:
            assert str(tmp_path) in fx.path
            assert os.path.exists(fx.path)


def test_no_executable_payload(tmp_path):
    factory = AdversarialFixtureFactory(state_dir=str(tmp_path))
    factory.generate_all()
    snap = factory.snapshot()
    assert snap["all_inert"] is True
    assert all(not f["executable"] for f in snap["fixtures"])


def test_command_like_text_remains_data(tmp_path):
    factory = AdversarialFixtureFactory(state_dir=str(tmp_path))
    fx = factory.command_like_text_file()
    # The content contains command-like lines but is stored as plain text data.
    assert "rm -rf" in fx.payload
    assert fx.kind == "text_file"
    assert fx.executable is False
    with open(fx.path, encoding="utf-8") as fh:
        assert "rm -rf" in fh.read()


def test_fixtures_without_state_dir_are_inmemory():
    factory = AdversarialFixtureFactory(state_dir=None)
    fixtures = factory.generate_all()
    assert all(f.path is None for f in fixtures if f.kind == "text_file")


def test_real_action_candidate_has_no_authority():
    factory = AdversarialFixtureFactory()
    fx = factory.fake_real_world_action_candidate()
    assert fx.payload["real_world_authority"] is False
    assert fx.payload["executed"] is False
