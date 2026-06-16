"""Birth certificate: generated, first event recorded, disclaimer present."""

from __future__ import annotations

import os

from solaris_ai_nn.live_birth import (
    BirthCertificateBuilder,
    default_live_birth_profile,
)


def _build(tmp_path):
    profile = default_live_birth_profile()
    builder = BirthCertificateBuilder(state_dir=str(tmp_path))
    cert = builder.build(
        run_id="run_1", profile=profile, governance_path="g",
        feeder_registry_path="f", allowed_sources=profile.allowed_sources,
        forbidden_sources=profile.forbidden_sources,
        inbox_result={"live_inbox_file_count": 1,
                      "live_event_accepted_count": 6,
                      "live_event_quarantined_count": 5},
        membrane={"membrane_activated": True, "first_event_id": "ev1",
                  "first_event_timestamp": "2026-06-16T18:00:00Z",
                  "first_absence_event_id": "ev2",
                  "first_operator_pulse_id": "ev_pulse"})
    return builder, cert


def test_certificate_generated(tmp_path):
    builder, cert = _build(tmp_path)
    paths = builder.write(cert)
    assert os.path.isfile(paths["markdown"])
    assert os.path.isfile(paths["json"])


def test_first_event_recorded(tmp_path):
    _, cert = _build(tmp_path)
    d = cert.to_dict()
    assert d["first_accepted_event_id"] == "ev1"
    assert d["first_absence_event_id"] == "ev2"
    assert d["first_operator_pulse_id"] == "ev_pulse"
    assert d["accepted_event_count"] == 6


def test_disclaimer_present(tmp_path):
    _, cert = _build(tmp_path)
    md = cert.render_md().lower()
    assert "does not imply consciousness" in md
    assert "operational live-read-only birth" in md
    assert cert.to_dict()["disclaimer"]
