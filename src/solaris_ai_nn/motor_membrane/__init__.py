"""Motor membrane -- Pilot-3 limited embodiment, simulation-only, firewalled.

Pilot-2 gave Solaris-AI-NN read-only environmental input. The motor membrane
adds the opposite boundary: it represents what Solaris-AI-NN *would* do if it
had embodiment, while remaining simulation-only, dry-run-capable, sandbox-only,
inspectable, auditable, reversible, and blocked from real-world effects.

Core principle: Solaris-AI-NN may form action intentions, simulate their
consequences, write action traces, and act inside sandbox worlds -- but it may
not act on the real world. An always-on :class:`ActuationFirewall` enforces
this and cannot be disabled by runtime modules; every proposal and veto is
recorded in the :class:`ActionLedger`; and every motor action carries
``real_world_authority = False``.
"""

from __future__ import annotations

from .action_ledger import ActionLedger, ActionLedgerRecord
from .actions import (
    MotorAction,
    MotorActionResult,
    MotorActionScope,
    MotorActionStatus,
    MotorActionType,
)
from .actuation_firewall import (
    ActuationFirewall,
    FirewallDecision,
    FirewallRule,
)
from .affordances import (
    Affordance,
    AffordanceDetector,
    AffordanceMap,
    AffordanceType,
)
from .consequence_model import (
    ActionConsequencePrediction,
    ActionConsequenceRecord,
    ConsequenceModel,
)
from .embodiment_profiles import (
    EmbodimentProfile,
    EmbodimentProfileName,
    EmbodimentProfileRegistry,
)
from .motor_contract import (
    MotorContract,
    MotorContractValidator,
    MotorContractViolation,
)
from .operator_runbook import Pilot3RunbookBuilder
from .pilot3_decision_gate import (
    Pilot3DecisionGate,
    Pilot3DecisionOption,
    Pilot3DecisionResult,
)
from .pilot3_protocol import (
    Pilot3Phase,
    Pilot3PhaseRecord,
    Pilot3PhaseStatus,
    Pilot3Protocol,
)
from .pilot3_report import Pilot3Report, Pilot3ReportBuilder
from .safety import HARD_RULES, MotorMembraneSafetyValidator, MotorSafetyReport
from .sandbox_runtime import EmbodimentSandboxRuntime
from .simulated_actuators import (
    ActuatorResult,
    GridWorldActuator,
    InternalActuator,
    SimulatedActuator,
)
from .veto import ActionVeto, ActionVetoLayer, VetoReason

__all__ = [
    # actions / contract / safety
    "MotorAction", "MotorActionType", "MotorActionScope", "MotorActionStatus",
    "MotorActionResult", "MotorContract", "MotorContractValidator",
    "MotorContractViolation", "MotorMembraneSafetyValidator",
    "MotorSafetyReport", "HARD_RULES",
    # firewall / veto / ledger
    "ActuationFirewall", "FirewallDecision", "FirewallRule",
    "ActionVeto", "ActionVetoLayer", "VetoReason",
    "ActionLedger", "ActionLedgerRecord",
    # actuators / affordances / consequences
    "SimulatedActuator", "GridWorldActuator", "InternalActuator",
    "ActuatorResult", "Affordance", "AffordanceType", "AffordanceMap",
    "AffordanceDetector", "ActionConsequencePrediction",
    "ActionConsequenceRecord", "ConsequenceModel",
    # sandbox / profiles / protocol / report / decision / runbook
    "EmbodimentSandboxRuntime", "EmbodimentProfile", "EmbodimentProfileName",
    "EmbodimentProfileRegistry", "Pilot3Protocol", "Pilot3Phase",
    "Pilot3PhaseStatus", "Pilot3PhaseRecord", "Pilot3Report",
    "Pilot3ReportBuilder", "Pilot3DecisionGate", "Pilot3DecisionResult",
    "Pilot3DecisionOption", "Pilot3RunbookBuilder",
]
