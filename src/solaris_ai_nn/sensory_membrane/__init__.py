"""Read-only sensory membrane -- the world may enter; the system may not act.

This package is the Pilot-2 preparation layer: a read-only sensory membrane
that receives controlled environmental input (JSONL / text / numeric streams,
watched folders, event logs, manual dumps, and simulated camera/audio
*metadata*) and converts it into canonical Solaris-AI-NN stimuli -- without
ever letting the system write to, delete, rename, or otherwise act on the
source, and without letting input text become an operator command.

Core principle: the world may enter the system; the system may not act on the
world. Camera/audio are metadata-only here (no OCR/ASR/image analysis), there
are no network sources or external APIs, provenance is mandatory, and source
boundaries are visible to Ego and the Inner MAP. Disabled by default; real
read-only sources require explicit configuration/governance.
"""

from __future__ import annotations

from .adapters import AdapterError, AdapterResult, SensoryAdapter
from .event_normalizer import (
    NormalizedSensoryEvent,
    RawSensoryEvent,
    SensoryEventNormalizer,
)
from .folder_watch import FolderPollAdapter
from .grounding import EnvironmentalGroundingRecord, SensoryGroundingEngine
from .jsonl_stream import JSONLStreamAdapter
from .membrane_runtime import SensoryMembraneRuntime
from .modality import ModalitySignal, SensoryModality, classify_modality
from .numeric_stream import NumericStreamAdapter
from .provenance import ProvenanceLedger, ProvenanceRecord, hash_text
from .read_only_contract import (
    ReadOnlyContract,
    ReadOnlyContractValidator,
    ReadOnlyViolation,
)
from .reports import SensoryMembraneReport, SensoryMembraneReportBuilder
from .safety import SensoryMembraneSafetyValidator, SensorySafetyReport
from .sensory_buffer import BufferedSensoryEvent, SensoryBuffer
from .source_registry import SensorySourceRegistry
from .sources import (
    SensorySource,
    SensorySourceConfig,
    SensorySourceStatus,
    SensorySourceType,
    TrustLevel,
)
from .text_stream import TextStreamAdapter

__all__ = [
    # sources / registry / contract
    "SensorySource", "SensorySourceConfig", "SensorySourceType",
    "SensorySourceStatus", "TrustLevel", "SensorySourceRegistry",
    "ReadOnlyContract", "ReadOnlyContractValidator", "ReadOnlyViolation",
    # adapters
    "SensoryAdapter", "AdapterResult", "AdapterError",
    "JSONLStreamAdapter", "TextStreamAdapter", "NumericStreamAdapter",
    "FolderPollAdapter",
    # modality / normalization / buffer / grounding / provenance
    "SensoryModality", "ModalitySignal", "classify_modality",
    "RawSensoryEvent", "NormalizedSensoryEvent", "SensoryEventNormalizer",
    "SensoryBuffer", "BufferedSensoryEvent",
    "EnvironmentalGroundingRecord", "SensoryGroundingEngine",
    "ProvenanceLedger", "ProvenanceRecord", "hash_text",
    # runtime / reports / safety
    "SensoryMembraneRuntime",
    "SensoryMembraneReportBuilder", "SensoryMembraneReport",
    "SensoryMembraneSafetyValidator", "SensorySafetyReport",
]
