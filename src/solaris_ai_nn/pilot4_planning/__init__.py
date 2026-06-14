"""Pilot-4 planning -- external actuation readiness, planning-only.

After Pilot-3 (simulated embodiment, proven non-actuation), Pilot-4 asks the
next question without taking the next step: *what would be required before
Solaris-AI-NN could ever be allowed to act on the external world?* The output is
a readiness framework, not an actuator. Pilot-4 plans the door; it does not open
it.

This package produces planning artifacts only: an actuator-class taxonomy, a
forbidden-actuator registry, a future-interface specification, an
external-actuation risk model, a consent boundary, an external authority model,
a threat model, hardware-isolation and emergency requirements, an external-audit
schema, a readiness dossier, and a planning-only decision gate.
``real_world_actuation_enabled`` is always false; every hardware / network /
browser / OS / robotics control flag is forced false; current authority can
never become external; and no actuator adapter is implemented. Real-world
actuation, device control, robotics, browser/OS automation, and network action
remain prohibited, and no consciousness, free will, agency, or life is claimed.
"""

from __future__ import annotations

from .actuator_taxonomy import (
    ActuatorCategory,
    ActuatorClass,
    ActuatorRiskTier,
    ActuatorTaxonomy,
)
from .approval_workflow import (
    ApprovalRequirement,
    ApprovalStep,
    FutureApprovalWorkflow,
)
from .audit_requirements import (
    AuditChecklist,
    ExternalActuationAuditRequirement,
)
from .authority_model import (
    AuthorityLevel,
    AuthorityTransition,
    ExternalAuthorityModel,
)
from .consent_boundary import (
    ConsentBoundary,
    ConsentRecordTemplate,
    ConsentRequirement,
)
from .decision_gate import (
    Pilot4DecisionGate,
    Pilot4DecisionOption,
    Pilot4DecisionResult,
)
from .emergency_requirements import (
    EmergencyRequirement,
    EmergencyRequirementSet,
)
from .forbidden_actuators import ForbiddenActuator, ForbiddenActuatorRegistry
from .future_interface_spec import (
    FutureActuatorInterfaceSpec,
    InterfaceConstraint,
    InterfaceRequirement,
)
from .hardware_isolation import (
    HardwareIsolationPlan,
    HardwareIsolationRequirement,
)
from .operator_runbook import Pilot4PlanningRunbookBuilder
from .pilot4_config import (
    DEFAULT_PILOT4_DIR,
    Pilot4AuthorityStatus,
    Pilot4PlanningConfig,
    Pilot4PlanningMode,
)
from .planning_protocol import (
    Pilot4PlanningPhase,
    Pilot4PlanningPhaseRecord,
    Pilot4PlanningPhaseStatus,
    Pilot4PlanningProtocol,
    Pilot4PlanningState,
)
from .readiness_dossier import (
    Pilot4ReadinessConclusion,
    Pilot4ReadinessDossier,
    Pilot4ReadinessDossierBuilder,
)
from .risk_model import (
    ActuationRisk,
    RiskAssessment,
    RiskLikelihood,
    RiskModel,
    RiskRecommendation,
    RiskSeverity,
)
from .safety import HARD_RULES, Pilot4PlanningSafetyValidator, Pilot4SafetyReport
from .threat_model import ThreatModel, ThreatScenario

__all__ = [
    # config / safety / protocol
    "Pilot4PlanningConfig", "Pilot4PlanningMode", "Pilot4AuthorityStatus",
    "DEFAULT_PILOT4_DIR", "Pilot4PlanningSafetyValidator", "Pilot4SafetyReport",
    "HARD_RULES", "Pilot4PlanningProtocol", "Pilot4PlanningPhase",
    "Pilot4PlanningPhaseStatus", "Pilot4PlanningState",
    "Pilot4PlanningPhaseRecord",
    # taxonomy / forbidden / interface spec
    "ActuatorTaxonomy", "ActuatorClass", "ActuatorCategory",
    "ActuatorRiskTier", "ForbiddenActuator", "ForbiddenActuatorRegistry",
    "FutureActuatorInterfaceSpec", "InterfaceRequirement",
    "InterfaceConstraint",
    # risk / consent / authority / threat
    "RiskModel", "RiskAssessment", "ActuationRisk", "RiskSeverity",
    "RiskLikelihood", "RiskRecommendation", "ConsentBoundary",
    "ConsentRequirement", "ConsentRecordTemplate", "ExternalAuthorityModel",
    "AuthorityLevel", "AuthorityTransition", "ThreatModel", "ThreatScenario",
    # hardware / approval / emergency / audit
    "HardwareIsolationPlan", "HardwareIsolationRequirement",
    "FutureApprovalWorkflow", "ApprovalStep", "ApprovalRequirement",
    "EmergencyRequirementSet", "EmergencyRequirement", "AuditChecklist",
    "ExternalActuationAuditRequirement",
    # dossier / decision / runbook
    "Pilot4ReadinessDossierBuilder", "Pilot4ReadinessDossier",
    "Pilot4ReadinessConclusion", "Pilot4DecisionGate", "Pilot4DecisionResult",
    "Pilot4DecisionOption", "Pilot4PlanningRunbookBuilder",
]
