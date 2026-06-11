"""Tests for the ego language queries."""

from __future__ import annotations

from solaris_ai_nn.ego.self_model import SelfModel
from solaris_ai_nn.ego.self_report import EgoQueryInterface
from solaris_ai_nn.governance.compliance import ClaimGuard


def _queries(tmp_path, context=None):
    model = SelfModel(state_dir=tmp_path)
    model.update(dict({"run_id": "r1", "session_id": "s1",
                       "health_level": "ok"}, **(context or {})))
    return model, EgoQueryInterface(model)


def test_current_perspective_query_grounded(tmp_path):
    _, queries = _queries(tmp_path, {"latent_mode": "replay"})
    result = queries.answer("what is the current perspective?")
    assert result.answered
    assert "The current perspective is 'latent_offline_replay'" \
        in result.text
    assert "recorded operating mode" in result.text


def test_internal_external_query_grounded(tmp_path):
    _, queries = _queries(tmp_path)
    result = queries.answer(
        "is this event internal or external?",
        event={"source": "stream", "kind": "stream_line"})
    assert result.answered
    assert "The self-model classifies the event as 'external'" \
        in result.text
    assert "observed_from_stream" in result.text


def test_evidence_query_grounded(tmp_path):
    _, queries = _queries(tmp_path)
    result = queries.answer(
        "was this evidence observed or simulated?",
        event={"source": "offline_replay", "kind": "replay_trace"})
    assert result.answered
    assert "'simulated'" in result.text


def test_continuity_and_authority_queries(tmp_path):
    model, queries = _queries(tmp_path)
    continuity = queries.answer("what is the identity continuity score?")
    assert "identity continuity score is 1.00" in continuity.text
    assert "runtime continuity" in continuity.text
    authority = queries.answer("what action authority exists?")
    assert "structurally forbidden" in authority.text
    # With a mismatch, the explanation names the reason.
    model.identity.update({"run_id": "r1"})
    model.identity.update({"run_id": "r2"})
    uncertain = queries.answer("what is the identity continuity score?")
    assert "uncertain because" in uncertain.text


def test_all_eight_queries_supported_and_safe(tmp_path):
    _, queries = _queries(tmp_path)
    assert len(queries.supported_queries()) == 8
    guard = ClaimGuard()
    for question in queries.supported_queries():
        answer = queries.answer(question)
        assert guard.is_safe(answer.text), question
        lowered = answer.text.lower()
        # Affirmative claims are forbidden; explicit denials ("no
        # consciousness ... claim is made") are the point of the layer.
        for forbidden in ("is conscious", "i am conscious", "has a soul",
                          "is sentient", "i want", "i am alive",
                          "is a person"):
            assert forbidden not in lowered, (question, forbidden)


def test_counterfactual_query_and_unknown_fallback(tmp_path):
    _, queries = _queries(tmp_path)
    result = queries.answer(
        "why was this classified as counterfactual?",
        event={"source": "counterfactual", "kind": "dream_trace"})
    assert "never counting as real observation" in result.text \
        or "counterfactual boundary" in result.text
    unknown = queries.answer("does the self-model love itself?")
    assert not unknown.answered
    assert "does not know how to answer" in unknown.text
