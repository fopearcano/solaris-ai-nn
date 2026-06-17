"""Live sign birth gate: born, defer, low-utility/label/contaminated blocks."""

from __future__ import annotations

from solaris_ai_nn.live_semiogenesis import (
    LiveSignBirthGate,
    LiveSignCandidate,
    LiveSignContaminationFilter,
)


def _cand(sid, sources, counter=0):
    c = LiveSignCandidate(sign_id=sid, private_token=f"sig_live_{sid}",
                          linked_concept_ids=["c"],
                          feature_signature_refs=["sig:c"])
    c.source_distribution = dict(sources)
    c.add_support("c", kind="concept")
    for i in range(counter):
        c.add_counter(f"x{i}", reason="divergent")
    return c


def _clean(sid):
    return LiveSignContaminationFilter().evaluate(candidate=_cand(sid,
                                                                  {"m": 5}))


def _gate(allow_birth=True):
    return LiveSignBirthGate(min_utility=0.6, allow_birth=allow_birth)


_OK = dict(governance_passed=True, birth_certificate_present=True,
           observation_stability_blocked=False, ontogenesis_report_present=True,
           linked_concept_eligible=True, linked_concept_contaminated=False,
           load={})


def test_born_case():
    c = _cand("b", {"machine_body": 5})
    r = _gate(True).evaluate(candidate=c, utility_score=0.75,
                             contamination=_clean("b"), **_OK)
    assert r.status == "born"
    assert r.born is True


def test_defer_case_counterevidence():
    c = _cand("d", {"machine_body": 5}, counter=3)
    r = _gate(True).evaluate(candidate=c, utility_score=0.75,
                             contamination=_clean("d"), **_OK)
    assert r.status == "defer"


def test_low_utility_block():
    c = _cand("u", {"machine_body": 5})
    r = _gate(True).evaluate(candidate=c, utility_score=0.2,
                             contamination=_clean("u"), **_OK)
    assert r.status == "blocked_by_low_utility"


def test_label_dependence_block():
    c = _cand("l", {"machine_body": 5})
    c.contamination_findings = ["human_label_copy"]
    contamination = LiveSignContaminationFilter().evaluate(candidate=c)
    r = _gate(True).evaluate(candidate=c, utility_score=0.75,
                             contamination=contamination, **_OK)
    assert r.status == "blocked_by_label_dependence"


def test_contaminated_concept_block():
    c = _cand("cc", {"machine_body": 5})
    opts = dict(_OK); opts["linked_concept_contaminated"] = True
    r = _gate(True).evaluate(candidate=c, utility_score=0.75,
                             contamination=_clean("cc"), **opts)
    assert r.status == "contaminated"


def test_candidate_only_profile_withholds_birth():
    c = _cand("s", {"machine_body": 5})
    r = _gate(allow_birth=False).evaluate(candidate=c, utility_score=0.75,
                                          contamination=_clean("s"), **_OK)
    assert r.status == "stable_candidate"
    assert r.born is False
