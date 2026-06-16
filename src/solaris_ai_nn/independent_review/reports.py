"""Independent review reports -- local review documents, ClaimGuard-scanned.

:class:`IndependentReviewReportBuilder` writes the independent review report plus
the manifest / sanitization / reviewer-pack / reproducibility-challenge / protocol
/ reviewer-questions / adversarial / audit-matrix / response-ledger / readiness
documents. Every report states explicitly that nothing was published or uploaded,
no Git/GitHub operation occurred, no command or experiment was executed
automatically, no external reviewer was contacted, no external agent was run, and
no consciousness/life/agency claim is made. ClaimGuard scans the Markdown.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_WHAT_THIS_DOES_NOT_DO = (
    "No artifacts were published.",
    "No files were uploaded.",
    "No Git or GitHub operation occurred.",
    "No commands or experiments were executed automatically.",
    "No external reviewer was contacted.",
    "No external agent was run.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class IndependentReviewReportBuilder:
    """Builds the independent review report set (JSON + claim-guarded Markdown)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.independent_review_status()
        sections: Dict[str, Any] = {
            "purpose": ("prepare a local, offline independent-review package: "
                        "index artifacts, scan for leak/forbidden-claim risks, "
                        "build a reviewer pack, reproducibility challenges, "
                        "hostile reviewer questions, adversarial alternatives, an "
                        "audit matrix, and an append-only response ledger -- "
                        "without publishing, uploading, or executing anything"),
            "artifact_manifest": rt.manifest.to_dict(),
            "sanitizer_status": rt.sanitizer_report,
            "reviewer_pack": rt.reviewer_pack,
            "reproducibility_challenge": rt.challenges,
            "review_protocol": rt.protocol,
            "reviewer_questions": rt.questions,
            "adversarial_findings": rt.adversarial,
            "audit_matrix": rt.audit_matrix,
            "response_ledger": rt.ledger.to_dict(),
            "review_readiness": rt.readiness,
            "experiment_inputs": rt.experiment_inputs(),
            "safety_status": rt.safety.snapshot(),
            "status": status,
            "what_this_does_not_do": list(_WHAT_THIS_DOES_NOT_DO),
        }
        markdown = self._render_main(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _render_main(self, sections: Dict[str, Any]) -> str:
        status = sections["status"]
        man = sections["artifact_manifest"]
        lines = [
            "# Independent Review Report", "",
            "_Prepares a local, offline package for independent reproducibility "
            "and critique. It does NOT publish, upload, contact reviewers, call "
            "Git/GitHub or external services, execute commands, or run "
            "experiments, and it makes no claim of consciousness, sentience, "
            "biological life, personhood, agency, free will, emotion, feeling, "
            "understanding, self-awareness, or subjective experience._", "",
            f"- artifacts indexed: {man['independent_review_artifact_count']} "
            f"(present {man.get('present_artifact_count', 0)}, missing "
            f"{man['missing_review_artifact_count']}, missing-critical "
            f"{man['missing_critical_artifact_count']})",
            f"- sanitizer: {status['sanitizer_finding_count']} finding(s) "
            f"({status['critical_sanitizer_finding_count']} critical)",
            f"- reproducibility challenges: "
            f"{status['reproducibility_challenge_count']} "
            f"({status['unavailable_challenge_count']} unavailable)",
            f"- reviewer questions: {status['reviewer_question_count']}",
            f"- adversarial alternatives: "
            f"{status['alternative_explanation_count']}",
            f"- audit matrix blockers: {status['audit_matrix_blocker_count']}",
            f"- unresolved objections: {status['unresolved_objection_count']}",
            f"- review readiness: **{status['review_readiness_status']}**",
            "",
            "## Readiness blockers", "",
        ]
        blockers = sections["review_readiness"].get("blockers", [])
        lines += [f"- {b['blocker_type']}: {b['detail']}" for b in blockers] \
            or ["- none"]
        lines += ["", "## Missing artifacts", ""]
        missing = [a["category"] for a in man.get("artifacts", [])
                   if a.get("status") == "missing"]
        lines += [f"- {m}" for m in missing] or ["- none"]
        lines += ["", "## Strongest objections / alternatives", ""]
        strong = [e for e in sections["adversarial_findings"].get(
            "explanations", []) if e.get("strong")]
        lines += [f"- {e['explanation_type']}: {e['text']} (needs: "
                  f"{e['evidence_needed']})" for e in strong] or ["- none"]
        lines += ["", "## Limitations (from claim layer)", ""]
        lims = sections["reviewer_pack"].get("sections", {}).get(
            "limitations_table", [])
        lines += [f"- {l.get('text', '')}" for l in lims[:8]] or ["- none"]
        lines += ["", "## Safety status", "",
                  "- no actuation, no hardware/feeders/network/shell, no Git/"
                  "GitHub, no publish/upload, no command/experiment execution"]
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
            "REVIEW_MANIFEST.md": self._manifest_md(s),
            "SANITIZATION_REPORT.md": self._sanitizer_md(s),
            "REVIEWER_PACK.md": self._pack_md(s),
            "REPRODUCIBILITY_CHALLENGE.md": self._challenge_md(s),
            "REVIEW_PROTOCOL.md": self._protocol_md(s),
            "REVIEWER_QUESTIONS.md": self._questions_md(s),
            "ADVERSARIAL_REVIEW.md": self._adversarial_md(s),
            "AUDIT_MATRIX.md": self._matrix_md(s),
            "RESPONSE_LEDGER.md": self._ledger_md(s),
            "REVIEW_READINESS.md": self._readiness_md(s),
        }

    def _manifest_md(self, s: Dict[str, Any]) -> str:
        man = s["artifact_manifest"]
        lines = ["# Review Manifest", "",
                 f"- artifacts: {man['independent_review_artifact_count']} "
                 f"(missing {man['missing_review_artifact_count']})", "",
                 "| category | status | negative/falsified |",
                 "| --- | --- | --- |"]
        for a in man.get("artifacts", []):
            lines.append(f"| {a['category']} | {a['status']} | "
                         f"{a['is_negative_or_falsified']} |")
        lines += ["", "_Indexes local artifacts only; uploads nothing; missing "
                  "artifacts stay visible._"]
        return self._guard("\n".join(lines))

    def _sanitizer_md(self, s: Dict[str, Any]) -> str:
        san = s["sanitizer_status"]
        lines = ["# Sanitization Report", "",
                 f"- status: {san.get('sanitizer_status')} "
                 f"({san.get('sanitizer_finding_count', 0)} finding(s), "
                 f"{san.get('critical_sanitizer_finding_count', 0)} critical)", ""]
        for f in san.get("findings", []):
            lines.append(f"- [{f['severity']}] {f['finding_type']} "
                         f"({f['artifact_ref']})")
        lines += ["", "_Scans local text only; modifies nothing; a critical "
                  "finding blocks readiness and the operator redacts manually._"]
        return self._guard("\n".join(lines))

    def _pack_md(self, s: Dict[str, Any]) -> str:
        pack = s["reviewer_pack"].get("sections", {})
        lines = ["# Reviewer Pack", "",
                 f"## Purpose", "", pack.get("purpose", ""), "",
                 "## What is being claimed", ""]
        lines += [f"- {c}" for c in pack.get("what_is_being_claimed", [])]
        lines += ["", "## What is NOT being claimed", ""]
        lines += [f"- {c}" for c in pack.get("what_is_not_being_claimed", [])]
        lines += ["", "## Required commands", ""]
        lines += [f"- `{c}`" for c in pack.get("required_commands", [])] \
            or ["- none currently runnable"]
        lines += ["", "## Counterevidence", ""]
        lines += [f"- {r.get('counter_type')}: {r.get('detail')}"
                  for r in pack.get("counterevidence_table", [])] or ["- none"]
        lines += ["", "## Reviewer checklist", ""]
        lines += [f"- {c}" for c in pack.get("reviewer_checklist", [])]
        lines += ["", f"_{pack.get('disclaimer', '')}_"]
        return self._guard("\n".join(lines))

    def _challenge_md(self, s: Dict[str, Any]) -> str:
        ch = s["reproducibility_challenge"]
        lines = ["# Reproducibility Challenge", "",
                 f"- challenges: {ch.get('reproducibility_challenge_count', 0)} "
                 f"(available {ch.get('available_challenge_count', 0)}, "
                 f"unavailable {ch.get('unavailable_challenge_count', 0)})", "",
                 "| challenge | status | command | expected |",
                 "| --- | --- | --- | --- |"]
        for st in ch.get("steps", []):
            lines.append(f"| {st['challenge_type']} | {st['status']} | "
                         f"`{st['command']}` | "
                         f"{st['expected']['expected_artifact']} |")
        lines += ["", "_Instructions only; nothing is executed; missing "
                  "prerequisites mark a challenge unavailable._"]
        return self._guard("\n".join(lines))

    def _protocol_md(self, s: Dict[str, Any]) -> str:
        p = s["review_protocol"]
        lines = ["# Review Protocol", "",
                 f"- stages: {p.get('review_protocol_stage_count', 0)} "
                 "(advisory only)", ""]
        for st in p.get("stages", []):
            lines.append(f"- {st['stage_type']}: {st['guidance']}")
        lines += ["", "## Exit criteria", ""]
        lines += [f"- {c}" for c in p.get("exit_criteria", [])]
        lines += ["", "_Instructions and local metadata only; runs no stage "
                  "automatically; the readiness decision is advisory._"]
        return self._guard("\n".join(lines))

    def _questions_md(self, s: Dict[str, Any]) -> str:
        q = s["reviewer_questions"]
        lines = ["# Reviewer Questions", "",
                 f"- questions: {q.get('reviewer_question_count', 0)}", ""]
        for item in q.get("questions", []):
            refs = (f" [claims: {', '.join(item['claim_refs'])}]"
                    if item.get("claim_refs") else "")
            lines.append(f"- ({item['category']}) {item['text']}{refs}")
        lines += ["", "_Hostile but scientifically useful; no answers invented._"]
        return self._guard("\n".join(lines))

    def _adversarial_md(self, s: Dict[str, Any]) -> str:
        adv = s["adversarial_findings"]
        lines = ["# Adversarial Review", "",
                 f"- alternatives: {adv.get('alternative_explanation_count', 0)} "
                 f"(strong {adv.get('strong_alternative_count', 0)})", ""]
        for e in adv.get("explanations", []):
            flag = " (STRONG)" if e.get("strong") else ""
            lines.append(f"- {e['explanation_type']}{flag}: {e['text']} "
                         f"(needs: {e['evidence_needed']})")
        lines += ["", "_Alternative explanations are preserved and never "
                  "auto-dismissed; a strong alternative downgrades readiness._"]
        return self._guard("\n".join(lines))

    def _matrix_md(self, s: Dict[str, Any]) -> str:
        m = s["audit_matrix"]
        lines = ["# Audit Matrix", "",
                 f"- rows: {m.get('audit_matrix_row_count', 0)} "
                 f"(blockers {m.get('audit_matrix_blocker_count', 0)})", "",
                 "| claim | status | evidence | counter | blocker |",
                 "| --- | --- | --- | --- | --- |"]
        for r in m.get("rows", []):
            lines.append(f"| {r['claim'][:48]} | {r['status']} | "
                         f"{len(r['supporting_evidence'])} | "
                         f"{len(r['counterevidence'])} | {r['blocker_flag']} |")
        lines += ["", "_The matrix exposes gaps; no empty green dashboard; "
                  "falsified/unsupported claims stay visible._"]
        return self._guard("\n".join(lines))

    def _ledger_md(self, s: Dict[str, Any]) -> str:
        led = s["response_ledger"]
        lines = ["# Reviewer Response Ledger", "",
                 f"- objections: {led.get('objection_count', 0)} "
                 f"(open {led.get('open_objection_count', 0)}, unresolved "
                 f"{led.get('unresolved_objection_count', 0)}, accepted-limitation "
                 f"{led.get('accepted_limitation_count', 0)})", ""]
        for o in led.get("objections", []):
            lines.append(f"- [{o['status']}] {o['text']} "
                         f"({o['response_count']} response(s))")
        lines += ["", "_Append-only; objections cannot be deleted; accepted "
                  "limitations/falsifications stay visible; the system cannot "
                  "declare victory over a reviewer by default._"]
        return self._guard("\n".join(lines))

    def _readiness_md(self, s: Dict[str, Any]) -> str:
        r = s["review_readiness"]
        lines = ["# Review Readiness", "",
                 f"- status: **{r.get('review_readiness_status')}**",
                 f"- blockers: {r.get('review_readiness_blocker_count', 0)}", ""]
        for b in r.get("blockers", []):
            lines.append(f"- {b['blocker_type']}: {b['detail']}")
        lines += ["", "_Readiness means the evidence is inspectable, not that the "
                  "claims are strong; a weak or negative result can still be "
                  "review-ready if documented honestly._"]
        return self._guard("\n".join(lines))

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = state_dir or self.runtime.state_dir
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "INDEPENDENT_REVIEW_REPORT.md")
        json_path = os.path.join(base, "INDEPENDENT_REVIEW_REPORT.json")
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
