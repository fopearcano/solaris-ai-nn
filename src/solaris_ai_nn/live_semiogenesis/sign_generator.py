"""Live private sign generator -- deterministic, opaque, evidence-preserving.

:class:`LivePrivateSignGenerator` mints a private internal token for each eligible
proto-concept. Tokens are deterministic opaque ids derived from the concept's feature
signature (e.g. ``sig_live_<hash>`` and a compact ``LSigma-<n>`` code). Tokens are
never copied from human labels, debug gloss, operator notes, command text, private
data, or secrets; a human-readable alias may exist only as a non-ground-truth debug
annotation. If a requested token is label-derived, the generated candidate is marked
contaminated / label-dependent.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .sign_candidate import LiveSignCandidate, SignCandidateStatus

_LABEL_DERIVED_MARKERS = ("label:", "gloss:", "operator:", "note:")
_SECRET_MARKERS = ("password", "secret", "api key", "api_key", "credential",
                   "token=", "private message")
_COMMAND_MARKERS = ("execute:", "run:", "sudo ", "rm -", "shell:", "command:")


@dataclass
class GeneratedSignToken:
    """A generated private sign token + its provenance."""

    private_token: str
    short_code: str
    derivation: str = "feature_shape"
    contaminated: bool = False
    contamination_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"private_token": self.private_token,
                "short_code": self.short_code, "derivation": self.derivation,
                "contaminated": self.contaminated,
                "contamination_reason": self.contamination_reason,
                "is_human_label": False, "is_ground_truth": False}


@dataclass
class SignGenerationResult:
    """The aggregate sign-generation result."""

    candidates: List[LiveSignCandidate] = field(default_factory=list)
    skipped_count: int = 0
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "live_sign_candidate_count": len(self.candidates),
            "skipped_count": self.skipped_count,
            "candidates": [c.to_dict() for c in self.candidates],
            "notes": list(self.notes),
            "note": "sign tokens are deterministic, opaque, and private; they "
                    "are never copied from human labels/gloss/operator text; a "
                    "debug alias is a non-ground-truth annotation only",
        }


@dataclass
class LivePrivateSignGenerator:
    """Generates private internal sign tokens for eligible proto-concepts."""

    counter_start: int = 1

    def generate_token(self, feature_signature: str) -> GeneratedSignToken:
        """Deterministic opaque token from a feature signature (no semantics)."""
        digest = hashlib.sha1(str(feature_signature).encode("utf-8")).hexdigest()
        n = int(digest[:6], 16) % 100000
        return GeneratedSignToken(
            private_token=f"sig_live_{digest[:12]}",
            short_code=f"LΣ-{n:05d}", derivation="feature_shape")

    def generate_for_concepts(self, concepts: List[Any], *,
                              max_signs: int = 200,
                              requested_tokens: Optional[Dict[str, str]] = None,
                              ) -> SignGenerationResult:
        result = SignGenerationResult()
        requested_tokens = requested_tokens or {}
        for i, concept in enumerate(concepts):
            if len(result.candidates) >= max_signs:
                result.notes.append("max signs reached; some concepts skipped")
                break
            cid = getattr(concept, "concept_id", "")
            signature = getattr(concept, "feature_signature", "")
            requested = requested_tokens.get(cid, "")
            token_obj = self.generate_token(signature or cid)
            cand = LiveSignCandidate(
                sign_id=f"live_sign_{i}_{token_obj.private_token[-6:]}",
                private_token=token_obj.private_token,
                linked_concept_ids=[cid],
                feature_signature_refs=[signature] if signature else [],
                source_distribution=dict(
                    getattr(concept, "source_distribution", {}) or {}),
                modality_distribution=dict(
                    getattr(concept, "modality_distribution", {}) or {}))
            cand.utility_evidence = {"short_code": token_obj.short_code,
                                     "derivation": token_obj.derivation}
            cand.add_support(cid, kind="concept",
                             detail=f"linked proto-concept {cid!r}")
            # A debug alias may be carried as a NON-ground-truth annotation.
            alias = self._debug_alias(concept)
            if alias:
                cand.debug_alias = alias
                cand.limitations.append(
                    "debug alias is annotation only, not sign identity")
            # If the operator *requested* a label-derived token, refuse identity
            # and mark contamination (the private token is still used as id).
            self._check_requested_token(cand, requested)
            result.candidates.append(cand)
        return result

    def _check_requested_token(self, cand: LiveSignCandidate,
                               requested: str) -> None:
        low = str(requested or "").lower()
        if not low:
            return
        if any(m in low for m in _SECRET_MARKERS):
            cand.contamination_findings.append("secret_marker")
            cand.status = SignCandidateStatus.CONTAMINATED
            cand.limitations.append(
                "requested token contained a secret marker; refused as identity")
        elif any(m in low for m in _COMMAND_MARKERS):
            cand.contamination_findings.append("command_like_text")
            cand.status = SignCandidateStatus.CONTAMINATED
        elif any(m in low for m in _LABEL_DERIVED_MARKERS) \
                or low.startswith("the ") or " " in low:
            cand.contamination_findings.append("human_label_copy")
            cand.status = SignCandidateStatus.LABEL_DEPENDENT
            cand.limitations.append(
                "requested token was label-derived; kept opaque internal token "
                "and marked label-dependent")

    @staticmethod
    def _debug_alias(concept: Any) -> str:
        annotations = getattr(concept, "annotations", {}) or {}
        gloss = annotations.get("debug_gloss", "")
        return str(gloss)[:80] if gloss else ""
