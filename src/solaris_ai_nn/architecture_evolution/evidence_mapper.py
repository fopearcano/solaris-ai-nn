"""Evidence mapper -- every recommendation must cite its evidence.

The :class:`ArchitectureEvidenceMap` links modules to evidence (research reports,
ablations, null models, pilot/post-pilot reports, safety invariants, ops
incidents, ...) with a graded strength. Contradictory evidence is retained;
missing artifacts weaken (never strengthen) confidence; and nothing is
fabricated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class EvidenceStrength:
    UNSUPPORTED = "unsupported"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"

    ALL = (UNSUPPORTED, WEAK, MODERATE, STRONG, CONTRADICTED, INCONCLUSIVE)
    _RANK = {UNSUPPORTED: 0, INCONCLUSIVE: 1, WEAK: 2, MODERATE: 3, STRONG: 4}


EVIDENCE_SOURCES = (
    "research_lab_report", "ablation_result", "baseline_comparison",
    "null_model_result", "post_pilot_analysis", "pilot1_report",
    "pilot2_report", "pilot3_report", "safety_invariant_report",
    "assurance_case", "ops_incident", "auto_regeneration_repair",
    "inner_map_snapshot", "perceptual_ontogenesis_report",
    "semiogenesis_report", "sensorium_cognition_report",
    "self_boundary_report", "desire_formation_report",
    "action_reaction_report", "developmental_life_report",
)


def developmental_revision_proposals(dev_status: Dict[str, Any],
                                     ) -> List[Dict[str, Any]]:
    """Turn a developmental-life status into architecture *proposals* only.

    Proposals are advisory: nothing here rewrites code or actuates anything. They
    suggest module pruning/promotion, sensorium/metabolism tuning, concept/sign
    threshold changes, desire/action policy changes, source-diet changes, or pilot
    protocol changes based on long-horizon development.
    """
    proposals: List[Dict[str, Any]] = []
    verdict = str(dev_status.get("structural_growth_status", "inconclusive"))
    if verdict in ("mere_event_accumulation", "log_bloat"):
        proposals.append({
            "target": "module_pruning",
            "proposal": "review modules that accumulate without growth",
            "reason": f"growth verdict: {verdict}",
            "advisory_only": True})
    if verdict == "fixture_overfit":
        proposals.append({
            "target": "source_diet_changes",
            "proposal": "broaden source diet / add live read-only exposure",
            "reason": "fixture overfit detected",
            "advisory_only": True})
    if verdict == "human_label_overfit":
        proposals.append({
            "target": "contamination_mitigation",
            "proposal": "reduce human-label weight in sign/concept formation",
            "reason": "human-label overfit detected",
            "advisory_only": True})
    if int(dev_status.get("regression_count", 0) or 0) > 0:
        proposals.append({
            "target": "pilot_protocol_changes",
            "proposal": "schedule auto-regeneration / regression review",
            "reason": "regressions recorded",
            "advisory_only": True})
    if int(dev_status.get("plateau_count", 0) or 0) > 0:
        proposals.append({
            "target": "sensorium_changes",
            "proposal": "vary sensorium / consolidation to break a plateau",
            "reason": "plateaus recorded",
            "advisory_only": True})
    return proposals


def action_reaction_revision_proposals(ar_status: Dict[str, Any],
                                       ) -> List[Dict[str, Any]]:
    """Turn an action-reaction status into architecture *proposals* only.

    Proposals are advisory: nothing here rewrites code or actuates anything. They
    suggest action-policy, habit-threshold, inhibition-threshold, desire-
    arbitration, no-op-policy, or safety-gate revisions based on observed action
    consequences.
    """
    proposals: List[Dict[str, Any]] = []
    reactions = int(ar_status.get("reaction_count", 0) or 0)
    disruptive = float(ar_status.get("disruptive_reaction_ratio", 0.0) or 0.0)
    if reactions and disruptive >= 0.5:
        proposals.append({
            "target": "action_policy_revision",
            "proposal": "raise action thresholds; many disruptive reactions",
            "reason": f"disruptive_reaction_ratio {disruptive}",
            "advisory_only": True})
    if int(ar_status.get("no_effect_action_count", 0) or 0) > 0:
        proposals.append({
            "target": "no_op_policy_revision",
            "proposal": "review no-effect actions; prefer no-op or evidence",
            "reason": "no-effect actions recorded",
            "advisory_only": True})
    if int(ar_status.get("blocked_action_count", 0) or 0) > 0:
        proposals.append({
            "target": "safety_gate_reinforcement",
            "proposal": "review desire sources producing forbidden actions",
            "reason": "blocked (forbidden external) actions observed",
            "advisory_only": True})
    if int(ar_status.get("strengthened_habit_count", 0) or 0) > 0:
        proposals.append({
            "target": "habit_threshold_changes",
            "proposal": "review habit strengthening for harmful rigidity",
            "reason": "strengthened habits present",
            "advisory_only": True})
    return proposals


def desire_revision_proposals(df_status: Dict[str, Any],
                              ) -> List[Dict[str, Any]]:
    """Turn a desire-formation status into architecture *proposals* only.

    Proposals are advisory: nothing here rewrites code or actuates anything. They
    suggest valence-weighting, desire-threshold, arbitration-policy, no-op-policy,
    conflict-handling, or safety-gate improvements based on observed desire
    dynamics.
    """
    proposals: List[Dict[str, Any]] = []
    desires = int(df_status.get("desire_candidate_count", 0) or 0)
    inhibited = int(df_status.get("inhibited_desire_count", 0) or 0)
    if desires and inhibited / max(1, desires) >= 0.6:
        proposals.append({
            "target": "desire_threshold",
            "proposal": "lower readiness thresholds; most desires inhibited",
            "reason": f"inhibited/desires = {inhibited}/{desires}",
            "advisory_only": True})
    if int(df_status.get("safety_blocked_desire_count", 0) or 0) > 0:
        proposals.append({
            "target": "safety_gate_improvements",
            "proposal": "review desire sources that produced forbidden actions",
            "reason": "safety-blocked desires observed",
            "advisory_only": True})
    if int(df_status.get("desire_conflict_count", 0) or 0) > 0:
        proposals.append({
            "target": "conflict_handling",
            "proposal": "tune conflict resolution / LOGOS routing",
            "reason": "desire conflicts present",
            "advisory_only": True})
    if int(df_status.get("no_op_count", 0) or 0) == 0 and desires:
        proposals.append({
            "target": "no_op_policy",
            "proposal": "review no-op policy; no inhibition observed",
            "reason": "no no-op decisions despite active desires",
            "advisory_only": True})
    return proposals


def self_boundary_revision_proposals(sb_status: Dict[str, Any],
                                     ) -> List[Dict[str, Any]]:
    """Turn a self-boundary status into architecture *proposals* only.

    Proposals are advisory: nothing here rewrites code or actuates anything. They
    suggest boundary-attribution improvements, feeder-provenance improvements,
    simulation-marker strengthening, ego/dimensional consolidation, source-
    attribution policy changes, or continuity-recovery improvements.
    """
    proposals: List[Dict[str, Any]] = []
    if float(sb_status.get("simulation_boundary_integrity", 1.0) or 1.0) < 1.0:
        proposals.append({
            "target": "simulation_marker_strengthening",
            "proposal": "strengthen simulation/observation boundary markers",
            "reason": "simulation boundary integrity below 1.0",
            "advisory_only": True})
    if float(sb_status.get("source_attribution_uncertainty_score",
                           0.0) or 0.0) >= 0.5:
        proposals.append({
            "target": "source_attribution_policy",
            "proposal": "improve feeder/source provenance attribution",
            "reason": "high source-attribution uncertainty",
            "advisory_only": True})
    if int(sb_status.get("ambiguous_ownership_count", 0) or 0) > 0:
        proposals.append({
            "target": "boundary_attribution_improvements",
            "proposal": "reduce ambiguous ownership via richer provenance",
            "reason": "ambiguous ownership attributions present",
            "advisory_only": True})
    if int(sb_status.get("continuity_break_count", 0) or 0) > 0:
        proposals.append({
            "target": "continuity_recovery_improvements",
            "proposal": "review continuity-recovery handling",
            "reason": "continuity breaks recorded",
            "advisory_only": True})
    return proposals


def cognition_revision_proposals(cog_status: Dict[str, Any],
                                 ) -> List[Dict[str, Any]]:
    """Turn a sensorium-cognition status into architecture *proposals* only.

    Proposals are advisory: nothing here rewrites code or actuates anything. They
    suggest sign-reasoning revision, prediction/simulation threshold changes,
    question-pressure tuning, LOGOS-tension handling, or synthesis/fragment
    preservation changes based on observed cognition.
    """
    proposals: List[Dict[str, Any]] = []
    success = float(cog_status.get("prediction_success_rate", 0.0) or 0.0)
    preds = int(cog_status.get("prediction_count", 0) or 0)
    if preds > 0 and success < 0.3:
        proposals.append({
            "target": "prediction_threshold",
            "proposal": "raise prediction confidence threshold; low success",
            "reason": f"prediction_success_rate {success}",
            "advisory_only": True})
    if int(cog_status.get("cognition_overload_event_count", 0) or 0) > 0:
        proposals.append({
            "target": "simulation_limit",
            "proposal": "lower max_moves/simulations per tick; overload seen",
            "reason": "cognition overload events observed",
            "advisory_only": True})
    if int(cog_status.get("question_pressure_count", 0) or 0) > 20:
        proposals.append({
            "target": "question_pressure_tuning",
            "proposal": "tune question-pressure generation; high volume",
            "reason": "many active question pressures",
            "advisory_only": True})
    if int(cog_status.get("unresolved_tension_count", 0) or 0) > 0:
        proposals.append({
            "target": "logos_tension_handling",
            "proposal": "review preserved-contradiction handling",
            "reason": "unresolved tensions present",
            "advisory_only": True})
    if int(cog_status.get("analogy_failure_count", 0) or 0) > 0:
        proposals.append({
            "target": "sign_reasoning_revision",
            "proposal": "review analogy thresholds; contradicted analogies",
            "reason": "contradicted analogies recorded",
            "advisory_only": True})
    return proposals


def semiogenesis_revision_proposals(sem_status: Dict[str, Any],
                                    ) -> List[Dict[str, Any]]:
    """Turn a semiogenesis status into architecture *proposals* only.

    Proposals are advisory: nothing here rewrites code or actuates anything. They
    suggest semiogenesis tuning, proto-language deprecation/merge, sign-birth
    threshold changes, contamination mitigation, sign-explosion control, or
    private-syntax revision based on the observed sign formation.
    """
    proposals: List[Dict[str, Any]] = []
    contamination = float(sem_status.get("contaminated_sign_ratio", 0.0) or 0.0)
    gloss_dep = float(sem_status.get("gloss_dependence_score", 0.0) or 0.0)
    if contamination >= 0.5 or gloss_dep >= 0.5:
        proposals.append({
            "target": "contamination_mitigation",
            "proposal": "down-weight human-label-contaminated signs / glosses",
            "reason": f"contaminated_sign_ratio {contamination}, "
                      f"gloss_dependence {gloss_dep}",
            "advisory_only": True})
    if int(sem_status.get("sign_explosion_warning_count", 0) or 0) > 0:
        proposals.append({
            "target": "sign_explosion_control",
            "proposal": "tighten max_signs_per_tick / sign-birth thresholds",
            "reason": "sign-explosion warnings observed",
            "advisory_only": True})
    if float(sem_status.get("modality_native_sign_ratio", 0.0) or 0.0) < 0.3:
        proposals.append({
            "target": "semiogenesis_tuning",
            "proposal": "raise modality-native sign-birth priority",
            "reason": "few modality-native signs formed",
            "advisory_only": True})
    if int(sem_status.get("private_syntax_pattern_count", 0) or 0) == 0 \
            and int(sem_status.get("internal_sign_count", 0) or 0) >= 2:
        proposals.append({
            "target": "private_syntax_revision",
            "proposal": "review sign-relation thresholds; no syntax emerged",
            "reason": "signs present but no private syntax patterns",
            "advisory_only": True})
    return proposals


def ontogenesis_revision_proposals(ont_status: Dict[str, Any],
                                   ) -> List[Dict[str, Any]]:
    """Turn a perceptual-ontogenesis status into architecture *proposals* only.

    Proposals are advisory: nothing here rewrites code, edits imports, or
    actuates anything. They suggest sensorium/receptor/metabolism/proto-language/
    world-model schema revisions, contamination mitigation, or concept-explosion
    controls based on the observed ontogenesis.
    """
    proposals: List[Dict[str, Any]] = []
    contamination = float(ont_status.get(
        "human_label_contamination_score", 0.0) or 0.0)
    if contamination >= 0.5:
        proposals.append({
            "target": "sensorium_profile",
            "proposal": "reduce human-label dominance in the source diet",
            "reason": f"human-label contamination {contamination}",
            "advisory_only": True})
        proposals.append({
            "target": "contamination_mitigation",
            "proposal": "mark/down-weight label-grounded concepts",
            "reason": "feature-grounded concepts under-represented",
            "advisory_only": True})
    if int(ont_status.get("concept_explosion_warning_count", 0) or 0) > 0:
        proposals.append({
            "target": "concept_explosion_controls",
            "proposal": "tighten max_concepts_per_tick / birth thresholds",
            "reason": "concept-explosion warnings observed",
            "advisory_only": True})
    if float(ont_status.get("modality_native_concept_ratio", 0.0) or 0.0) < 0.3:
        proposals.append({
            "target": "receptor_profile",
            "proposal": "strengthen non-human modality receptors",
            "reason": "few modality-native concepts formed",
            "advisory_only": True})
    if float(ont_status.get("world_formation_density", 0.0) or 0.0) < 0.2:
        proposals.append({
            "target": "world_model_schema",
            "proposal": "review concept-relation growth thresholds",
            "reason": "sparse world formation",
            "advisory_only": True})
    return proposals


@dataclass
class EvidenceLink:
    """One piece of evidence for/against a module recommendation."""

    module_name: str
    source: str
    strength: str = EvidenceStrength.INCONCLUSIVE
    supports: bool = True
    ref: str = ""
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ArchitectureEvidenceMap:
    """Maps modules to graded evidence; retains contradictions; never fabricates."""

    links: List[EvidenceLink] = field(default_factory=list)
    missing_artifacts: List[str] = field(default_factory=list)

    def add(self, module_name: str, source: str, strength: str,
            *, supports: bool = True, ref: str = "",
            summary: str = "") -> EvidenceLink:
        if strength not in EvidenceStrength.ALL:
            strength = EvidenceStrength.INCONCLUSIVE
        link = EvidenceLink(module_name=module_name, source=source,
                            strength=strength, supports=supports,
                            ref=ref or f"{source}:{module_name}",
                            summary=summary)
        self.links.append(link)
        return link

    def note_missing(self, artifact: str) -> None:
        self.missing_artifacts.append(artifact)

    def for_module(self, module_name: str) -> List[EvidenceLink]:
        return [l for l in self.links if l.module_name == module_name]

    def contradictions(self, module_name: str) -> List[EvidenceLink]:
        return [l for l in self.for_module(module_name)
                if l.strength == EvidenceStrength.CONTRADICTED
                or not l.supports]

    def confidence_for(self, module_name: str) -> str:
        """The graded confidence for a module's recommendation."""
        links = self.for_module(module_name)
        if not links:
            return EvidenceStrength.INCONCLUSIVE
        if any(l.strength == EvidenceStrength.CONTRADICTED for l in links):
            return EvidenceStrength.CONTRADICTED
        best = max(EvidenceStrength._RANK.get(l.strength, 0)
                   for l in links if l.supports) if any(
                       l.supports for l in links) else 0
        # Missing artifacts weaken confidence by one rank (floor at weak).
        if self.missing_artifacts and best > 2:
            best -= 1
        inv = {v: k for k, v in EvidenceStrength._RANK.items()}
        return inv.get(best, EvidenceStrength.INCONCLUSIVE)

    def refs_for(self, module_name: str) -> List[str]:
        return [l.ref for l in self.for_module(module_name)]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "link_count": len(self.links),
            "missing_artifacts": list(self.missing_artifacts),
            "modules": sorted({l.module_name for l in self.links}),
            "links": [l.to_dict() for l in self.links],
            "sources": list(EVIDENCE_SOURCES),
        }
