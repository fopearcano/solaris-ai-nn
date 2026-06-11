"""Controlled communication interface and operator dialogue (Prompt 19).

Language is an interface into the system, not the ruler of it: operator
text is classified before any effect, routed through safety and
governance, answered from recorded state, and transcribed. No LLM, no
chatbot, no authority -- and no claim of consciousness anywhere.
"""

from .approval_router import ApprovalRouter
from .command_router import CommandRouter
from .dialogue_state import (
    DialogueMode,
    DialogueState,
    PendingClarification,
    PendingConfirmation,
)
from .gateway import CommunicationGateway
from .input_classifier import (
    InputClassification,
    InputKind,
    OperatorInputClassifier,
)
from .operator_commands import (
    FORBIDDEN_COMMAND_TYPES,
    CommandType,
    CommandValidationResult,
    OperatorCommand,
    command_from_classification,
)
from .query_router import QueryRouter
from .response_builder import CommunicationResponse, ResponseBuilder
from .safety import CommunicationSafetyReport, CommunicationSafetyValidator
from .session import CommunicationSession, CommunicationSessionConfig
from .templates import TEMPLATES, render
from .transcript import (
    CommunicationTranscript,
    TranscriptEntry,
    sanitize_text,
)

__all__ = [
    "ApprovalRouter", "CommandRouter", "CommandType",
    "CommandValidationResult", "CommunicationGateway",
    "CommunicationResponse", "CommunicationSafetyReport",
    "CommunicationSafetyValidator", "CommunicationSession",
    "CommunicationSessionConfig", "CommunicationTranscript",
    "DialogueMode", "DialogueState", "FORBIDDEN_COMMAND_TYPES",
    "InputClassification", "InputKind", "OperatorCommand",
    "OperatorInputClassifier", "PendingClarification",
    "PendingConfirmation", "QueryRouter", "ResponseBuilder", "TEMPLATES",
    "TranscriptEntry", "command_from_classification", "render",
    "sanitize_text",
]
