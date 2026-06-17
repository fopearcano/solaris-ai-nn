"""Live anticipation engine: rhythm/absence generated; operator-only blocked."""

from __future__ import annotations

from solaris_ai_nn.live_cognition import LiveAnticipationEngine, SignInputLoader


def _signs(records):
    return SignInputLoader().from_records(records, synthetic=True).signs


def _rec(sid, sources, concepts, supporting=None):
    return {"sign_id": sid, "private_token": f"sig_live_{sid}", "status": "born",
            "linked_concept_ids": concepts, "utility_score": 0.7,
            "source_distribution": sources,
            "supporting_refs": supporting or concepts,
            "contradicting_refs": [], "contamination_findings": []}


_RHYTHM = {"patterns": [{"source_id": "machine_body", "kind": "periodic"}]}


def test_rhythm_anticipation_generated():
    signs = _signs([_rec("s1", {"machine_body": 6}, ["c_machine_body"])])
    ants = LiveAnticipationEngine().anticipate(signs=signs, rhythm=_RHYTHM)
    assert any(a.anticipation_type == "rhythm_continuation" for a in ants)


def test_absence_anticipation_generated():
    signs = _signs([_rec("s1", {"chronos_absence": 5}, ["c_absence"],
                         supporting=["chronos_absence:chronos:absence"])])
    ants = LiveAnticipationEngine().anticipate(signs=signs)
    assert any(a.anticipation_type == "source_silence_likely_continues"
               for a in ants)


def test_operator_text_only_anticipation_blocked():
    signs = _signs([_rec("s1", {"operator_pulse": 5}, ["c_op"])])
    ants = LiveAnticipationEngine().anticipate(signs=signs)
    assert ants
    assert all(a.status == "contaminated" for a in ants)
    assert all("operator_pulse_dominance" in a.contamination_findings
               for a in ants)


def test_uncertainty_included():
    signs = _signs([_rec("s1", {"machine_body": 6}, ["c_machine_body"])])
    ants = LiveAnticipationEngine().anticipate(signs=signs, rhythm=_RHYTHM)
    assert all(a.uncertainty > 0 for a in ants)
