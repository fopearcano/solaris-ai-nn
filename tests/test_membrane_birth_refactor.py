"""Live Birth refactor: certificate records environmental-membrane status."""

from __future__ import annotations

from solaris_ai_nn.live_birth.birth_certificate import BirthCertificateBuilder
from solaris_ai_nn.live_birth.birth_profile import default_live_birth_profile


def _build(env_membrane=None):
    return BirthCertificateBuilder().build(
        run_id="r1", profile=default_live_birth_profile(), governance_path="g",
        feeder_registry_path="f", allowed_sources=[], forbidden_sources=[],
        inbox_result={}, membrane={}, environmental_membrane=env_membrane)


def test_certificate_has_environmental_membrane_field():
    cert = _build({"environmental_membrane_available": True,
                   "live_birth_bypasses_membrane": False})
    em = cert.fields["environmental_membrane"]
    assert em["environmental_membrane_available"] is True
    assert em["live_birth_bypasses_membrane"] is False


def test_certificate_membrane_defaults_empty():
    cert = _build()
    assert cert.fields["environmental_membrane"] == {}


def test_environmental_membrane_status_no_bypass(tmp_path):
    from solaris_ai_nn.live_birth.birth_runtime import LiveReadOnlyBirthRuntime

    rt = LiveReadOnlyBirthRuntime(state_dir=str(tmp_path))
    status = rt.environmental_membrane_status()
    assert status["live_birth_bypasses_membrane"] is False
    assert "environmental_membrane_available" in status
