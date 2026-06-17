"""RC artifact collector: required collected, recommended warn, no private/upload."""

from __future__ import annotations

from _tester_rc_helpers import seed_ready_state

from solaris_ai_nn.tester_release_candidate import TesterRCArtifactCollector


def test_required_artifacts_collected(tmp_path):
    base = str(tmp_path / "ready")
    seed_ready_state(base)
    res = TesterRCArtifactCollector(tester_state_dir=base).collect()
    # Repo-level required docs always exist.
    assert res.present("readme")
    assert res.present("forbidden_claims_doc")
    assert res.present("install_guide")


def test_recommended_missing_warns(tmp_path):
    res = TesterRCArtifactCollector(
        tester_state_dir=str(tmp_path / "empty")).collect()
    d = res.to_dict()
    assert d["missing_recommended_count"] >= 0
    # Recommended missing never appears in the required-missing list.
    for k in d["missing_recommended"]:
        assert k not in d["missing_required"]


def test_private_payloads_excluded_by_default(tmp_path):
    res = TesterRCArtifactCollector(
        tester_state_dir=str(tmp_path / "x")).collect()
    assert res.to_dict()["includes_private_payloads"] is False


def test_no_upload_publish(tmp_path):
    d = TesterRCArtifactCollector(
        tester_state_dir=str(tmp_path / "x")).collect().to_dict()
    assert d["uploaded"] is False
    assert d["published"] is False
    assert d["local_only"] is True
