"""PrivacyFilter: flags assigned; raw private warning; metadata-only accepted."""

from __future__ import annotations

from solaris_ai_nn.feeder_sdk import PrivacyFilter, PrivacyFlag, PrivacyRisk


def test_privacy_flags_assigned():
    report = PrivacyFilter().assess({"modality": "radio_frequency",
                                     "features": {"power": 0.5}})
    assert PrivacyFlag.CONTAINS_RF_FEATURES_ONLY in report.flags
    assert PrivacyFlag.NO_RAW_PRIVATE_CONTENT in report.flags
    assert report.blocked is False


def test_raw_private_content_warning():
    report = PrivacyFilter().assess({"modality": "radio_frequency",
                                     "features": {"decoded_message": "x"}})
    assert report.blocked is True
    assert report.risk == PrivacyRisk.HIGH
    assert report.warnings


def test_metadata_only_accepted():
    report = PrivacyFilter().assess({"modality": "vibration",
                                     "features": {"amplitude": 0.3}})
    assert report.blocked is False
    assert PrivacyFlag.METADATA_ONLY in report.flags


def test_human_text_flagged_and_warned():
    report = PrivacyFilter().assess({"modality": "human_textual",
                                     "features": {"length": 5.0},
                                     "annotation": "rain"})
    assert PrivacyFlag.CONTAINS_HUMAN_TEXT in report.flags
    assert PrivacyFlag.CONTAINS_EXTERNAL_ANNOTATION in report.flags
    assert report.warnings


def test_apply_merges_flags():
    out = PrivacyFilter().apply({"modality": "radio_frequency",
                                 "features": {"power": 0.5},
                                 "privacy_flags": []})
    assert PrivacyFlag.NO_RAW_PRIVATE_CONTENT in out["privacy_flags"]
