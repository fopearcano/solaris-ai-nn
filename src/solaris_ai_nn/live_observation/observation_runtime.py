"""Post-birth live observation runtime -- bounded, read-only, non-learning.

:class:`PostBirthLiveObservationRuntime` runs phases 2-3 of the post-birth sequence:
a bounded live read-only observation (no learning) and a report-only perceptual
metabolism calibration. It re-reads the local inbox through the Prompt 67 validator
(reusing quarantine), groups accepted events into bounded observation windows, and
runs the source-health, source-diet, rhythm, absence, and overload/deprivation
analyzers, a report-only metabolism calibration, and an advisory stability gate.

It is bounded and local-only. It does not learn, form concepts, birth signs, run
developmental learning, start/stop/configure feeders, control hardware, access the
network/shell/browser/OS/camera/microphone, call Git/GitHub, execute commands,
modify source, treat sensory text as a command, treat human labels or debug gloss
as ground truth, or claim consciousness, sentience, life, personhood, agency, free
will, emotion, feeling, understanding, self-awareness, or subjective experience.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..live_birth.event_validator import LiveEventValidator
from ..live_birth.feeder_registry import LiveFeederRegistry
from ..live_birth.governance import GovernanceValidator
from ..live_birth.inbox_spool import LiveInboxSpool
from ..live_birth.quarantine import QuarantineStore
from .absence_analysis import LiveAbsenceAnalyzer
from .metabolism_calibration import PerceptualMetabolismCalibrator
from .observation_profile import get_observation_profile
from .observation_window import ObservationWindowBuilder, parse_timestamp
from .overload_deprivation import LiveOverloadDeprivationAssessor
from .rhythm_analysis import LiveRhythmAnalyzer
from .safety import LiveObservationSafetyValidator
from .source_diet import LiveSourceDietAnalyzer
from .source_health import LiveSourceHealthEvaluator
from .stability_gate import LiveStabilityGate

_SUBDIRS = ("windows", "source_health", "source_diet", "metabolism", "reports",
            "first_day", "index")


@dataclass
class PostBirthLiveObservationRuntime:
    """Bounded, local, read-only post-birth observation runtime (no learning)."""

    state_dir: str = ".solaris_ai_nn_live"
    alpha_state_dir: str = ".solaris_ai_nn_alpha"
    profile: Optional[str] = None
    max_runtime_s: float = 120.0
    max_events: int = 2000
    max_files: int = 100
    observation_window_minutes: int = 30
    report_only: bool = False
    dry_run: bool = False
    strict: bool = False
    require_governance: bool = True
    require_birth_certificate: bool = True
    allow_new_inbox_read: bool = True
    require_claimguard: bool = False
    operator_note: str = ""

    safety: LiveObservationSafetyValidator = field(
        default_factory=LiveObservationSafetyValidator, init=False)
    observation_profile: Any = field(default=None, init=False)
    governance: Any = field(default=None, init=False)
    governance_result: Dict[str, Any] = field(default_factory=dict, init=False)
    feeders: Any = field(default=None, init=False)
    quarantine: Any = field(default=None, init=False)
    run_id: str = field(default="", init=False)
    blocked: bool = field(default=False, init=False)
    blockers: List[str] = field(default_factory=list, init=False)

    accepted_events: List[Dict[str, Any]] = field(default_factory=list,
                                                  init=False)
    quarantine_by_source: Dict[str, int] = field(default_factory=dict,
                                                  init=False)
    windows: List[Dict[str, Any]] = field(default_factory=list, init=False)
    source_health_summary: Dict[str, Any] = field(default_factory=dict,
                                                   init=False)
    source_diet: Dict[str, Any] = field(default_factory=dict, init=False)
    rhythm: Dict[str, Any] = field(default_factory=dict, init=False)
    absence: Dict[str, Any] = field(default_factory=dict, init=False)
    load: Dict[str, Any] = field(default_factory=dict, init=False)
    metabolism: Dict[str, Any] = field(default_factory=dict, init=False)
    stability: Dict[str, Any] = field(default_factory=dict, init=False)
    birth_certificate_present: bool = field(default=False, init=False)
    reports: Dict[str, Any] = field(default_factory=dict, init=False)
    first_day_record: Dict[str, Any] = field(default_factory=dict, init=False)
    _refused: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.state_dir == self.alpha_state_dir:
            self.state_dir = ".solaris_ai_nn_live"
        self.observation_profile = get_observation_profile(self.profile)
        self.observation_window_minutes = (
            self.observation_window_minutes
            or self.observation_profile.observation_window_minutes)
        self.run_id = f"obs_{int(time.time())}"
        if not self.max_runtime_s:
            self._refused = True

    # -- state layout -------------------------------------------------------

    def initialize(self) -> Dict[str, Any]:
        base = os.path.join(self.state_dir, "observation")
        os.makedirs(base, exist_ok=True)
        created = []
        for name in _SUBDIRS:
            path = os.path.join(base, name)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            created.append({"name": name, "existed": existed})
        return {"observation_dir": base, "directories": created,
                "deletes_state": False}

    # -- doctor -------------------------------------------------------------

    def run_doctor(self) -> Dict[str, Any]:
        self.initialize()
        self.governance = GovernanceValidator().load(self.state_dir)
        self.governance_result = GovernanceValidator().validate(self.governance)
        cert = self._find_birth_certificate()
        bounded = self.safety.validate_bounded(self.max_runtime_s).safe
        blockers = list(self.governance_result.get("blockers", []))
        if self.require_birth_certificate and not cert:
            blockers.append("birth certificate required but not present")
        if not bounded:
            blockers.append("runtime is unbounded")
        return {
            "governance_status": self.governance_result.get("governance_status"),
            "governance_passed": self.governance_result.get("governance_passed"),
            "birth_certificate_present": bool(cert),
            "bounded": bounded,
            "blockers": blockers, "passed": not blockers,
            "note": "live observation doctor validates governance, birth "
                    "certificate, and bounded runtime read-only",
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
        self.birth_certificate_present = bool(self._find_birth_certificate())

        gov_ok = self.governance_result.get("governance_passed", False)
        if self.require_governance and not gov_ok:
            self.blocked = True
            self.blockers = list(self.governance_result.get(
                "blockers", ["governance not present/approved"]))
        if self.require_birth_certificate and not self.birth_certificate_present:
            self.blocked = True
            self.blockers.append("birth certificate required but not present")

        # Read + validate events (bounded, read-only) feeding all analyzers.
        if not self.blocked:
            self._read_events()

        # Analyzers (run on whatever was accepted; empty is valid -> deprivation).
        self._analyze()

        if not self.dry_run:
            self.write_artifacts()
        return self._result()

    def _find_birth_certificate(self) -> str:
        cert_dir = os.path.join(self.state_dir, "certificates")
        if not os.path.isdir(cert_dir):
            return ""
        for name in sorted(os.listdir(cert_dir)):
            if name.endswith(".md") or name.endswith(".json"):
                return os.path.join(cert_dir, name)
        return ""

    def _read_events(self) -> None:
        if not self.allow_new_inbox_read:
            return
        allowed = (self.governance.allowed_sources
                   or self.observation_profile_allowed())
        validator = LiveEventValidator(
            allowed_sources=allowed,
            registered_sources=[r.source_id for r in self.feeders.records]
            if self.feeders else [],
            strict=self.strict)
        spool = LiveInboxSpool(
            inbox_dir=os.path.join(self.state_dir, "inbox"),
            validator=validator, quarantine=self.quarantine,
            max_files=self.max_files, max_events=self.max_events,
            strict=self.strict)
        read = spool.read()
        for env in read.accepted_envelopes:
            event = env.event
            if event is None:
                continue
            d = event.to_dict()
            d["source_kind"] = "live_readonly"
            d["stimulus"] = d.get("payload")
            self.accepted_events.append(d)
        # Quarantine-by-source from preserved originals.
        for rec in self.quarantine.records:
            orig = rec.original
            sid = orig.get("source_id", "") if isinstance(orig, dict) else ""
            self.quarantine_by_source[sid] = \
                self.quarantine_by_source.get(sid, 0) + 1

    def observation_profile_allowed(self) -> List[str]:
        from ..live_birth.birth_profile import ALLOWED_FIRST_BIRTH_SOURCES

        return list(ALLOWED_FIRST_BIRTH_SOURCES)

    def _expected_sources(self) -> List[str]:
        if self.feeders and self.feeders.records:
            return [r.source_id for r in self.feeders.records]
        return list(self.governance.allowed_sources or
                    self.observation_profile_allowed())

    def _split_windows(self) -> List[List[Dict[str, Any]]]:
        """Group accepted events into bounded time windows (no infinite tail)."""
        if not self.accepted_events:
            return [[]]
        window_s = max(1, self.observation_window_minutes) * 60.0
        stamped: List[tuple] = []
        undated: List[Dict[str, Any]] = []
        for ev in self.accepted_events:
            t = parse_timestamp(ev.get("timestamp_utc", ""))
            (stamped.append((t, ev)) if t is not None
             else undated.append(ev))
        if not stamped:
            return [self.accepted_events]
        stamped.sort(key=lambda p: p[0])
        base = stamped[0][0]
        groups: Dict[int, List[Dict[str, Any]]] = {}
        for t, ev in stamped:
            idx = int((t - base) // window_s)
            groups.setdefault(idx, []).append(ev)
        out = [groups[k] for k in sorted(groups)]
        if undated:
            out.append(undated)
        return out or [[]]

    def _analyze(self) -> None:
        expected = self._expected_sources()
        registered = (
            [r.source_id for r in self.feeders.records]
            if self.feeders and self.feeders.records else expected)

        # Bounded observation windows.
        builder = ObservationWindowBuilder()
        batches = self._split_windows()
        total_quarantined = sum(self.quarantine_by_source.values())
        for i, batch in enumerate(batches):
            # Attribute the quarantine count to the first window only.
            window = builder.build(
                window_id=f"{self.run_id}_w{i}", accepted_events=batch,
                quarantined_count=total_quarantined if i == 0 else 0,
                expected_sources=expected,
                duration_target_minutes=self.observation_window_minutes)
            self.windows.append(window.to_dict())

        # Source health.
        healths = LiveSourceHealthEvaluator().evaluate(
            registered_sources=registered, accepted_events=self.accepted_events,
            quarantine_by_source=self.quarantine_by_source)
        self.source_health_summary = LiveSourceHealthEvaluator.summary(healths)

        # Source diet, rhythm, absence.
        self.source_diet = LiveSourceDietAnalyzer().analyze(
            self.accepted_events).to_dict()
        self.rhythm = LiveRhythmAnalyzer().analyze(self.accepted_events).to_dict()
        self.absence = LiveAbsenceAnalyzer().analyze(
            accepted_events=self.accepted_events,
            expected_sources=expected).to_dict()

        # Overload / deprivation.
        self.load = LiveOverloadDeprivationAssessor().assess(
            windows=self.windows,
            source_health_summary=self.source_health_summary,
            source_diet=self.source_diet, absence=self.absence).to_dict()

        # Report-only perceptual metabolism calibration.
        self.metabolism = PerceptualMetabolismCalibrator().calibrate(
            source_health_summary=self.source_health_summary,
            source_diet=self.source_diet, rhythm=self.rhythm,
            absence=self.absence, load=self.load).to_dict()

        # Advisory stability gate.
        self.stability = LiveStabilityGate().evaluate(
            governance_passed=self.governance_result.get(
                "governance_passed", False),
            birth_certificate_present=self.birth_certificate_present,
            safety_ok=self.safety.rejected_count == 0,
            source_health_summary=self.source_health_summary,
            source_diet=self.source_diet, load=self.load,
            quarantine_rate=self._quarantine_rate()).to_dict()

    def _quarantine_rate(self) -> float:
        accepted = len(self.accepted_events)
        quarantined = sum(self.quarantine_by_source.values())
        total = accepted + quarantined
        return quarantined / total if total else 0.0

    # -- result + integration views -----------------------------------------

    def _result(self) -> Dict[str, Any]:
        return {
            "refused": False, "run_id": self.run_id, "blocked": self.blocked,
            "blockers": list(self.blockers),
            "accepted_event_count": len(self.accepted_events),
            "window_count": len(self.windows),
            "load_status": self.load.get("load_status"),
            "live_stability_status": self.stability.get("live_stability_status"),
            "recommended_next_phase": self.stability.get(
                "recommended_next_phase"),
            "first_day_record": self.first_day_record.get("markdown"),
            "report": self.reports.get("markdown"),
        }

    def observation_status(self) -> Dict[str, Any]:
        return {
            "live_observation_enabled": True,
            "observation_run_id": self.run_id,
            "live_observation_blocked": self.blocked,
            "live_observation_window_count": len(self.windows),
            "live_observation_accepted_event_count": len(self.accepted_events),
            "live_observation_quarantine_rate": round(self._quarantine_rate(), 3),
            "live_source_count": self.source_health_summary.get(
                "live_source_count", 0),
            "live_healthy_source_count": self.source_health_summary.get(
                "live_healthy_source_count", 0),
            "live_source_diet_balance": self.source_diet.get("balance"),
            "live_load_status": self.load.get("load_status", "unknown"),
            "live_stability_status": self.stability.get(
                "live_stability_status", "inconclusive"),
            "live_recommended_next_phase": self.stability.get(
                "recommended_next_phase", "continue_observation"),
            "metabolism_calibration_confidence": self.metabolism.get(
                "calibration_confidence"),
            "first_day_record_path": self.first_day_record.get("markdown"),
            "latest_observation_report_path": self.reports.get("markdown"),
            "live_observation_safety_block_count": self.safety.rejected_count,
            "learns": False, "forms_concepts": False, "births_signs": False,
            "starts_feeders": False, "controls_hardware": False,
            "accesses_network": False, "runs_git": False,
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.observation_status()

    def next_phase_recommendations(self) -> List[Dict[str, str]]:
        """Recommend next phases; never start them automatically."""
        if self.blocked:
            return [{"phase": "fix_blockers",
                     "detail": "fix governance / birth-certificate blockers "
                               "before observing"}]
        next_phase = self.stability.get("recommended_next_phase",
                                        "continue_observation")
        recs = [{"phase": next_phase,
                 "detail": "advisory next phase from the stability gate"}]
        for correction in self.stability.get("corrections", []):
            recs.append({"phase": "correction", "detail": correction})
        return recs

    def write_artifacts(self) -> Dict[str, Any]:
        from .first_day_record import FirstDayRecordBuilder
        from .reports import LiveObservationReportBuilder

        self._write_state()
        self.first_day_record = FirstDayRecordBuilder(self).write()
        self.reports = LiveObservationReportBuilder(self).write()
        return {"reports": self.reports, "first_day_record": self.first_day_record}

    def _write_state(self) -> None:
        import json

        base = os.path.join(self.state_dir, "observation")

        def dump(subdir: str, name: str, obj: Any) -> None:
            path = os.path.join(base, subdir, name)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, indent=2, default=str)

        for window in self.windows:
            dump("windows", f"{window['window_id']}.json", window)
        dump("source_health", f"{self.run_id}.json", self.source_health_summary)
        dump("source_diet", f"{self.run_id}.json", self.source_diet)
        dump("metabolism", f"{self.run_id}.json", self.metabolism)
        dump("index", f"{self.run_id}.json", self.observation_status())
