"""Review-assimilation reports -- local research documents, ClaimGuard-scanned.

:class:`ReviewerFeedbackAssimilationReportBuilder` writes the review assimilation
report plus the feedback-manifest / objection-classification / reproduction-outcomes
/ claim-impact / theory-impact / evidence-gap / experiment-recommendations /
claim-revision / publication-readiness / review-queue documents. Every report
states explicitly that reviewer feedback is assimilated as research evidence (not
model training), that nothing was published, no reviewer contacted, no Git/GitHub
operation occurred, no command/experiment executed, no external agent run, and no
consciousness/life/agency claim made. ClaimGuard scans the Markdown.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_WHAT_THIS_DOES_NOT_DO = (
    "Reviewer feedback is assimilated as research evidence, not as model "
    "training.",
    "No publication occurred.",
    "No reviewer was contacted.",
    "No Git or GitHub operation occurred.",
    "No commands or experiments were executed automatically.",
    "No external agent was run.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class ReviewerFeedbackAssimilationReportBuilder:
    """Builds the review-assimilation report set (JSON + claim-guarded Markdown)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.review_assimilation_status()
        sections: Dict[str, Any] = {
            "purpose": ("assimilate local reviewer feedback (objections, "
                        "reproduction outcomes, adversarial findings) into the "
                        "research ledger as evidence: classify objections, "
                        "assess claim/theory impact, map evidence gaps, propose "
                        "reviewer-driven experiments and claim revisions, and "
                        "revise publication readiness -- never as model training"),
            "feedback_manifest": rt.manifest.to_dict(),
            "objection_classification": rt.objections,
            "reproduction_outcomes": rt.reproductions,
            "claim_impact": rt.claim_impact,
            "theory_impact": rt.theory_impact,
            "evidence_gap_map": rt.evidence_gaps,
            "experiment_recommendations": rt.recommendations,
            "claim_revision_proposals": rt.claim_revisions,
            "publication_readiness_revision": rt.publication_revision,
            "review_queue": rt.queue.to_dict(),
            "scientific_claims_proposals": rt.scientific_claims_proposals(),
            "research_cycle_inputs": rt.research_cycle_inputs(),
            "safety_status": rt.safety.snapshot(),
            "status": status,
            "what_this_does_not_do": list(_WHAT_THIS_DOES_NOT_DO),
        }
        markdown = self._render_main(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _render_main(self, sections: Dict[str, Any]) -> str:
        status = sections["status"]
        lines = [
            "# Review Assimilation Report", "",
            "_Assimilates local reviewer feedback as research evidence -- NOT as "
            "model training, RLHF, or a Human Feedback / Teaching Loop. It does "
            "not publish, upload, contact reviewers, call Git/GitHub or external "
            "services, execute commands, or run experiments, and it makes no "
            "claim of consciousness, sentience, biological life, personhood, "
            "agency, free will, emotion, feeling, understanding, self-awareness, "
            "or subjective experience._", "",
            f"- feedback artifacts: {status['reviewer_feedback_artifact_count']}",
            f"- objections: {status['reviewer_objection_count']} "
            f"(valid {status['valid_objection_count']}, partial "
            f"{status['partially_valid_objection_count']}, critical "
            f"{status['critical_objection_count']}, unresolved "
            f"{status['unresolved_objection_count']}, unresolved-critical "
            f"{status['unresolved_critical_objection_count']})",
            f"- reproduction outcomes: {status['reproduction_outcome_count']} "
            f"(success {status['reproduction_success_count']}, failure "
            f"{status['reproduction_failure_count']})",
            f"- claim impacts: {status['claim_impact_count']} "
            f"(downgrades {status['claim_downgrade_count']}, falsifications "
            f"{status['claim_falsification_count']})",
            f"- theory impacts: {status['theory_impact_count']} "
            f"(revisions {status['theory_revision_count']})",
            f"- evidence gaps: {status['evidence_gap_count']} "
            f"(critical {status['critical_evidence_gap_count']})",
            f"- experiment recommendations: "
            f"{status['reviewer_driven_experiment_count']}",
            f"- claim revision proposals: "
            f"{status['claim_revision_proposal_count']}",
            f"- publication readiness impact: "
            f"**{status['publication_readiness_impact']}**",
            f"- review queue items: {status['review_queue_item_count']}",
            "",
            "## Objection classification", "",
        ]
        for c in sections["objection_classification"].get("classifications", []):
            lines.append(f"- [{c['severity']}/{c['validity']}] {c['category']}: "
                         f"{c['text'][:70]}"
                         + (" (BLOCKS)" if c.get("blocks") else ""))
        lines += ["", "## Claim impacts", ""]
        lines += [f"- {i['claim_id']}: {i['impact_type']} ({i['severity']})"
                  for i in sections["claim_impact"].get("impacts", [])] \
            or ["- none"]
        lines += ["", "## Experiment recommendations", ""]
        for r in sections["experiment_recommendations"].get(
                "recommendations", []):
            ctx = f" [{r['safety_context']}]" if r.get("safety_context") else ""
            lines.append(f"- [{r['priority']}] {r['recommendation_type']}{ctx}")
        lines += ["", "## Claim revision proposals", ""]
        for p in sections["claim_revision_proposals"].get("proposals", []):
            lines.append(f"- [{p['status']}] {p['claim_id']}: "
                         f"{p['revision_type']}")
        lines += ["", "## Publication readiness revision", "",
                  f"- impact: **{sections['publication_readiness_revision'].get('publication_readiness_impact')}**"]
        for b in sections["publication_readiness_revision"].get("blockers", []):
            lines.append(f"- blocker: {b['blocker_type']}: {b['detail']}")
        lines += ["", "## Unresolved objections", ""]
        unresolved = [c for c in
                      sections["objection_classification"].get(
                          "classifications", []) if c.get("open")]
        lines += [f"- {c['category']}: {c['text'][:70]}" for c in unresolved] \
            or ["- none"]
        lines += ["", "## Evidence gaps", ""]
        lines += [f"- [{g['severity']}] {g['category']}"
                  for g in sections["evidence_gap_map"].get("gaps", [])] \
            or ["- none"]
        lines += ["", "## Safety status", "",
                  "- no publish/upload/reviewer-contact, no Git/GitHub, no "
                  "command/experiment execution, no training from feedback"]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in sections["what_this_does_not_do"]]
        return "\n".join(lines)

    @staticmethod
    def _claim_guard_safe(text: str) -> bool:
        try:
            from ..governance.compliance import ClaimGuard

            return ClaimGuard().scan_text(text).safe
        except Exception:
            return True

    @staticmethod
    def _guard(text: str) -> str:
        try:
            from ..governance.compliance import ClaimGuard

            guard = ClaimGuard()
            if not guard.scan_text(text).safe:
                return guard.rewrite(text)
        except Exception:
            pass
        return text

    def _sub_reports(self, sections: Dict[str, Any]) -> Dict[str, str]:
        s = sections
        return {
            "FEEDBACK_MANIFEST.md": self._manifest_md(s),
            "OBJECTION_CLASSIFICATION.md": self._objections_md(s),
            "REPRODUCTION_OUTCOMES.md": self._repro_md(s),
            "CLAIM_IMPACT.md": self._claim_impact_md(s),
            "THEORY_IMPACT.md": self._theory_md(s),
            "EVIDENCE_GAP_MAP.md": self._gap_md(s),
            "EXPERIMENT_RECOMMENDATIONS.md": self._rec_md(s),
            "CLAIM_REVISION_PROPOSALS.md": self._revision_md(s),
            "PUBLICATION_READINESS_REVISION.md": self._readiness_md(s),
            "REVIEW_QUEUE.md": self._queue_md(s),
        }

    def _manifest_md(self, s: Dict[str, Any]) -> str:
        man = s["feedback_manifest"]
        lines = ["# Feedback Manifest", "",
                 f"- feedback artifacts: "
                 f"{man['reviewer_feedback_artifact_count']} "
                 f"(missing {man['missing_feedback_count']}, negative "
                 f"{man['negative_feedback_count']})", "",
                 "| source | status | negative |", "| --- | --- | --- |"]
        for a in man.get("artifacts", []):
            lines.append(f"| {a['source_type']} | {a['status']} | "
                         f"{a['is_negative']} |")
        lines += ["", "_Indexes local feedback only; contacts no reviewer, "
                  "uploads nothing; negative feedback is preserved._"]
        return self._guard("\n".join(lines))

    def _objections_md(self, s: Dict[str, Any]) -> str:
        o = s["objection_classification"]
        lines = ["# Objection Classification", "",
                 f"- objections: {o.get('reviewer_objection_count', 0)} "
                 f"(valid {o.get('valid_objection_count', 0)}, critical "
                 f"{o.get('critical_objection_count', 0)}, unresolved "
                 f"{o.get('unresolved_objection_count', 0)})", "",
                 "| category | severity | validity | blocks |",
                 "| --- | --- | --- | --- |"]
        for c in o.get("classifications", []):
            lines.append(f"| {c['category']} | {c['severity']} | "
                         f"{c['validity']} | {c['blocks']} |")
        lines += ["", "_Objections are never dismissed by default; critical open "
                  "objections block the relevant status._"]
        return self._guard("\n".join(lines))

    def _repro_md(self, s: Dict[str, Any]) -> str:
        r = s["reproduction_outcomes"]
        lines = ["# Reproduction Outcomes", "",
                 f"- outcomes: {r.get('reproduction_outcome_count', 0)} "
                 f"(success {r.get('reproduction_success_count', 0)}, failure "
                 f"{r.get('reproduction_failure_count', 0)}, project-limitation "
                 f"{r.get('project_limitation_count', 0)})", ""]
        for o in r.get("outcomes", []):
            lines.append(f"- {o['challenge_type']}: {o['status']}"
                         + (f" ({o['failure_reason']})" if o['failure_reason']
                            else ""))
        lines += ["", "_Failed/partial reproduction is evidence; successful "
                  "reproduction proves nothing about consciousness/life/agency; a "
                  "missing artifact is a project limitation._"]
        return self._guard("\n".join(lines))

    def _claim_impact_md(self, s: Dict[str, Any]) -> str:
        ci = s["claim_impact"]
        lines = ["# Claim Impact", "",
                 f"- impacts: {ci.get('claim_impact_count', 0)} "
                 f"(downgrades {ci.get('claim_downgrade_count', 0)}, "
                 f"falsifications {ci.get('claim_falsification_count', 0)})", "",
                 "| claim | impact | severity |", "| --- | --- | --- |"]
        for i in ci.get("impacts", []):
            lines.append(f"| {i['claim_id']} | {i['impact_type']} | "
                         f"{i['severity']} |")
        lines += ["", "_Claim impacts are proposals; the Scientific Claim "
                  "Registry remains the source of truth._"]
        return self._guard("\n".join(lines))

    def _theory_md(self, s: Dict[str, Any]) -> str:
        t = s["theory_impact"]
        lines = ["# Theory Impact", "",
                 f"- impacts: {t.get('theory_impact_count', 0)} "
                 f"(revisions {t.get('theory_revision_count', 0)}, retired "
                 f"{t.get('theory_retired_count', 0)})", ""]
        for i in t.get("impacts", []):
            lines.append(f"- {i['theory_id'] or '(unlinked)'}: {i['impact_type']}")
        lines += ["", "_Theory impact preserves prior statements; narrowing is "
                  "preferred over hype; it proves nothing about consciousness._"]
        return self._guard("\n".join(lines))

    def _gap_md(self, s: Dict[str, Any]) -> str:
        g = s["evidence_gap_map"]
        lines = ["# Evidence Gap Map", "",
                 f"- gaps: {g.get('evidence_gap_count', 0)} "
                 f"(critical {g.get('critical_evidence_gap_count', 0)})", ""]
        for gap in g.get("gaps", []):
            lines.append(f"- [{gap['severity']}] {gap['category']}"
                         + (" (blocks readiness)" if gap.get("blocks_readiness")
                            else ""))
        lines += ["", "_Gaps map to claims/blockers where possible; critical "
                  "gaps block readiness and become next-cycle tasks._"]
        return self._guard("\n".join(lines))

    def _rec_md(self, s: Dict[str, Any]) -> str:
        r = s["experiment_recommendations"]
        lines = ["# Experiment Recommendations", "",
                 f"- recommendations: "
                 f"{r.get('reviewer_driven_experiment_count', 0)} "
                 f"(experiment inputs {r.get('experiment_input_count', 0)})", ""]
        for rec in r.get("recommendations", []):
            ctx = f" [{rec['safety_context']}]" if rec.get("safety_context") \
                else ""
            lines.append(f"- [{rec['priority']}] {rec['recommendation_type']}"
                         f"{ctx}")
        lines += ["", "_Recommendations are instructions only; no experiment is "
                  "executed and no branch is created._"]
        return self._guard("\n".join(lines))

    def _revision_md(self, s: Dict[str, Any]) -> str:
        cr = s["claim_revision_proposals"]
        lines = ["# Claim Revision Proposals", "",
                 f"- proposals: {cr.get('claim_revision_proposal_count', 0)} "
                 f"(blocked-unsafe {cr.get('blocked_unsafe_wording_count', 0)})",
                 ""]
        for p in cr.get("proposals", []):
            lines.append(f"- [{p['status']}] {p['claim_id']}: "
                         f"{p['revision_type']}")
            lines.append(f"    proposed: {p['proposed_wording']}")
        lines += ["", "_Proposals do not edit the claim registry; unsafe wording "
                  "is blocked and safe wording still includes limitations._"]
        return self._guard("\n".join(lines))

    def _readiness_md(self, s: Dict[str, Any]) -> str:
        pr = s["publication_readiness_revision"]
        lines = ["# Publication Readiness Revision", "",
                 f"- impact: **{pr.get('publication_readiness_impact')}**",
                 f"- blockers: {pr.get('publication_readiness_blocker_count', 0)}",
                 ""]
        for b in pr.get("blockers", []):
            lines.append(f"- {b['blocker_type']}: {b['detail']}")
        lines += ["", "_Publication readiness is advisory; no publication occurs "
                  "and critical unresolved objections block readiness._"]
        return self._guard("\n".join(lines))

    def _queue_md(self, s: Dict[str, Any]) -> str:
        q = s["review_queue"]
        lines = ["# Review Queue", "",
                 f"- items: {q.get('review_queue_item_count', 0)} "
                 f"(open {q.get('open_queue_item_count', 0)})", ""]
        for i in q.get("items", []):
            lines.append(f"- [{i['priority']}/{i['status']}] {i['item_type']}: "
                         f"{i['detail']}")
        lines += ["", "_The queue is local metadata; it executes no task and "
                  "preserves unresolved items._"]
        return self._guard("\n".join(lines))

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = state_dir or self.runtime.state_dir
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "REVIEW_ASSIMILATION_REPORT.md")
        json_path = os.path.join(base, "REVIEW_ASSIMILATION_REPORT.json")
        markdown = self._render_main(report["sections"])
        if not report["claim_guard_safe"]:
            markdown = self._guard(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        written = [md_path, json_path]
        for name, body in self._sub_reports(report["sections"]).items():
            path = os.path.join(base, name)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self._guard(body))
            written.append(path)
        return {"markdown": md_path, "json": json_path, "documents": written,
                "report": report}
