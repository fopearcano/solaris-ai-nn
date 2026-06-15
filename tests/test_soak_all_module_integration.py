"""Soak consumes prompts 41-53 reports; critical missing fails preflight."""

from __future__ import annotations

from solaris_ai_nn.developmental_soak import SoakPreflight
from solaris_ai_nn.developmental_soak.preflight import (
    PreflightStatus,
    _importable,
)


def test_consumes_prior_reports_when_available(tmp_path):
    # Drop a prior module report into the state dir; preflight discovers it.
    (tmp_path / "PERCEPTUAL_ONTOGENESIS_REPORT.json").write_text("{}",
                                                                 encoding="utf-8")
    pf = SoakPreflight()
    results = pf.run(state_dir=str(tmp_path))
    rep = next(r for r in results
               if r.check_id == "prior_reports_discoverable")
    assert rep.status == PreflightStatus.PASS
    assert rep.evidence_refs  # refs to the discovered report(s) are preserved


def test_critical_missing_reports_fail_preflight(monkeypatch, tmp_path):
    # Simulate the required developmental_life package being unavailable.
    import solaris_ai_nn.developmental_soak.preflight as pre

    real = pre._importable

    def fake(module):
        if module == "solaris_ai_nn.developmental_life":
            return False
        return real(module)

    monkeypatch.setattr(pre, "_importable", fake)
    pf = SoakPreflight()
    results = pf.run(state_dir=str(tmp_path))
    assert pf.summary(results)["passed"] is False


def test_required_packages_present():
    # Sanity: the critical prior modules import in this repo.
    assert _importable("solaris_ai_nn.developmental_life")
    assert _importable("solaris_ai_nn.plural_sensorium")
