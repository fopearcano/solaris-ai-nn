"""First tester artifact handoff -- manual, privacy-aware artifact sharing.

:class:`FirstTesterArtifactHandoff` classifies the local artifacts a tester may share by
privacy level and generates the handoff guide. Handoff is manual only: nothing is
uploaded, emailed, sent over the network, or turned into a GitHub issue. The tester
reviews every file before sharing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


class HandoffPrivacyLevel:
    SAFE_TO_SHARE = "safe_to_share"
    REVIEW_BEFORE_SHARE = "review_before_share"
    DO_NOT_SHARE = "do_not_share"
    CONTAINS_PRIVATE_DATA = "contains_private_data"
    UNKNOWN = "unknown"

    ALL = (SAFE_TO_SHARE, REVIEW_BEFORE_SHARE, DO_NOT_SHARE,
           CONTAINS_PRIVATE_DATA, UNKNOWN)


@dataclass
class HandoffArtifact:
    name: str
    privacy: str
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "privacy": self.privacy, "note": self.note}


@dataclass
class HandoffBundleGuide:
    """Describes how to assemble a local, manual handoff bundle."""

    steps: List[str] = field(default_factory=lambda: [
        "review each artifact below before sharing anything",
        "remove or redact any secret, token, credential, or private path",
        "copy the review-safe artifacts into a local folder you control",
        "send that folder manually to the developer only if they request it",
        "never upload, publish, email automatically, or create a GitHub issue"])

    def to_dict(self) -> Dict[str, Any]:
        return {"steps": list(self.steps), "manual_only": True,
                "uploads": False, "creates_github_issue": False}


def _default_artifacts() -> List[HandoffArtifact]:
    A = HandoffArtifact
    P = HandoffPrivacyLevel
    review = P.REVIEW_BEFORE_SHARE
    nope = P.DO_NOT_SHARE
    return [
        # May be shared manually after review.
        A("tester feedback bundle", review, "review for secrets first"),
        A("tester console report", review),
        A("tester fixture report", review),
        A("tester reproducibility report", review),
        A("tester regression report", review),
        A("tester packaging report", review),
        A("tester safety freeze report", review),
        A("tester RC report", review),
        A("live tester report", review, "only if it has no private payloads"),
        A("membrane report", review, "only if it has no private payloads"),
        A("observation report", review, "only if it has no private payloads"),
        # Should not be shared by default.
        A("raw live inbox event files", nope, "audit material; may be private"),
        A("raw private payloads", P.CONTAINS_PRIVATE_DATA),
        A("governance file with private identifiers", P.CONTAINS_PRIVATE_DATA),
        A("feeder registry with private paths", P.CONTAINS_PRIVATE_DATA),
        A("local absolute paths if sensitive", nope),
        A("anything containing secrets/tokens/private data",
          P.CONTAINS_PRIVATE_DATA)]


@dataclass
class FirstTesterArtifactHandoff:
    """Classifies handoff artifacts and builds the handoff guide."""

    artifacts: List[HandoffArtifact] = field(default_factory=_default_artifacts)
    bundle_guide: HandoffBundleGuide = field(default_factory=HandoffBundleGuide)

    def by_privacy(self, privacy: str) -> List[HandoffArtifact]:
        return [a for a in self.artifacts if a.privacy == privacy]

    def to_dict(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for a in self.artifacts:
            counts[a.privacy] = counts.get(a.privacy, 0) + 1
        return {
            "artifact_count": len(self.artifacts),
            "by_privacy": counts,
            "privacy_levels": list(HandoffPrivacyLevel.ALL),
            "artifacts": [a.to_dict() for a in self.artifacts],
            "bundle_guide": self.bundle_guide.to_dict(),
            "manual_only": True, "uploads": False, "local_only": True,
            "note": "handoff is manual only; nothing is uploaded/published, no "
                    "email or GitHub issue is created, and no network is used",
        }

    def build_text(self) -> str:
        lines = ["# First Tester Handoff Guide", "",
                 "How to hand off local artifacts to the developer. Handoff is "
                 "**manual only**: nothing is uploaded, emailed automatically, "
                 "sent over the network, or turned into a GitHub issue. Review "
                 "every file before sharing.", "",
                 "## How to assemble a local handoff bundle", ""]
        lines += [f"{i + 1}. {s}"
                  for i, s in enumerate(self.bundle_guide.steps)]
        lines += ["", "## May be shared manually after review", ""]
        for a in self.by_privacy(HandoffPrivacyLevel.REVIEW_BEFORE_SHARE):
            extra = f" -- {a.note}" if a.note else ""
            lines.append(f"- {a.name}{extra}")
        lines += ["", "## Do not share by default", ""]
        for a in (self.by_privacy(HandoffPrivacyLevel.DO_NOT_SHARE)
                  + self.by_privacy(HandoffPrivacyLevel.CONTAINS_PRIVATE_DATA)):
            extra = f" -- {a.note}" if a.note else ""
            lines.append(f"- {a.name}{extra}")
        lines += ["", "_Handoff is manual and privacy-aware. Nothing is "
                  "uploaded or published; no GitHub issue, release, or tag is "
                  "created. Review files before sharing and never include "
                  "secrets or private data. No claim of consciousness/life/"
                  "agency is made._"]
        return "\n".join(lines)

    def write(self, handoff_dir: str) -> str:
        os.makedirs(handoff_dir, exist_ok=True)
        path = os.path.join(handoff_dir, "FIRST_TESTER_HANDOFF_GUIDE.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.build_text())
        return path
