"""RC manifest: generated, readiness computed, missing optional warn, required block."""

from __future__ import annotations

from _tester_rc_helpers import run_rc, seed_ready_state


def test_manifest_generated(tmp_path):
    rt = run_rc(str(tmp_path / "rc"))
    m = rt.manifest.to_dict()
    assert m["rc_id"]
    assert m["package_name"]
    assert m["implies_publication"] is False
    assert m["published"] is False


def test_readiness_status_computed(tmp_path):
    rt = run_rc(str(tmp_path / "rc"))
    # Fresh state has no packaging/safety-freeze -> blocked.
    assert rt.manifest.readiness in ("blocked", "critical_blocked")


def test_missing_optional_modules_warning_only(tmp_path):
    rt = run_rc(str(tmp_path / "rc"))
    m = rt.manifest.to_dict()
    # Optional modules absent in a fixture-only state: listed, not blocking.
    assert m["known_missing_optional_modules"]
    assert "ontogenesis report" in m["known_missing_optional_modules"]


def test_missing_required_artifacts_block(tmp_path):
    rt = run_rc(str(tmp_path / "rc"))
    assert rt.manifest.missing_required_artifact_count > 0
    assert rt.manifest.readiness in ("blocked", "critical_blocked")


def test_ready_state_manifest(tmp_path):
    base = str(tmp_path / "ready")
    seed_ready_state(base)
    rt = run_rc(base)
    assert rt.manifest.missing_required_artifact_count == 0
    assert rt.manifest.readiness in ("ready_for_first_tester",
                                     "ready_with_warnings")


def test_commit_hash_unknown_allowed(tmp_path):
    rt = run_rc(str(tmp_path / "rc"))
    assert isinstance(rt.manifest.commit_hash, str)
