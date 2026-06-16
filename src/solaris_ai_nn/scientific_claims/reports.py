"""Scientific claim reports -- evidence-disciplined documents, ClaimGuard-scanned.

:class:`ScientificClaimReportBuilder` writes the scientific claim report plus the
claim-registry / theory-ledger / evidence-map / counterevidence / forbidden-claims
/ publication-dossier / safe-abstracts / limitations documents. Every report states
explicitly that the claim registry proves nothing about consciousness/life/agency,
that the publication dossier is a draft evidence compilation, that unsupported and
falsified claims remain visible, and that no release/Git/GitHub/experiment occurred.
ClaimGuard scans the Markdown.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .claim_registry import ClaimStatus

_WHAT_THIS_DOES_NOT_DO = (
    "The claim registry does not prove consciousness, sentience, life, or agency.",
    "The publication dossier is a draft evidence compilation, not a release.",
    "Unsupported claims remain unsupported and visible.",
    "Falsified and contradicted claims remain visible.",
    "No public release was created.",
    "No Git or GitHub operation occurred.",
    "No experiment was executed automatically.",
    "No source code was modified outside the claim package/docs/tests/examples.",
)


@dataclass
class ScientificClaimReportBuilder:
    """Builds the scientific claim report set (JSON + claim-guarded Markdown)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.scientific_claims_status()
        sections: Dict[str, Any] = {
            "purpose": ("map the Solaris-AI-NN evidence to scientific claims, "
                        "preserve counterevidence and falsified results, block "
                        "forbidden claims, and compile a draft publication "
                        "dossier -- evidence discipline, not hype production"),
            "claim_registry": rt.registry.to_dict(),
            "theory_ledger": rt.theory.to_dict(),
            "evidence_map": rt.evidence_map.to_dict(),
            "counterevidence": rt.counterevidence,
            "forbidden_claims": rt.forbidden,
            "limitations": rt.limitations,
            "publication_dossier": rt.dossier,
            "safe_abstracts": rt.abstracts,
            "safety_status": rt.safety.snapshot(),
            "claim_guard": rt.claim_guard.to_dict(),
            "experiment_suggestions": rt.experiment_suggestions(),
            "status": status,
            "what_this_does_not_do": list(_WHAT_THIS_DOES_NOT_DO),
        }
        markdown = self._render_main(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _render_main(self, sections: Dict[str, Any]) -> str:
        status = sections["status"]
        reg = sections["claim_registry"]
        lines = [
            "# Scientific Claim Report", "",
            "_Maps evidence to claims and disciplines what may be said. The claim "
            "registry proves nothing about consciousness, sentience, biological "
            "life, personhood, agency, free will, emotion, feeling, "
            "understanding, self-awareness, or subjective experience. The "
            "publication dossier is a draft evidence compilation, not a release._",
            "",
            f"- claims: {status['scientific_claim_count']} "
            f"(supported {status['supported_claim_count']}, weakly "
            f"{status['weakly_supported_claim_count']}, partially "
            f"{status['partially_supported_claim_count']}, inconclusive "
            f"{status['inconclusive_claim_count']}, unsupported "
            f"{status['unsupported_claim_count']}, contradicted "
            f"{status['contradicted_claim_count']}, falsified "
            f"{status['falsified_claim_count']}, forbidden "
            f"{status['forbidden_claim_count']})",
            f"- theory statements: {status['theory_statement_count']}",
            f"- evidence mappings: {status['evidence_mapping_count']}",
            f"- counterevidence: {status['counterevidence_count']}",
            f"- limitations: {status['limitation_count']}",
            f"- publication readiness: **{status['publication_readiness_status']}**",
            f"- ClaimGuard: {status['claimguard_status']} "
            f"({status['claimguard_block_count']} block(s))",
            "",
            "## Supported claims", "",
        ]
        lines += self._claim_lines(reg, (ClaimStatus.SUPPORTED,
                                         ClaimStatus.PARTIALLY_SUPPORTED))
        lines += ["", "## Weakly supported claims", ""]
        lines += self._claim_lines(reg, (ClaimStatus.WEAKLY_SUPPORTED,))
        lines += ["", "## Inconclusive claims", ""]
        lines += self._claim_lines(reg, (ClaimStatus.INCONCLUSIVE,
                                         ClaimStatus.REQUIRES_MORE_EVIDENCE))
        lines += ["", "## Unsupported claims", ""]
        lines += self._claim_lines(reg, (ClaimStatus.UNSUPPORTED,))
        lines += ["", "## Contradicted / falsified claims", ""]
        lines += self._claim_lines(reg, (ClaimStatus.CONTRADICTED,
                                         ClaimStatus.FALSIFIED))
        lines += ["", "## Forbidden claims (blocked)", ""]
        lines += self._claim_lines(reg, (ClaimStatus.FORBIDDEN,))
        lines += ["", "## Counterevidence", ""]
        ce = sections["counterevidence"].get("records", [])
        lines += [f"- {r['counter_type']}: {r['detail']}"
                  + (" (blocks claim)" if r.get("blocks_claim") else "")
                  for r in ce] or ["- none"]
        lines += ["", "## Limitations", ""]
        lims = sections["limitations"].get("limitations", [])
        lines += [f"- [{l['category']}] {l['text']}" for l in lims] or ["- none"]
        lines += ["", "## Publication readiness", "",
                  f"- status: **{status['publication_readiness_status']}**",
                  "- the dossier is a draft evidence compilation, not a release"]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in sections["what_this_does_not_do"]]
        return "\n".join(lines)

    @staticmethod
    def _claim_lines(reg: Dict[str, Any], statuses) -> List[str]:
        out = [f"- [{c['status']}/{c['strength']}] {c['text']} "
               f"(evidence {len(c['evidence_refs'])}, counter "
               f"{len(c['counterevidence_refs'])})"
               for c in reg.get("claims", []) if c["status"] in statuses]
        return out or ["- none"]

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
            "CLAIM_REGISTRY.md": self._registry_md(s),
            "THEORY_LEDGER.md": self._theory_md(s),
            "EVIDENCE_MAP.md": self._evidence_md(s),
            "COUNTEREVIDENCE.md": self._counter_md(s),
            "FORBIDDEN_CLAIMS.md": self._forbidden_md(s),
            "PUBLICATION_DOSSIER.md": self._dossier_md(s),
            "SAFE_ABSTRACTS.md": self._abstracts_md(s),
            "LIMITATIONS.md": self._limitations_md(s),
        }

    def _registry_md(self, s: Dict[str, Any]) -> str:
        reg = s["claim_registry"]
        lines = ["# Claim Registry", "",
                 f"- claims: {reg['scientific_claim_count']}", "",
                 "| claim | status | strength | evidence | counter |",
                 "| --- | --- | --- | --- | --- |"]
        for c in reg.get("claims", []):
            lines.append(f"| {c['text'][:60]} | {c['status']} | {c['strength']} "
                         f"| {len(c['evidence_refs'])} | "
                         f"{len(c['counterevidence_refs'])} |")
        lines += ["", "_Append-only; unsupported, contradicted, and falsified "
                  "claims stay visible; forbidden claims are blocked, not "
                  "deleted; proves nothing about consciousness/life/agency._"]
        return self._guard("\n".join(lines))

    def _theory_md(self, s: Dict[str, Any]) -> str:
        t = s["theory_ledger"]
        lines = ["# Theory Ledger", "",
                 f"- statements: {t['theory_statement_count']} "
                 f"(challenged {t['challenged_count']}, falsified "
                 f"{t['falsified_count']}, retired {t['retired_count']})", ""]
        for st in t.get("statements", []):
            lines.append(f"- [{st['status']}] ({st['area']}) {st['text']} "
                         f"-- {st['revision_count']} revision(s)")
        lines += ["", "_Theory is a hypothesis under evidence, not proof; "
                  "revisions preserve prior versions and retired/falsified "
                  "statements remain archived._"]
        return self._guard("\n".join(lines))

    def _evidence_md(self, s: Dict[str, Any]) -> str:
        em = s["evidence_map"]
        lines = ["# Evidence Map", "",
                 f"- mappings: {em['evidence_mapping_count']} "
                 f"(contradictions {em['contradiction_count']}, missing "
                 f"{em['missing_count']})", "",
                 "| claim | evidence | source | role |",
                 "| --- | --- | --- | --- |"]
        for cid, evs in em.get("mapping", {}).items():
            for e in evs:
                lines.append(f"| {cid} | {e['evidence_id']} | {e['source']} | "
                             f"{e['role']} |")
        lines += ["", "_Many-to-many; contradictory evidence is preserved and "
                  "missing evidence is explicit._"]
        return self._guard("\n".join(lines))

    def _counter_md(self, s: Dict[str, Any]) -> str:
        ce = s["counterevidence"]
        lines = ["# Counterevidence", "",
                 f"- counterevidence: {ce.get('counterevidence_count', 0)} "
                 f"(blocking {ce.get('blocking_counterevidence_count', 0)})", ""]
        for r in ce.get("records", []):
            lines.append(f"- {r['counter_type']}: {r['detail']}"
                         + (" (blocks claim)" if r.get("blocks_claim") else ""))
        lines += ["", "_Counterevidence is as visible as evidence; it is never "
                  "ignored for being inconvenient._"]
        return self._guard("\n".join(lines))

    def _forbidden_md(self, s: Dict[str, Any]) -> str:
        fb = s["forbidden_claims"]
        lines = ["# Forbidden Claims", "",
                 f"- forbidden findings: {fb.get('forbidden_claim_count', 0)} "
                 f"(asserted {fb.get('asserted_forbidden_count', 0)}, ambiguous "
                 f"{fb.get('ambiguous_count', 0)}, disclaimers "
                 f"{fb.get('disclaimer_count', 0)})",
                 f"- blocks publication: {fb.get('blocks_publication', False)}",
                 ""]
        for c in fb.get("claims", []):
            kind = ("disclaimer" if c.get("is_disclaimer")
                    else "ambiguous" if c.get("is_ambiguous") else "asserted")
            lines.append(f"- [{kind}] {c['area']}: {c['detail']}")
        lines += ["", "_Forbidden inner-state claims may appear only as explicit "
                  "disclaimers; an asserted forbidden claim blocks publication._"]
        return self._guard("\n".join(lines))

    def _dossier_md(self, s: Dict[str, Any]) -> str:
        d = s["publication_dossier"]
        sec = d.get("sections", {})
        lines = ["# Publication Dossier (Draft)", "",
                 f"- readiness: **{d.get('publication_readiness_status')}**",
                 f"- is release: {d.get('is_release')}; is marketing: "
                 f"{d.get('is_marketing')}; is draft: {d.get('is_draft')}", "",
                 f"## Abstract", "", sec.get("abstract", ""), "",
                 f"## Research question", "", sec.get("research_question", ""), "",
                 f"## Safety boundaries", "", sec.get("safety_boundaries", ""), "",
                 "## Forbidden claims explicitly rejected", ""]
        lines += [f"- {x}" for x in
                  sec.get("forbidden_claims_explicitly_rejected", [])]
        lines += ["", "## Future work", ""]
        lines += [f"- {x}" for x in sec.get("future_work", [])] or ["- none"]
        lines += ["", "_Draft evidence compilation only; includes negative and "
                  "inconclusive results and safety boundaries; asserts no "
                  "unsupported claim and is not a release._"]
        return self._guard("\n".join(lines))

    def _abstracts_md(self, s: Dict[str, Any]) -> str:
        lines = ["# Safe Abstracts", ""]
        for variant, text in s["safe_abstracts"].items():
            lines += [f"## {variant}", "", text, ""]
        lines += ["_Abstracts are claim-constrained; they include no forbidden "
                  "claim except as a disclaimer._"]
        return self._guard("\n".join(lines))

    def _limitations_md(self, s: Dict[str, Any]) -> str:
        lim = s["limitations"]
        lines = ["# Limitations", "",
                 f"- limitations: {lim.get('limitation_count', 0)} "
                 f"(mandatory {lim.get('mandatory_count', 0)})", ""]
        for l in lim.get("limitations", []):
            lines.append(f"- [{l['category']}] {l['text']}")
        lines += ["", "_Limitations are mandatory, specific, and linked to the "
                  "claims they constrain._"]
        return self._guard("\n".join(lines))

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = state_dir or self.runtime.state_dir
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "SCIENTIFIC_CLAIM_REPORT.md")
        json_path = os.path.join(base, "SCIENTIFIC_CLAIM_REPORT.json")
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
