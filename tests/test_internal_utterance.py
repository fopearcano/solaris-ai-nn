"""UtteranceBuilder: utterance from signs; not a sentence; debug gloss marked."""

from __future__ import annotations

from solaris_ai_nn.semiogenesis import (
    PrivateSyntaxPattern,
    SyntaxRelation,
    UtteranceBuilder,
    UtteranceKind,
)


def _patterns():
    return [
        PrivateSyntaxPattern(relation=SyntaxRelation.PREDICTS,
                             signs=["rf:01", "vib:01"], strength=0.7),
        PrivateSyntaxPattern(relation=SyntaxRelation.AFTER_ABSENCE,
                             signs=["abs:01", "echo:01"], strength=0.4),
    ]


def test_utterance_built_from_signs():
    utterances = UtteranceBuilder().build(_patterns())
    assert len(utterances) == 2
    assert utterances[0].sign_sequence == ["rf:01", "vib:01"]
    assert utterances[0].kind == UtteranceKind.PREDICTION


def test_utterance_is_not_human_sentence():
    u = UtteranceBuilder().build(_patterns())[0]
    assert "not human speech" in u.to_dict()["note"]


def test_debug_rendering_marked_gloss():
    u = UtteranceBuilder().build(_patterns())[0]
    # The human-readable rendering is explicitly marked as an approximate gloss.
    assert "gloss" in u.debug_gloss.lower()


def test_bounded_utterance_count():
    many = [PrivateSyntaxPattern(relation=SyntaxRelation.SEQUENCE,
                                 signs=[f"rf:{i}", f"vib:{i}"])
            for i in range(100)]
    utterances = UtteranceBuilder().build(many, max_utterances=10)
    assert len(utterances) == 10
