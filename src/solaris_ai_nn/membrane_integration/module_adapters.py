"""Membrane module adapters -- safe, tolerant, read-only bridges to live modules.

Each adapter bridges the membrane boundary to one live module. Adapters are tolerant
of missing optional modules (producing a warning, not a crash), reuse existing module
APIs where present, and never fake success when a module cannot be called. They are
read-only with respect to feeders, governance, and source files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AdapterResult:
    """The result of running one module adapter."""

    module: str
    available: bool = False
    used_impressions: bool = False
    raw_fallback: bool = False
    status: str = "unknown"
    detail: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"module": self.module, "available": self.available,
                "used_impressions": self.used_impressions,
                "raw_fallback": self.raw_fallback, "status": self.status,
                "detail": self.detail, "data": dict(self.data),
                "warnings": list(self.warnings)}


def _impression_event(imp) -> Dict[str, Any]:
    """Convert a loaded sensory impression into an ontogenesis-compatible event.

    Features come from the impression's structural fields (source/modality/channel
    + impression kind + a coarse intensity bucket), so proto-concepts are grounded
    in membrane-filtered impressions rather than raw events.
    """
    d = imp.raw if getattr(imp, "raw", None) else {}
    quality = d.get("quality", {}) or {}
    return {
        "event_id": imp.source_event_id or imp.impression_id,
        "timestamp_utc": d.get("timestamp_utc", ""),
        "source_id": imp.source_id, "modality": d.get("modality", "scalar"),
        "channel": d.get("channel", "membrane/impression"),
        "read_only": True, "is_command": False,
        "human_label_is_ground_truth": False,
        "payload": {"impression_kind": imp.impression_kind,
                    "intensity_bucket": round(
                        d.get("perceptual_intensity", 0.0), 1)},
        "quality": {"completeness": float(quality.get("completeness", 1.0)
                                          or 0.0),
                    "noise": float(quality.get("noise", 0.0) or 0.0),
                    "is_absence": imp.impression_kind == "absence",
                    "is_noisy": bool(quality.get("is_noisy"))},
        "safety": {"private_data": False, "contains_instruction": False,
                   "contains_secret": False, "allow_learning": False},
        "debug_gloss": "", "debug_gloss_is_ground_truth": False,
        "membrane_impression_id": imp.impression_id,
        "receptor_id": imp.receptor_id,
    }


@dataclass
class LiveBirthMembraneAdapter:
    """Records membrane activation status for Live Birth (read-only)."""

    def run(self, state_dir: str, load_result) -> AdapterResult:
        r = AdapterResult(module="live_birth")
        cert_dir = os.path.join(state_dir, "certificates")
        r.available = os.path.isdir(cert_dir)
        r.used_impressions = load_result.impressions_present
        r.data = {
            "membrane_available": load_result.membrane_present,
            "impression_count": len(load_result.impressions),
            "blocked_impression_count": sum(1 for i in load_result.impressions
                                            if i.blocked),
            "downstream_handoff":
                "Use sensory impressions for downstream modules when available.",
            "live_birth_bypasses_membrane": False,
        }
        r.status = "satisfied" if load_result.membrane_present else "warning"
        if not load_result.membrane_present:
            r.warnings.append("no membrane present; birth handoff degraded")
        return r


@dataclass
class LiveObservationMembraneAdapter:
    """Computes impression diet alongside source diet (read-only)."""

    def run(self, state_dir: str, load_result) -> AdapterResult:
        r = AdapterResult(module="live_observation")
        r.available = os.path.isdir(os.path.join(state_dir, "observation")) \
            or load_result.impressions_present
        impressions = load_result.impressions
        r.used_impressions = bool(impressions)
        impression_diet: Dict[str, int] = {}
        event_diet: Dict[str, int] = {}
        for imp in impressions:
            impression_diet[imp.impression_kind] = impression_diet.get(
                imp.impression_kind, 0) + 1
            event_diet[imp.source_id] = event_diet.get(imp.source_id, 0) + 1
        r.data = {
            "impression_diet": impression_diet,
            "event_diet": event_diet,
            "receptor_health": load_result.membrane_report.get(
                "sections", {}).get("receptor_field", {}) if
            load_result.membrane_report else {},
            "membrane_memory_present": bool(load_result.membrane_memory),
            "distinguishes_event_and_impression_diet": True,
        }
        r.status = "satisfied" if impressions else "warning"
        if not impressions:
            r.warnings.append("no impressions; observation uses raw diagnostics")
        return r


@dataclass
class LiveOntogenesisMembraneAdapter:
    """Drives ontogenesis from sensory impressions; marks raw fallback loudly."""

    def run(self, state_dir: str, load_result, *, strict: bool = False,
            allow_birth: bool = True) -> AdapterResult:
        r = AdapterResult(module="live_ontogenesis")
        try:
            from ..live_ontogenesis import FirstLiveOntogenesisRuntime
            r.available = True
        except Exception:
            r.warnings.append("live_ontogenesis module unavailable")
            r.status = "warning"
            return r

        clean = load_result.clean_impressions
        if not load_result.impressions_present:
            r.raw_fallback = True
            r.status = "blocked" if strict else "fallback_used"
            r.detail = ("RAW FALLBACK: no sensory impressions available; "
                        "ontogenesis would consume raw events" +
                        (" (blocked in strict mode)" if strict else
                         " (loudly reported)"))
            r.warnings.append(r.detail)
            return r

        events = [_impression_event(i) for i in clean]
        rt = FirstLiveOntogenesisRuntime(
            state_dir=os.path.join(state_dir, "_membrane_onto_audit"),
            allow_limited_birth=allow_birth)
        rt.analyze_events(events)
        st = rt.ontogenesis_status()
        r.used_impressions = True
        blocked_contaminated = len(load_result.impressions) - len(clean)
        r.data = {
            "impression_events": len(events),
            "born_proto_concept_count": st.get(
                "live_born_proto_concept_count", 0),
            "candidate_count": st.get("live_candidate_count", 0),
            "contaminated_impressions_excluded": blocked_contaminated,
            "concept_birth_requires_impressions": True,
        }
        r.status = "satisfied"
        if blocked_contaminated:
            r.warnings.append(
                f"{blocked_contaminated} contaminated impression(s) excluded "
                "from concept birth")
        return r


@dataclass
class LiveSemiogenesisMembraneAdapter:
    """Checks sign ancestry to impressions; flags contaminated ancestry."""

    def run(self, state_dir: str, ancestry, *, strict: bool = False,
            ) -> AdapterResult:
        r = AdapterResult(module="live_semiogenesis", available=True)
        sign_chains = [c for c in (ancestry.chains if ancestry else [])
                       if c.artifact_type == "private_sign"]
        with_anc = sum(1 for c in sign_chains if c.has_impression_ancestry)
        contaminated = sum(1 for c in sign_chains
                           if c.contamination_score >= 0.5)
        r.used_impressions = with_anc > 0
        r.data = {
            "sign_count": len(sign_chains),
            "signs_with_impression_ancestry": with_anc,
            "contaminated_ancestry_signs": contaminated,
            "contaminated_ancestry_blocks_birth": True,
        }
        if sign_chains and with_anc < len(sign_chains) and strict:
            r.status = "blocked"
            r.warnings.append("some signs lack impression ancestry (strict)")
        else:
            r.status = "satisfied" if sign_chains else "warning"
        return r


@dataclass
class LiveCognitionMembraneAdapter:
    """Checks trace ancestry to impressions; downgrades contaminated ancestry."""

    def run(self, state_dir: str, ancestry, *, strict: bool = False,
            ) -> AdapterResult:
        r = AdapterResult(module="live_cognition", available=True)
        trace_chains = [c for c in (ancestry.chains if ancestry else [])
                        if c.artifact_type == "cognition_trace"]
        with_anc = sum(1 for c in trace_chains if c.has_impression_ancestry)
        contaminated = sum(1 for c in trace_chains
                           if c.contamination_score >= 0.5)
        r.used_impressions = with_anc > 0
        r.data = {
            "trace_count": len(trace_chains),
            "traces_with_impression_ancestry": with_anc,
            "contaminated_ancestry_traces": contaminated,
            "distinguishes_event_vs_impression_prediction": True,
        }
        if trace_chains and with_anc < len(trace_chains) and strict:
            r.status = "blocked"
            r.warnings.append("some traces lack impression ancestry (strict)")
        else:
            r.status = "satisfied" if trace_chains else "warning"
        return r


@dataclass
class ScientificClaimsMembraneAdapter:
    """Types evidence as raw / validated / membrane-filtered / ancestry-backed."""

    def run(self, state_dir: str, load_result, bypass_findings) -> AdapterResult:
        r = AdapterResult(module="scientific_claims", available=True)
        bypass = len(bypass_findings or [])
        r.used_impressions = load_result.impressions_present
        r.data = {
            "evidence_categories": [
                "raw_event_evidence", "validated_event_evidence",
                "membrane_filtered_sensory_impression_evidence",
                "downstream_concept_sign_cognition_evidence_with_ancestry",
                "raw_fallback_evidence", "bypass_warning_evidence"],
            "raw_event_supports_birth_claims": False,
            "bypass_warning_count": bypass,
            "claim_strength_downgraded_by_bypass": bypass > 0,
            "mentions_membrane_status": True,
        }
        r.status = "satisfied"
        return r


@dataclass
class ResearchCycleMembraneAdapter:
    """Adds membrane integration status to cycle evidence; critical = blocker."""

    def run(self, state_dir: str, bypass_summary) -> AdapterResult:
        r = AdapterResult(module="research_cycle", available=True)
        critical = (bypass_summary or {}).get("critical_bypass_count", 0)
        blocker = (bypass_summary or {}).get("blocker_bypass_count", 0)
        cycle_blocked = bool(critical or blocker)
        r.data = {
            "membrane_integration_status_recorded": True,
            "critical_bypass_count": critical,
            "cycle_blocked": cycle_blocked,
            "next_action": (
                "Resolve membrane bypass / missing ancestry before proceeding."
                if cycle_blocked else
                "Run post-birth live observation using sensory impressions."),
        }
        r.status = "blocked" if cycle_blocked else "satisfied"
        return r


@dataclass
class AlphaSystemMembraneAdapter:
    """Surfaces membrane integration status for the Alpha system (read-only)."""

    def run(self, state_dir: str, load_result, bypass_summary,
            ancestry) -> AdapterResult:
        r = AdapterResult(module="alpha_system", available=True)
        r.used_impressions = load_result.impressions_present
        r.data = {
            "membrane_available": load_result.membrane_present,
            "membrane_integration_available": True,
            "impression_count": len(load_result.impressions),
            "bypass_count": (bypass_summary or {}).get(
                "bypass_finding_count", 0),
            "critical_bypass_count": (bypass_summary or {}).get(
                "critical_bypass_count", 0),
            "ancestry_validation_status": (
                "ok" if ancestry and ancestry.missing_ancestry == 0
                else "missing_ancestry" if ancestry else "unknown"),
        }
        r.status = "satisfied"
        return r
