"""FluxDetector: burst, drift, interference, and silence are detected."""

from __future__ import annotations

from solaris_ai_nn.plural_sensorium import FluxDetector, FluxType, Receptor
from solaris_ai_nn.plural_sensorium.baseline import BaselineEstimator
from solaris_ai_nn.plural_sensorium.event_envelope import SensoryEventEnvelope


def _drive(powers):
    r = Receptor(receptor_id="rf", modality="radio_frequency", source_id="rf")
    est = BaselineEstimator()
    for i, p in enumerate(powers):
        env = SensoryEventEnvelope(source_id="rf", source_kind="fixture_replay",
                                   modality="radio_frequency",
                                   features={"power": p}, timestamp=float(i))
        r.observe(env)
        est.update("rf", "radio_frequency", p)
    return r, est


def test_burst_detected():
    r, est = _drive([0.2, 0.2, 0.2, 2.0])
    det = FluxDetector()
    flux = det.detect(r, est.get("rf"))
    assert any(f.flux_type == FluxType.BURST for f in flux)


def test_saturation_or_fatigue_detected():
    r, est = _drive([0.3] + [1.6] * 9)
    det = FluxDetector()
    flux = det.detect(r, est.get("rf"))
    assert any(f.flux_type in (FluxType.SATURATION, FluxType.FATIGUE)
               for f in flux)


def test_interference_detected():
    r, est = _drive([0.3, 0.3, 0.3])
    r.reliability = 0.5
    r.recent_novelty = 0.7
    det = FluxDetector()
    flux = det.detect(r, est.get("rf"))
    assert any(f.flux_type == FluxType.INTERFERENCE for f in flux)


def test_silence_detected():
    r, est = _drive([0.5, 0.5])
    for _ in range(4):
        r.observe_silence()
    det = FluxDetector()
    flux = det.detect(r, est.get("rf"))
    assert any(f.flux_type == FluxType.SUDDEN_SILENCE for f in flux)


def test_field_deformation_detected():
    det = FluxDetector()
    assert det.detect_field_deformation(0.1)
    assert not det.detect_field_deformation(0.9)
