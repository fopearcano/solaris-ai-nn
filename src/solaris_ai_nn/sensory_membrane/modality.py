"""Sensory modality model -- what kind of environmental signal this is.

Modalities are deliberately metadata-only for camera/audio in this prompt:
the membrane performs no OCR, no speech recognition, and no image analysis.
Future adapters may add local processing behind governance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SensoryModality:
    TEXTUAL = "textual"
    NUMERIC = "numeric"
    FILE_PRESENCE = "file_presence"
    FILE_CHANGE = "file_change"
    TEMPORAL = "temporal"
    SIMULATED_VISUAL = "simulated_visual"
    SIMULATED_AUDIO = "simulated_audio"
    ENVIRONMENTAL_EVENT = "environmental_event"
    UNKNOWN = "unknown"

    ALL = (TEXTUAL, NUMERIC, FILE_PRESENCE, FILE_CHANGE, TEMPORAL,
           SIMULATED_VISUAL, SIMULATED_AUDIO, ENVIRONMENTAL_EVENT, UNKNOWN)
    # Modalities that are metadata-only in this prompt (no heavy processing).
    METADATA_ONLY = frozenset({SIMULATED_VISUAL, SIMULATED_AUDIO})


@dataclass
class ModalitySignal:
    """A modality classification with confidence and a metadata-only flag."""

    modality: str = SensoryModality.UNKNOWN
    confidence: float = 0.0
    metadata_only: bool = False
    notes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.modality not in SensoryModality.ALL:
            self.modality = SensoryModality.UNKNOWN
        self.metadata_only = self.modality in SensoryModality.METADATA_ONLY

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


def classify_modality(source_type: str,
                      hint: Optional[str] = None) -> ModalitySignal:
    """Map a source type / hint to a modality (no content analysis)."""
    if hint in SensoryModality.ALL:
        return ModalitySignal(modality=hint, confidence=0.9)
    mapping = {
        "jsonl_file": SensoryModality.ENVIRONMENTAL_EVENT,
        "text_file": SensoryModality.TEXTUAL,
        "numeric_csv": SensoryModality.NUMERIC,
        "folder_snapshot": SensoryModality.FILE_PRESENCE,
        "folder_poll": SensoryModality.FILE_CHANGE,
        "event_log": SensoryModality.ENVIRONMENTAL_EVENT,
        "manual_dump": SensoryModality.ENVIRONMENTAL_EVENT,
        "simulated_camera_metadata": SensoryModality.SIMULATED_VISUAL,
        "simulated_audio_metadata": SensoryModality.SIMULATED_AUDIO,
        "synthetic_sensor": SensoryModality.NUMERIC,
    }
    modality = mapping.get(source_type, SensoryModality.UNKNOWN)
    notes = (["metadata only; no image/audio content analysis"]
             if modality in SensoryModality.METADATA_ONLY else [])
    return ModalitySignal(modality=modality, confidence=0.7, notes=notes)
