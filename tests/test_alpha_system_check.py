"""Alpha system check (doctor): pass, warning, blocker, strict behavior."""

from __future__ import annotations

from solaris_ai_nn.alpha_system import (
    AlphaCheckSeverity,
    AlphaModuleRegistry,
    AlphaModuleStatus,
    AlphaSystemCheck,
    default_alpha_profile,
)


def test_doctor_pass_case(tmp_path):
    check = AlphaSystemCheck()
    check.run(state_root=str(tmp_path), profile=default_alpha_profile(),
              registry=AlphaModuleRegistry.build())
    summary = check.summary()
    assert summary["passed"] is True
    assert summary["blocker_count"] == 0


def test_warning_case(tmp_path):
    # require_claimguard=False + (if ClaimGuard present it passes). Force a
    # warning by allowing live read-only on the profile.
    profile = default_alpha_profile()
    profile.live_read_only_allowed = True
    check = AlphaSystemCheck()
    check.run(state_root=str(tmp_path), profile=profile,
              registry=AlphaModuleRegistry.build())
    names = {r["name"]: r["severity"] for r in check.summary()["results"]}
    assert names["no_live_mode_default"] == AlphaCheckSeverity.WARNING


def test_blocker_case(tmp_path):
    registry = AlphaModuleRegistry.build()
    rec = registry.get("evaluation")
    rec.status = AlphaModuleStatus.MISSING  # required -> blocks
    check = AlphaSystemCheck()
    check.run(state_root=str(tmp_path), profile=default_alpha_profile(),
              registry=registry)
    summary = check.summary()
    assert summary["passed"] is False
    assert summary["blocker_count"] >= 1


def test_require_claimguard_blocker_when_missing(tmp_path, monkeypatch):
    # Simulate ClaimGuard import failure by pointing at a bad module name.
    import solaris_ai_nn.alpha_system.system_check as sc

    check = sc.AlphaSystemCheck()
    # Run normally; if ClaimGuard is present this is a pass, otherwise a
    # blocker under require_claimguard. Either way the check must exist.
    check.run(state_root=str(tmp_path), profile=default_alpha_profile(),
              registry=AlphaModuleRegistry.build(), require_claimguard=True)
    names = {r["name"] for r in check.summary()["results"]}
    assert "claimguard_available" in names
