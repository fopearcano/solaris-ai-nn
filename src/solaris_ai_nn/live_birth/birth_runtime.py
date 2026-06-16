"""Live read-only birth runtime -- the bounded first contact with real input.

:class:`LiveReadOnlyBirthRuntime` loads the birth profile, governance, and feeder
registry, initializes the state layout, reads a bounded inbox batch, validates and
quarantines events, activates the read-only environmental membrane, optionally
hands accepted-event summaries to perceptual metabolism in report-only mode, and
issues a birth certificate and reports. It is bounded and local-only: it reads
local JSONL files only and never calls the network, runs a shell, calls Git/GitHub,
starts/stops feeders, controls hardware, executes commands, modifies source,
publishes/uploads, or claims consciousness/life/agency.
"""

from __future__ import annotations

import importlib.util
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .birth_certificate import BirthCertificateBuilder
from .birth_profile import (
    FORBIDDEN_FIRST_BIRTH_SOURCES,
    LiveBirthProfile,
    get_live_birth_profile,
)
from .event_validator import LiveEventValidator
from .feeder_registry import LiveFeederRegistry, feeder_registry_template
from .governance import (
    GOVERNANCE_FILENAME,
    GovernanceValidator,
    governance_template,
)
from .inbox_spool import LiveInboxSpool
from .membrane_activation import EnvironmentalMembraneActivation
from .quarantine import QuarantineStore
from .safety import LiveBirthSafetyValidator

_SUBDIRS = ("governance", "feeders", "inbox", "quarantine", "processed",
            "reports", "certificates", "index")


@dataclass
class LiveReadOnlyBirthRuntime:
    """Bounded, local live read-only birth runtime."""

    state_dir: str = ".solaris_ai_nn_live"
    alpha_state_dir: str = ".solaris_ai_nn_alpha"
    profile: Optional[str] = None
    max_runtime_s: float = 60.0
    max_files: int = 50
    max_events: int = 500
    max_bytes: int = 5_000_000
    strict: bool = False
    dry_run: bool = False
    report_only: bool = False
    require_governance: bool = True
    require_feeder_registry: bool = False
    allow_operator_pulse: bool = True
    require_claimguard: bool = False
    operator_note: str = ""

    safety: LiveBirthSafetyValidator = field(
        default_factory=LiveBirthSafetyValidator, init=False)
    birth_profile: Any = field(default=None, init=False)
    governance: Any = field(default=None, init=False)
    governance_result: Dict[str, Any] = field(default_factory=dict, init=False)
    feeders: Any = field(default=None, init=False)
    quarantine: Any = field(default=None, init=False)
    inbox_result: Dict[str, Any] = field(default_factory=dict, init=False)
    membrane: Dict[str, Any] = field(default_factory=dict, init=False)
    metabolism_status: str = field(default="", init=False)
    certificate: Dict[str, str] = field(default_factory=dict, init=False)
    run_id: str = field(default="", init=False)
    blocked: bool = field(default=False, init=False)
    blockers: List[str] = field(default_factory=list, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.birth_profile = get_live_birth_profile(self.profile)
        self.run_id = f"birth_{int(time.time())}"
        if not self.max_runtime_s:
            self._refused = True

    # -- state layout -------------------------------------------------------

    def initialize(self) -> Dict[str, Any]:
        os.makedirs(self.state_dir, exist_ok=True)
        created = []
        for name in _SUBDIRS:
            path = os.path.join(self.state_dir, name)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            created.append({"name": name, "existed": existed})
        return {"state_dir": self.state_dir, "directories": created,
                "deletes_state": False}

    def write_templates(self) -> Dict[str, str]:
        """Write governance + feeder registry templates if absent (never over-write)."""
        self.initialize()
        gov_path = os.path.join(self.state_dir, "governance", GOVERNANCE_FILENAME)
        reg_path = os.path.join(self.state_dir, "feeders",
                                "FEEDER_REGISTRY.json")
        if not os.path.isfile(gov_path):
            with open(gov_path, "w", encoding="utf-8") as fh:
                json.dump(governance_template(), fh, indent=2)
        if not os.path.isfile(reg_path):
            with open(reg_path, "w", encoding="utf-8") as fh:
                json.dump(feeder_registry_template(), fh, indent=2)
        return {"governance": gov_path, "feeder_registry": reg_path}

    # -- doctor -------------------------------------------------------------

    def run_doctor(self) -> Dict[str, Any]:
        self.initialize()
        self.governance = GovernanceValidator().load(self.state_dir)
        self.governance_result = GovernanceValidator().validate(self.governance)
        self.feeders = LiveFeederRegistry.load(self.state_dir)
        feeder_blockers = [f.feeder_id for f in self.feeders.blocking()]
        inbox_dir = os.path.join(self.state_dir, "inbox")
        inbox_present = os.path.isdir(inbox_dir) and any(
            n.endswith(".jsonl") for n in os.listdir(inbox_dir)) \
            if os.path.isdir(inbox_dir) else False
        blockers = list(self.governance_result.get("blockers", []))
        blockers += [f"feeder grants control: {fid}" for fid in feeder_blockers]
        return {
            "governance_status": self.governance_result.get("governance_status"),
            "governance_passed": self.governance_result.get("governance_passed"),
            "feeder_registry_present": self.feeders.present,
            "feeder_blocker_count": len(feeder_blockers),
            "inbox_has_events": inbox_present,
            "blockers": blockers,
            "passed": not blockers,
            "note": "live doctor validates governance, feeder registry, inbox, "
                    "and safety read-only",
        }

    # -- run ----------------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        if self._refused or not self.safety.validate_bounded(
                self.max_runtime_s).safe:
            return {"refused": True, "reason": "unbounded runtime"}

        self.initialize()
        self.quarantine = QuarantineStore(state_dir=self.state_dir)
        self.governance = GovernanceValidator().load(self.state_dir)
        self.governance_result = GovernanceValidator().validate(self.governance)
        self.feeders = LiveFeederRegistry.load(self.state_dir)

        # Governance gate.
        gov_ok = self.governance_result.get("governance_passed", False)
        if self.require_governance and not gov_ok:
            self.blocked = True
            self.blockers = list(self.governance_result.get("blockers",
                                 ["governance not present/approved"]))
            self.membrane = EnvironmentalMembraneActivation().activate([]).to_dict()
            self.membrane["membrane_activated"] = False
            self._finalize(first_safety_block="governance_blocked")
            return self._result()

        # Feeder registry gate (optional).
        if self.require_feeder_registry and not self.feeders.present:
            self.blocked = True
            self.blockers = ["feeder registry required but not present"]
            self.membrane = EnvironmentalMembraneActivation().activate([]).to_dict()
            self.membrane["membrane_activated"] = False
            self._finalize(first_safety_block="feeder_registry_missing")
            return self._result()
        if self.feeders.blocking():
            self.blocked = True
            self.blockers = [f"feeder grants control: {f.feeder_id}"
                             for f in self.feeders.blocking()]
            self.membrane = EnvironmentalMembraneActivation().activate([]).to_dict()
            self.membrane["membrane_activated"] = False
            self._finalize(first_safety_block="feeder_control_granted")
            return self._result()

        # Bounded inbox read + validation + quarantine.
        allowed = self.governance.allowed_sources or \
            self.birth_profile.allowed_sources
        if not self.allow_operator_pulse:
            allowed = [s for s in allowed if s != "operator_pulse"]
        validator = LiveEventValidator(
            allowed_sources=allowed,
            registered_sources=[r.source_id for r in self.feeders.records],
            strict=self.strict)
        spool = LiveInboxSpool(
            inbox_dir=os.path.join(self.state_dir, "inbox"),
            validator=validator, quarantine=self.quarantine,
            max_files=self.max_files, max_events=self.max_events,
            max_bytes=self.max_bytes, strict=self.strict)
        read = spool.read() if not self.report_only else spool.read()
        self.inbox_result = read.to_dict()

        # Membrane activation (read-only).
        activation = EnvironmentalMembraneActivation()
        self.membrane = activation.activate(read.accepted_envelopes).to_dict()

        # Optional perceptual metabolism handoff (report-only, bounded).
        self._maybe_metabolism(activation)

        if not self.dry_run:
            self.quarantine.write()
        self._finalize()
        return self._result()

    def _maybe_metabolism(self, activation) -> None:
        if not self._module_available("perceptual_metabolism"):
            self.metabolism_status = "unavailable (warning)"
            return
        # Report-only: summarize counts; never request more data or control.
        self.metabolism_status = (
            f"report-only handoff of {activation.last_batch.count} accepted "
            "event(s); metabolism may not request more data or control feeders")

    @staticmethod
    def _module_available(submodule: str) -> bool:
        try:
            return importlib.util.find_spec(
                f"solaris_ai_nn.{submodule}") is not None
        except Exception:
            return False

    def _finalize(self, first_safety_block: str = "") -> None:
        builder = BirthCertificateBuilder(state_dir=self.state_dir)
        certificate = builder.build(
            run_id=self.run_id, profile=self.birth_profile,
            governance_path=getattr(self.governance, "path", ""),
            feeder_registry_path=getattr(self.feeders, "path", ""),
            allowed_sources=(self.governance.allowed_sources
                             or self.birth_profile.allowed_sources),
            forbidden_sources=self.birth_profile.forbidden_sources,
            inbox_result=self.inbox_result, membrane=self.membrane,
            metabolism_status=self.metabolism_status,
            first_safety_block=first_safety_block,
            safety_status=("blocked" if self.blocked else "pass"),
            operator_note=self.operator_note)
        self._certificate_obj = certificate
        if not self.dry_run:
            self.certificate = builder.write(certificate)
            self.write_artifacts()

    def _result(self) -> Dict[str, Any]:
        return {
            "refused": False, "run_id": self.run_id, "blocked": self.blocked,
            "blockers": list(self.blockers),
            "accepted_event_count": self.inbox_result.get(
                "live_event_accepted_count", 0),
            "quarantined_event_count": self.inbox_result.get(
                "live_event_quarantined_count", 0),
            "membrane_activated": self.membrane.get("membrane_activated", False),
            "certificate": self.certificate.get("markdown"),
        }

    # -- integration views --------------------------------------------------

    def live_birth_status(self) -> Dict[str, Any]:
        gov = self.governance_result
        return {
            "live_birth_enabled": True,
            "birth_run_id": self.run_id,
            "live_birth_blocked": self.blocked,
            "governance_status": gov.get("governance_status"),
            "governance_passed": gov.get("governance_passed", False),
            "live_feeder_count": (self.feeders.index()["live_feeder_count"]
                                  if self.feeders else 0),
            "live_inbox_file_count": self.inbox_result.get(
                "live_inbox_file_count", 0),
            "live_event_count": self.inbox_result.get("live_event_count", 0),
            "live_event_accepted_count": self.inbox_result.get(
                "live_event_accepted_count", 0),
            "live_event_quarantined_count": self.inbox_result.get(
                "live_event_quarantined_count", 0),
            "membrane_activation_status": (
                "activated" if self.membrane.get("membrane_activated")
                else "not_activated"),
            "metabolism_status": self.metabolism_status,
            "latest_birth_certificate_path": self.certificate.get("markdown"),
            "live_birth_safety_block_count": self.safety.rejected_count,
            "starts_feeders": False, "controls_hardware": False,
            "accesses_network": False, "runs_git": False, "calls_github": False,
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.live_birth_status()

    def next_phase_recommendations(self) -> List[Dict[str, str]]:
        """Recommend next phases; never start them automatically."""
        if self.blocked:
            return [{"phase": "fix_blockers",
                     "detail": "fix governance/feeders/quarantine blockers"}]
        return [
            {"phase": "live_observation_2h",
             "detail": "run a 2-hour live read-only observation phase"},
            {"phase": "live_metabolism_24h",
             "detail": "run a 24-hour live metabolism phase"},
            {"phase": "live_ontogenesis_3_7d",
             "detail": "run a 3-7 day live ontogenesis phase"},
            {"phase": "live_semiogenesis_7_14d",
             "detail": "run a 7-14 day live semiogenesis phase"},
            {"phase": "live_short_developmental_soak_7_30d",
             "detail": "run a 7-30 day live short developmental soak"},
        ]

    def write_artifacts(self) -> Dict[str, Any]:
        from .reports import LiveBirthReportBuilder

        return LiveBirthReportBuilder(self).write()
