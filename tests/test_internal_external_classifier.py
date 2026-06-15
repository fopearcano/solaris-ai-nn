"""InternalExternalClassifier: internal/external/mixed; sensory not auto-self."""

from __future__ import annotations

from solaris_ai_nn.self_boundary import (
    InternalExternalClassifier,
    InternalExternalLabel,
)


def test_internal_external_mixed_classifications():
    clf = InternalExternalClassifier()
    internal = clf.classify("c1", "perceptual_ontogenesis")
    external = clf.classify("f1", "feeder_sdk")
    mixed = clf.classify("r1", "plural_sensorium")
    assert internal.label == InternalExternalLabel.INTERNAL
    assert external.label == InternalExternalLabel.EXTERNAL
    assert mixed.label == InternalExternalLabel.MIXED
    assert mixed.is_mixed is True


def test_processed_sensory_input_not_automatically_self():
    clf = InternalExternalClassifier()
    # Plural-sensorium records read the external world via internal receptors:
    # they are MIXED, never silently collapsed into internal-self.
    c = clf.classify("r1", "plural_sensorium")
    assert c.label != InternalExternalLabel.INTERNAL
    assert c.external_component is True
    assert "not silently collapsed into internal-self" in c.to_dict()["note"]


def test_mixed_records_are_explicit():
    clf = InternalExternalClassifier()
    clf.classify("r1", "plural_sensorium")
    clf.classify("c1", "semiogenesis")
    assert len(clf.mixed()) == 1
    dist = clf.distribution()
    assert dist.get(InternalExternalLabel.MIXED, 0) == 1


def test_unknown_origin():
    clf = InternalExternalClassifier()
    c = clf.classify("x", "mystery_origin")
    assert c.label == InternalExternalLabel.UNKNOWN
