"""Console summary cards -- concise per-area status cards for the dashboard.

:class:`ConsoleSummaryCard` is a concise card (title, status, explanation, key metrics,
report path, blockers, warnings, next action). Cards distinguish "not run" from
"failed" and "optional skipped" from "missing required", and they carry safety
disclaimers where needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class SummaryCardKind:
    FIXTURE_DEMO = "fixture_demo"
    LIVE_TESTER = "live_tester"
    GOVERNANCE = "governance"
    FEEDER_REGISTRY = "feeder_registry"
    QUARANTINE = "quarantine"
    MEMBRANE = "membrane"
    MEMBRANE_INTEGRATION = "membrane_integration"
    SENSORY_IMPRESSIONS = "sensory_impressions"
    SOURCE_PRESSURE = "source_pressure"
    OBSERVATION = "observation"
    ONTOGENESIS = "ontogenesis"
    SEMIOGENESIS = "semiogenesis"
    COGNITION = "cognition"
    SAFETY = "safety"
    CLAIMS = "claims"
    REPRODUCIBILITY = "reproducibility"
    REGRESSION = "regression"
    ARTIFACT_BUNDLE = "artifact_bundle"
    FEEDBACK = "feedback"
    PACKAGING = "packaging"
    SAFETY_FREEZE = "safety_freeze"
    RELEASE_CANDIDATE = "release_candidate"
    FIRST_TESTER_PROTOCOL = "first_tester_protocol"
    NEXT_ACTION = "next_action"

    ALL = (FIXTURE_DEMO, LIVE_TESTER, GOVERNANCE, FEEDER_REGISTRY, QUARANTINE,
           MEMBRANE, MEMBRANE_INTEGRATION, SENSORY_IMPRESSIONS, SOURCE_PRESSURE,
           OBSERVATION, ONTOGENESIS, SEMIOGENESIS, COGNITION, SAFETY, CLAIMS,
           REPRODUCIBILITY, REGRESSION, ARTIFACT_BUNDLE, FEEDBACK, PACKAGING,
           SAFETY_FREEZE, RELEASE_CANDIDATE, FIRST_TESTER_PROTOCOL,
           NEXT_ACTION)


class SummarySeverity:
    INFO = "info"
    OK = "ok"
    WARNING = "warning"
    BLOCKER = "blocker"
    NOT_RUN = "not_run"
    OPTIONAL_SKIPPED = "optional_skipped"

    ALL = (INFO, OK, WARNING, BLOCKER, NOT_RUN, OPTIONAL_SKIPPED)


@dataclass
class ConsoleSummaryCard:
    """One concise dashboard card."""

    kind: str
    title: str
    status: str = SummarySeverity.NOT_RUN
    explanation: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    report_path: str = ""
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    next_action: str = ""
    disclaimer: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind, "title": self.title, "status": self.status,
            "explanation": self.explanation, "metrics": dict(self.metrics),
            "report_path": self.report_path, "blockers": list(self.blockers),
            "warnings": list(self.warnings), "next_action": self.next_action,
            "disclaimer": self.disclaimer,
        }


@dataclass
class SummaryCardBuilder:
    """Builds the summary cards from discovery, status, and the safety panel."""

    def build(self, discovery, status, safety_panel) -> List[ConsoleSummaryCard]:
        from .artifact_discovery import ArtifactKind as K
        from .status_model import StageHealth

        cards: List[ConsoleSummaryCard] = []
        Card = ConsoleSummaryCard
        S = SummarySeverity

        def health_to_sev(health):
            return {
                StageHealth.PASS: S.OK,
                StageHealth.PASS_WITH_WARNINGS: S.WARNING,
                StageHealth.BLOCKED: S.BLOCKER,
                StageHealth.FAILED: S.BLOCKER,
                StageHealth.MISSING_ARTIFACTS: S.NOT_RUN,
                StageHealth.NOT_STARTED: S.NOT_RUN,
                StageHealth.SKIPPED_OPTIONAL: S.OPTIONAL_SKIPPED,
            }.get(health, S.INFO)

        # Fixture demo.
        fx = discovery.latest(K.TESTER_FIXTURE_REPORT)
        st = status.stage("tester_fixture_demo")
        cards.append(Card(
            SummaryCardKind.FIXTURE_DEMO, "Fixture tester demo",
            status=health_to_sev(st.health) if st else S.NOT_RUN,
            explanation="fixture-only known-good rehearsal" if fx else
            "no fixture demo run yet",
            metrics={"reproducibility": fx.summary.get("reproducibility_status")
                     if fx else None,
                     "regression": fx.summary.get("regression_status")
                     if fx else None} if fx else {},
            report_path=fx.path if fx else "",
            next_action="" if fx else "run `tester-demo`"))

        # Reproducibility / regression.
        repro = discovery.latest(K.TESTER_REPRODUCIBILITY_REPORT)
        cards.append(Card(
            SummaryCardKind.REPRODUCIBILITY, "Reproducibility",
            status=S.OK if repro and repro.summary.get(
                "reproducibility_status") == "pass" else
            (S.WARNING if repro else S.NOT_RUN),
            explanation="ignores timestamps; checks structure + safety",
            metrics={"status": repro.summary.get("reproducibility_status")}
            if repro else {}, report_path=repro.path if repro else ""))
        regr = discovery.latest(K.TESTER_REGRESSION_REPORT)
        cards.append(Card(
            SummaryCardKind.REGRESSION, "Regression",
            status=S.OK if regr and regr.summary.get(
                "regression_status") == "no_regression" else
            (S.WARNING if regr else S.NOT_RUN),
            metrics={"status": regr.summary.get("regression_status")}
            if regr else {}, report_path=regr.path if regr else ""))

        # Live tester + governance + feeder registry.
        live = discovery.latest(K.TESTER_LIVE_REPORT)
        cards.append(Card(
            SummaryCardKind.LIVE_TESTER, "Live-read-only tester",
            status=S.OK if live else S.NOT_RUN,
            explanation="external manual feeders only; Solaris controls none",
            report_path=live.path if live else "",
            next_action="" if live else "run `tester-live-init` then approve "
            "governance by hand"))
        gov = discovery.latest(K.LIVE_GOVERNANCE)
        gov_data = _load(gov.path) if gov else {}
        cards.append(Card(
            SummaryCardKind.GOVERNANCE, "Governance",
            status=S.OK if gov_data.get("operator_approved") else
            (S.WARNING if gov else S.NOT_RUN),
            metrics={"enabled": gov_data.get("live_readonly_enabled"),
                     "approved": gov_data.get("operator_approved")}
            if gov else {}, report_path=gov.path if gov else "",
            disclaimer="governance must be enabled + approved by hand"))
        reg = discovery.latest(K.FEEDER_REGISTRY)
        reg_data = _load(reg.path) if reg else {}
        controllable = any(f.get("solaris_may_control")
                           for f in reg_data.get("feeders", []))
        cards.append(Card(
            SummaryCardKind.FEEDER_REGISTRY, "Feeder registry",
            status=S.BLOCKER if controllable else (S.OK if reg else S.NOT_RUN),
            metrics={"feeder_count": len(reg_data.get("feeders", []))}
            if reg else {},
            blockers=["a feeder grants Solaris control"] if controllable else [],
            report_path=reg.path if reg else "",
            disclaimer="feeders are external/manual; Solaris controls none"))

        # Quarantine.
        q = discovery.latest(K.QUARANTINE_REPORT)
        qcount = q.summary.get("quarantined_count",
                               q.summary.get("quarantine_count", 0)) if q else 0
        cards.append(Card(
            SummaryCardKind.QUARANTINE, "Quarantine",
            status=S.WARNING if qcount else (S.OK if q else S.NOT_RUN),
            explanation="unsafe events are quarantined, never learned",
            metrics={"quarantined_count": qcount}, report_path=q.path if q else ""))

        # Membrane + impressions + source pressure.
        mem = discovery.latest(K.MEMBRANE_REPORT)
        impr = discovery.latest(K.SENSORY_IMPRESSION_INDEX)
        impr_count = impr.summary.get("membrane_impression_count", 0) if impr \
            else 0
        cards.append(Card(
            SummaryCardKind.MEMBRANE, "Environmental membrane",
            status=S.OK if mem else S.NOT_RUN,
            metrics={"impression_count": impr_count}, report_path=mem.path
            if mem else ""))
        cards.append(Card(
            SummaryCardKind.SENSORY_IMPRESSIONS, "Sensory impressions",
            status=S.OK if impr_count else S.NOT_RUN,
            explanation="downstream consumes impressions, not raw events",
            metrics={"impression_count": impr_count},
            report_path=impr.path if impr else ""))
        cards.append(Card(
            SummaryCardKind.SOURCE_PRESSURE, "Source pressure / diet",
            status=S.OK if mem else S.NOT_RUN,
            metrics={"source_pressure_status": mem.summary.get(
                "source_pressure_status")} if mem else {},
            report_path=mem.path if mem else ""))

        # Membrane integration.
        integ = discovery.latest(K.MEMBRANE_INTEGRATION_REPORT)
        integ_data = _load(integ.path) if integ else {}
        integ_status = (integ_data.get("sections", {}) or {}).get("status", {}) \
            if isinstance(integ_data, dict) else {}
        critical = integ_status.get("critical_bypass_count", 0)
        cards.append(Card(
            SummaryCardKind.MEMBRANE_INTEGRATION, "Membrane integration",
            status=S.BLOCKER if critical else (S.OK if integ else S.NOT_RUN),
            metrics={"critical_bypass_count": critical,
                     "raw_fallback_count": integ_status.get(
                         "raw_fallback_count", 0)} if integ else {},
            blockers=[f"{critical} critical bypass"] if critical else [],
            report_path=integ.path if integ else ""))

        # Observation.
        obs = discovery.latest(K.OBSERVATION_REPORT)
        cards.append(Card(
            SummaryCardKind.OBSERVATION, "Live observation",
            status=S.OK if obs else S.NOT_RUN, report_path=obs.path if obs else ""))

        # Optional learning layers.
        for kind, card_kind, title in (
                (K.CONCEPT_MEMORY, SummaryCardKind.ONTOGENESIS,
                 "Live ontogenesis (optional)"),
                (K.SIGN_MEMORY, SummaryCardKind.SEMIOGENESIS,
                 "Live semiogenesis (optional)"),
                (K.COGNITION_MEMORY, SummaryCardKind.COGNITION,
                 "Live cognition (optional)")):
            art = discovery.latest(kind)
            cards.append(Card(
                card_kind, title,
                status=S.OK if art else S.OPTIONAL_SKIPPED,
                explanation="optional layer" if not art else "present",
                report_path=art.path if art else ""))

        # Claims.
        claim = discovery.latest(K.SCIENTIFIC_CLAIM_REPORT)
        claim_blockers = [f.detail for f in safety_panel.findings
                          if f.check == "unsupported_claim"]
        cards.append(Card(
            SummaryCardKind.CLAIMS, "Scientific claims",
            status=S.BLOCKER if claim_blockers else
            (S.OK if claim else S.NOT_RUN),
            explanation="fixture/live evidence is operational, not consciousness",
            blockers=claim_blockers, report_path=claim.path if claim else "",
            disclaimer="no consciousness/life/agency claim is made"))

        # Artifact bundle.
        bundle = discovery.latest(K.TESTER_FIXTURE_BUNDLE) \
            or discovery.latest(K.TESTER_LIVE_BUNDLE)
        cards.append(Card(
            SummaryCardKind.ARTIFACT_BUNDLE, "Artifact bundle",
            status=S.OK if bundle else S.NOT_RUN,
            explanation="local-only; nothing uploaded or published",
            report_path=bundle.path if bundle else ""))

        # Tester feedback (QA ledger).
        fb = discovery.latest(K.TESTER_FEEDBACK_LEDGER) \
            or discovery.latest(K.TESTER_FEEDBACK_REPORT)
        fb_blockers = fb.summary.get("release_blocker_count", 0) if fb else 0
        fb_entries = fb.summary.get("entry_count", 0) if fb else 0
        cards.append(Card(
            SummaryCardKind.FEEDBACK, "Tester feedback (QA ledger)",
            status=S.BLOCKER if fb_blockers else (S.OK if fb else S.NOT_RUN),
            explanation="local QA evidence only; not training, not a command",
            metrics={"entry_count": fb_entries,
                     "release_blocker_count": fb_blockers,
                     "safety_concern_count": fb.summary.get(
                         "safety_concern_count", 0) if fb else 0},
            blockers=[f"{fb_blockers} feedback release blocker(s)"]
            if fb_blockers else [],
            report_path=fb.path if fb else "",
            next_action="fill a feedback form (`tester-feedback-init`)"
            if not fb else "review feedback release blockers"
            if fb_blockers else "",
            disclaimer="feedback does not modify Solaris behaviour"))

        # Tester packaging readiness.
        pkg = discovery.latest(K.TESTER_RELEASE_MANIFEST) \
            or discovery.latest(K.TESTER_PACKAGING_REPORT)
        guide = discovery.latest(K.TESTER_INSTALL_GUIDE)
        pkg_readiness = pkg.summary.get("readiness") if pkg else None
        cards.append(Card(
            SummaryCardKind.PACKAGING, "Install readiness (packaging)",
            status=S.BLOCKER if pkg_readiness == "blocked" else
            (S.OK if pkg else S.NOT_RUN),
            explanation="local editable install; report-only, installs nothing",
            metrics={"readiness": pkg_readiness,
                     "install_guide": bool(guide)},
            report_path=pkg.path if pkg else "",
            next_action="run `tester-packaging`" if not pkg else "",
            disclaimer="packaging installs nothing and publishes nothing"))

        # Tester safety freeze (release gate).
        sf = discovery.latest(K.TESTER_SAFETY_FREEZE_MANIFEST) \
            or discovery.latest(K.TESTER_RELEASE_BLOCKERS)
        sf_blockers = (sf.summary.get("release_blocker_count",
                                      sf.summary.get("open_blocker_count", 0))
                       if sf else 0)
        sf_readiness = sf.summary.get("readiness") if sf else None
        cards.append(Card(
            SummaryCardKind.SAFETY_FREEZE, "Safety freeze (release gate)",
            status=S.BLOCKER if sf_blockers else (S.OK if sf else S.NOT_RUN),
            explanation="tester-release firewall; report/gate-only",
            metrics={"readiness": sf_readiness,
                     "release_blocker_count": sf_blockers,
                     "forbidden_claim_count": sf.summary.get(
                         "forbidden_claim_count", 0) if sf else 0},
            blockers=[f"{sf_blockers} open release blocker(s)"]
            if sf_blockers else [],
            report_path=sf.path if sf else "",
            next_action="run `tester-safety-freeze`" if not sf else
            "resolve open release blockers" if sf_blockers else "",
            disclaimer="the safety freeze is a tester-release gate only"))

        # Tester release candidate (local assembly).
        rc = discovery.latest(K.TESTER_RC_MANIFEST) \
            or discovery.latest(K.TESTER_RC_READINESS_REPORT)
        rc_readiness = rc.summary.get("readiness",
                                      rc.summary.get("status")) if rc else None
        rc_blockers = rc.summary.get("blocker_count", 0) if rc else 0
        rc_bundle = discovery.latest(K.TESTER_RC_BUNDLE_REPORT)
        cards.append(Card(
            SummaryCardKind.RELEASE_CANDIDATE, "Release candidate (local)",
            status=S.BLOCKER if rc_blockers else (S.OK if rc else S.NOT_RUN),
            explanation="local tester RC assembly; publishes/uploads nothing",
            metrics={"readiness": rc_readiness,
                     "blocker_count": rc_blockers,
                     "bundle": bool(rc_bundle)},
            blockers=[f"{rc_blockers} open RC blocker(s)"] if rc_blockers
            else [],
            report_path=rc.path if rc else "",
            next_action="run `tester-rc`" if not rc else
            "resolve open RC blockers" if rc_blockers else "",
            disclaimer="local assembly only; nothing is uploaded or released"))

        # First tester protocol (local, documentation-only).
        ftp = discovery.latest(K.FIRST_TESTER_PROTOCOL_REPORT)
        ftp_status = ftp.summary.get("session_status") if ftp else None
        ftp_blocked = ftp_status == "blocked"
        ftp_script = discovery.latest(K.FIRST_TESTER_SESSION_SCRIPT)
        cards.append(Card(
            SummaryCardKind.FIRST_TESTER_PROTOCOL, "First tester protocol",
            status=S.BLOCKER if ftp_blocked else (S.OK if ftp else S.NOT_RUN),
            explanation="local session script + acceptance + stops + handoff; "
            "documentation-only",
            metrics={"session_status": ftp_status,
                     "session_script": bool(ftp_script)},
            blockers=["session blocked; resolve RC/packaging/safety blockers"]
            if ftp_blocked else [],
            report_path=ftp.path if ftp else "",
            next_action="run `first-tester-protocol`" if not ftp else
            "resolve blockers before the session" if ftp_blocked else
            "run the first tester session following the script",
            disclaimer="documentation-only; it does not run the tester "
            "session"))

        # Safety card (always present, prominent).
        cards.append(Card(
            SummaryCardKind.SAFETY, "Safety",
            status=S.BLOCKER if safety_panel.blocking_findings() else
            (S.WARNING if safety_panel.status == "warnings" else S.OK),
            explanation="read-only console; controls no feeders/hardware/network",
            metrics={"blocker_count": len(safety_panel.blocking_findings()),
                     "finding_count": len(safety_panel.findings)},
            blockers=[f.detail for f in safety_panel.blocking_findings()],
            disclaimer="no consciousness/life/agency claim is made"))
        return cards


def _load(path: str) -> Dict[str, Any]:
    import json
    import os
    try:
        if not os.path.isfile(path) or os.path.getsize(path) > 5_000_000:
            return {}
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}
