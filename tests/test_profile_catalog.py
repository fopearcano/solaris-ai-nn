"""ProfileCatalog: profiles indexed; long/prohibited blocked; no authority."""

from __future__ import annotations

from solaris_ai_nn.operator_console import ProfileCatalog, ProfileSafetyClass


def test_profiles_indexed():
    catalog = ProfileCatalog()
    assert len(catalog.entries()) > 20
    # safety, research, architecture, and pilot profiles are all present.
    ids = {e.profile_id for e in catalog.entries()}
    assert "safety_fast_check" in ids
    assert "research_baseline_random" in ids
    assert "architecture_review" in ids


def test_long_run_soak_blocked():
    catalog = ProfileCatalog()
    entry = catalog.get("pilot1_30d_soak")
    assert entry is not None
    assert entry.safety_class == \
        ProfileSafetyClass.LONG_RUN_REQUIRES_GOVERNANCE
    assert entry.can_run_from_console is False


def test_no_external_authority():
    catalog = ProfileCatalog()
    assert not any(e.external_authority for e in catalog.entries())
    assert catalog.summary()["any_external_authority"] is False


def test_runnable_and_blocked_partition():
    catalog = ProfileCatalog()
    runnable = {e.profile_id for e in catalog.runnable_entries()}
    blocked = {e.profile_id for e in catalog.blocked_entries()}
    assert runnable.isdisjoint(blocked)
    assert runnable | blocked == {e.profile_id for e in catalog.entries()}


def test_bounded_profile_runnable():
    catalog = ProfileCatalog()
    assert catalog.is_runnable("safety_fast_check")
