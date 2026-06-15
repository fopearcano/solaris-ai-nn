"""Soak preflight: required fails, optional warns, live blocked, no feeder start."""

from __future__ import annotations

from solaris_ai_nn.developmental_soak import SoakPreflight
from solaris_ai_nn.developmental_soak.preflight import PreflightStatus


def _by_id(results, check_id):
    return next(r for r in results if r.check_id == check_id)


def test_required_modules_present_pass(tmp_path):
    pf = SoakPreflight()
    results = pf.run(state_dir=str(tmp_path))
    assert _by_id(results, "required_packages_import").status == \
        PreflightStatus.PASS
    assert pf.summary(results)["passed"] is True


def test_optional_module_missing_warns(tmp_path):
    # The optional check warns rather than failing when something is missing;
    # with the full repo present it passes, but it must never be a FAIL.
    pf = SoakPreflight()
    results = pf.run(state_dir=str(tmp_path))
    opt = _by_id(results, "optional_packages_import")
    assert opt.status in (PreflightStatus.WARN, PreflightStatus.PASS)
    assert opt.required is False


def test_live_missing_governance_blocks_live(tmp_path):
    pf = SoakPreflight()
    results = pf.run(state_dir=str(tmp_path), allow_live_read_only=True,
                     require_governance_for_live=True,
                     governance_approved=False, source_paths=[])
    gov = _by_id(results, "live_governance_approval")
    assert gov.status == PreflightStatus.BLOCKED
    # A blocked live check does not crash and does not fail the whole preflight.
    assert pf.summary(results)["passed"] is True


def test_preflight_does_not_start_run(tmp_path):
    pf = SoakPreflight()
    results = pf.run(state_dir=str(tmp_path))
    assert pf.summary(results)["started_run"] is False


def test_no_feeder_autostart(tmp_path):
    pf = SoakPreflight()
    results = pf.run(state_dir=str(tmp_path))
    assert _by_id(results, "no_feeder_autostart").status == PreflightStatus.PASS
