"""CognitiveMove: serializes; evidence preserved; no external action."""

from __future__ import annotations

from solaris_ai_nn.sensorium_cognition import CognitiveMove, CognitiveMoveType


def test_move_serializes():
    mv = CognitiveMove(move_type=CognitiveMoveType.PREDICT_NEXT_SIGN,
                       input_sign_refs=["SIGN_1"], evidence_refs=["e1"])
    d = mv.to_dict()
    assert d["move_type"] == CognitiveMoveType.PREDICT_NEXT_SIGN
    assert d["input_sign_refs"] == ["SIGN_1"]
    assert "internal-only" in d["note"]


def test_evidence_refs_preserved():
    mv = CognitiveMove(move_type=CognitiveMoveType.TEST_RELATION,
                       evidence_refs=["inv:1", "pat:2"])
    assert mv.evidence_refs == ["inv:1", "pat:2"]


def test_external_action_impossible():
    mv = CognitiveMove(move_type=CognitiveMoveType.SELECT_ATTENTION_TARGET)
    # No attribute or method permits external action; only internal attention.
    assert not hasattr(mv, "actuate")
    assert not hasattr(mv, "execute_external")
    assert any("cannot act on the external world" in lim
               for lim in mv.limitations)
    assert mv.recommends_attention is True


def test_all_move_types_known():
    assert len(CognitiveMoveType.ALL) == 14
    mv = CognitiveMove(move_type=CognitiveMoveType.MARK_UNKNOWN)
    assert mv.move_type in CognitiveMoveType.ALL
