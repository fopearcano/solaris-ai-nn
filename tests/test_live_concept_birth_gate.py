"""Live concept birth gate: born, defer, contaminated/overload/operator blocks."""

from __future__ import annotations

from solaris_ai_nn.live_ontogenesis import (
    LiveConceptBirthGate,
    LiveOntogenesisContaminationFilter,
    LiveProtoConceptCandidate,
)


def _cand(cid, sources, recurrence, counter=0):
    c = LiveProtoConceptCandidate(candidate_id=cid, feature_signature="s")
    c.source_distribution = dict(sources)
    c.recurrence_count = recurrence
    for i in range(recurrence):
        src = next(iter(sources))
        c.add_support(f"{cid}_e{i}", src, "")
    for i in range(counter):
        c.add_counter(f"{cid}_x{i}", next(iter(sources)), "divergent")
    return c


def _clean_contamination(cid):
    c = LiveProtoConceptCandidate(candidate_id=cid, feature_signature="s")
    return LiveOntogenesisContaminationFilter().evaluate(
        candidate=c, vectors_by_event={}, source_diet={})


def _gate(allow_birth=True):
    return LiveConceptBirthGate(min_recurrence=3, min_stability=0.6,
                                allow_birth=allow_birth)


_OK = dict(governance_passed=True, birth_certificate_present=True,
           observation_stability_blocked=False, source_diet={}, load={})


def test_born_case():
    c = _cand("b", {"machine_body": 5}, 5)
    r = _gate(allow_birth=True).evaluate(
        candidate=c, stability_score=0.75,
        contamination=_clean_contamination("b"), **_OK)
    assert r.status == "born"
    assert r.born is True


def test_defer_case_low_recurrence():
    c = _cand("d", {"machine_body": 1}, 1)
    r = _gate().evaluate(candidate=c, stability_score=0.75,
                         contamination=_clean_contamination("d"), **_OK)
    assert r.status == "defer"


def test_contaminated_block():
    c = _cand("ct", {"operator_pulse": 5}, 5)
    contamination = LiveOntogenesisContaminationFilter().evaluate(
        candidate=c, vectors_by_event={}, source_diet={})
    r = _gate().evaluate(candidate=c, stability_score=0.75,
                         contamination=contamination, **_OK)
    assert r.status == "blocked_by_operator_dominance"
    assert r.blocked is True


def test_overload_block():
    c = _cand("o", {"machine_body": 5}, 5)
    opts = dict(_OK); opts["load"] = {"severe_overload": True}
    r = _gate().evaluate(candidate=c, stability_score=0.75,
                         contamination=_clean_contamination("o"), **opts)
    assert r.status == "blocked_by_overload"


def test_deprivation_block():
    c = _cand("dp", {"machine_body": 5}, 5)
    opts = dict(_OK); opts["load"] = {"severe_deprivation": True}
    r = _gate().evaluate(candidate=c, stability_score=0.75,
                         contamination=_clean_contamination("dp"), **opts)
    assert r.status == "blocked_by_deprivation"


def test_operator_text_dominance_block_via_source_diet():
    c = _cand("od", {"machine_body": 5}, 5)
    opts = dict(_OK); opts["source_diet"] = {"balance": "operator_pulse_dominant"}
    r = _gate().evaluate(candidate=c, stability_score=0.75,
                         contamination=_clean_contamination("od"), **opts)
    assert r.status == "blocked_by_source_diet"


def test_candidate_only_profile_withholds_birth():
    c = _cand("s", {"machine_body": 5}, 5)
    r = _gate(allow_birth=False).evaluate(
        candidate=c, stability_score=0.75,
        contamination=_clean_contamination("s"), **_OK)
    assert r.status == "stable_candidate"
    assert r.born is False
