"""Shared helpers for tester live-read-only tests (not a test module)."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.tester_live_readonly import (
    GovernanceTemplateBuilder,
    TesterFeederTemplateBuilder,
)


def approve_governance(state_dir, *, allowed_extra=None, forbidden_extra=None):
    """Write an enabled+approved governance file (simulates the tester's edit)."""
    gov = GovernanceTemplateBuilder().build().to_dict()
    gov.update(live_readonly_enabled=True, operator_approved=True,
               approved_by="Tester", approved_at_utc="2026-06-17T00:00:00Z")
    if allowed_extra:
        gov["allowed_sources"] = list(gov["allowed_sources"]) + list(allowed_extra)
    os.makedirs(os.path.join(state_dir, "governance"), exist_ok=True)
    path = os.path.join(state_dir, "governance",
                        "LIVE_READONLY_GOVERNANCE.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(gov, fh, indent=2)
    return path


def write_feeder_registry(state_dir):
    return TesterFeederTemplateBuilder().write_live_registry(
        state_dir, overwrite=True)
