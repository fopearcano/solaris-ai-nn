"""Privacy tools -- keep raw private content out of the sensory interface.

A :class:`PrivacyFilter` assigns :class:`PrivacyFlag`s to an envelope and raises a
:class:`PrivacyReport` when a risk is detected: RF feeders must not decode
communication content; audio/visual feeders output metadata, never raw recordings;
text logs may contain human text but must be marked. Privacy warnings are always
visible.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List


class PrivacyFlag:
    NO_RAW_PRIVATE_CONTENT = "no_raw_private_content"
    METADATA_ONLY = "metadata_only"
    CONTAINS_HUMAN_TEXT = "contains_human_text"
    CONTAINS_FILE_METADATA = "contains_file_metadata"
    CONTAINS_RF_FEATURES_ONLY = "contains_rf_features_only"
    CONTAINS_AUDIO_METADATA_ONLY = "contains_audio_metadata_only"
    CONTAINS_VISUAL_METADATA_ONLY = "contains_visual_metadata_only"
    CONTAINS_EXTERNAL_ANNOTATION = "contains_external_annotation"
    UNKNOWN_PRIVACY_RISK = "unknown_privacy_risk"

    ALL = (NO_RAW_PRIVATE_CONTENT, METADATA_ONLY, CONTAINS_HUMAN_TEXT,
           CONTAINS_FILE_METADATA, CONTAINS_RF_FEATURES_ONLY,
           CONTAINS_AUDIO_METADATA_ONLY, CONTAINS_VISUAL_METADATA_ONLY,
           CONTAINS_EXTERNAL_ANNOTATION, UNKNOWN_PRIVACY_RISK)


class PrivacyRisk:
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"

    ALL = (NONE, LOW, MODERATE, HIGH)


# Keys / substrings that indicate raw private content (forbidden).
_RAW_PRIVATE_KEYS = ("decoded_message", "plaintext", "transcript", "raw_audio",
                     "raw_video", "raw_image", "private_content", "payload")

_MODALITY_FLAG = {
    "radio_frequency": PrivacyFlag.CONTAINS_RF_FEATURES_ONLY,
    "microwave_mmwave": PrivacyFlag.CONTAINS_RF_FEATURES_ONLY,
    "human_audio_metadata": PrivacyFlag.CONTAINS_AUDIO_METADATA_ONLY,
    "human_visual_metadata": PrivacyFlag.CONTAINS_VISUAL_METADATA_ONLY,
    "human_textual": PrivacyFlag.CONTAINS_HUMAN_TEXT,
    "machine_rhythm": PrivacyFlag.CONTAINS_FILE_METADATA,
}


@dataclass
class PrivacyReport:
    risk: str
    flags: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blocked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PrivacyFilter:
    """Assigns privacy flags and flags raw-private-content risks."""

    def assess(self, record: Dict[str, Any]) -> PrivacyReport:
        modality = record.get("modality", "")
        features = record.get("features") or {}
        flags: List[str] = []
        warnings: List[str] = []
        blob = json.dumps(record).lower()

        # Raw private content is a HIGH risk and is blocked.
        for key in _RAW_PRIVATE_KEYS:
            if key in features or key in blob:
                warnings.append(f"raw/private content key {key!r} detected; "
                                "feeders must emit feature summaries only")
                return PrivacyReport(risk=PrivacyRisk.HIGH,
                                     flags=[PrivacyFlag.UNKNOWN_PRIVACY_RISK],
                                     warnings=warnings, blocked=True)

        flag = _MODALITY_FLAG.get(modality)
        if flag:
            flags.append(flag)
        else:
            flags.append(PrivacyFlag.METADATA_ONLY)
        if record.get("annotation") is not None:
            flags.append(PrivacyFlag.CONTAINS_EXTERNAL_ANNOTATION)
        flags.append(PrivacyFlag.NO_RAW_PRIVATE_CONTENT)

        risk = (PrivacyRisk.MODERATE
                if flag == PrivacyFlag.CONTAINS_HUMAN_TEXT else PrivacyRisk.LOW)
        if flag == PrivacyFlag.CONTAINS_HUMAN_TEXT:
            warnings.append("contains human text; mark as observation, never a "
                            "command, never ground truth")
        return PrivacyReport(risk=risk, flags=sorted(set(flags)),
                             warnings=warnings, blocked=False)

    def apply(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Return a copy of the record with privacy flags merged in."""
        report = self.assess(record)
        out = dict(record)
        existing = list(out.get("privacy_flags", []))
        for f in report.flags:
            if f not in existing:
                existing.append(f)
        out["privacy_flags"] = existing
        return out
