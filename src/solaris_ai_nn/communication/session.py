"""Communication session -- one operator, one scope, one transcript.

The config is deny-leaning by default: sensory text stimulus is off, and
shutdown/benchmark commands require confirmation. The session holds
identity and bookkeeping; permissions stay with governance.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .dialogue_state import DialogueState
from .transcript import CommunicationTranscript


@dataclass
class CommunicationSessionConfig:
    """What this session may even ask for (governance still decides)."""

    allow_benchmark_commands: bool = True
    allow_checkpoint_request: bool = True
    allow_safe_shutdown_request: bool = True
    allow_governance_approval: bool = True
    allow_sensory_text_stimulus: bool = False
    require_confirmation_for_shutdown: bool = True
    require_confirmation_for_benchmark: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class CommunicationSession:
    """Operator identity + dialogue state + transcript + scope."""

    operator: str = "operator"
    state_dir: Optional[Union[str, Path]] = None
    config: CommunicationSessionConfig = field(
        default_factory=CommunicationSessionConfig)
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    started_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        self.state = DialogueState(operator_session_id=self.session_id)
        self.transcript = CommunicationTranscript(state_dir=self.state_dir)
        if self.transcript.path is not None:
            self.state.transcript_path = str(self.transcript.path)

    def allowed_command_scope(self) -> Dict[str, bool]:
        c = self.config
        return {
            "run_bounded_benchmark": c.allow_benchmark_commands,
            "request_checkpoint": c.allow_checkpoint_request,
            "request_safe_shutdown": c.allow_safe_shutdown_request,
            "approve_governance_request": c.allow_governance_approval,
            "reject_governance_request": c.allow_governance_approval,
            "sensory_text_stimulus": c.allow_sensory_text_stimulus,
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "operator": self.operator,
            "started_at": self.started_at,
            "config": self.config.to_dict(),
            "allowed_command_scope": self.allowed_command_scope(),
            "dialogue": self.state.snapshot(),
            "transcript": self.transcript.summary(),
        }
