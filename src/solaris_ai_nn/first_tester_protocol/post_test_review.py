"""First tester post-test review -- a QA-only review template.

:class:`FirstTesterPostTestReview` generates the post-test review template the tester
fills in after the session. The review is QA evidence only: it is not training, not ground
truth, and it never modifies Solaris automatically.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PostTestReviewQuestion:
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text}


def _default_questions() -> List[PostTestReviewQuestion]:
    Q = PostTestReviewQuestion
    return [Q(t) for t in (
        "Did install work?",
        "Did doctor output make sense?",
        "Did the fixture demo complete?",
        "Were the reports understandable?",
        "Did the console help?",
        "Were blockers visible?",
        "Were the safety boundaries clear?",
        "Was the membrane concept understandable?",
        "Was quarantine understandable?",
        "Was the live-read-only setup clear?",
        "Did any command feel unsafe?",
        "Did any report overclaim (consciousness/life/agency/understanding)?",
        "Did any step require developer explanation?",
        "What was the first confusing moment?",
        "What would block a second tester?",
        "What artifacts are attached?",
        "Any privacy concerns?")]


@dataclass
class PostTestReviewSummary:
    """A small structured summary the developer can fill from the review."""

    install_ok: bool = False
    reports_understandable: bool = False
    any_overclaim: bool = False
    any_unsafe_command: bool = False
    first_confusing_moment: str = ""
    blocks_second_tester: str = ""
    privacy_concerns: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "install_ok": self.install_ok,
            "reports_understandable": self.reports_understandable,
            "any_overclaim": self.any_overclaim,
            "any_unsafe_command": self.any_unsafe_command,
            "first_confusing_moment": self.first_confusing_moment,
            "blocks_second_tester": self.blocks_second_tester,
            "privacy_concerns": self.privacy_concerns,
            "is_training": False, "is_ground_truth": False,
            "modifies_solaris": False,
        }


@dataclass
class FirstTesterPostTestReview:
    """Builds the post-test review template."""

    questions: List[PostTestReviewQuestion] = field(
        default_factory=_default_questions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_count": len(self.questions),
            "questions": [q.to_dict() for q in self.questions],
            "is_training": False, "is_ground_truth": False,
            "modifies_solaris": False, "local_only": True,
            "note": "QA-only post-test review; it is not training, not ground "
                    "truth, and never modifies Solaris automatically",
        }

    def build_text(self) -> str:
        lines = ["# First Tester Post-Test Review Template", "",
                 "Fill this in after the session. This review is **QA evidence "
                 "only**: it is not training, it is not ground truth, and it "
                 "does not modify Solaris automatically.", ""]
        for q in self.questions:
            lines += [f"### {q.text}", "", "> _your answer here_", ""]
        lines += ["_QA-only post-test review. Tester feedback is not training "
                  "and is never treated as ground truth; it cannot modify "
                  "Solaris behavior automatically. No claim of consciousness/"
                  "life/agency is made._"]
        return "\n".join(lines)

    def write(self, reports_dir: str) -> str:
        os.makedirs(reports_dir, exist_ok=True)
        path = os.path.join(reports_dir,
                            "FIRST_TESTER_POST_TEST_REVIEW_TEMPLATE.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.build_text())
        return path
