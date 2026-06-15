"""Daily evidence packet: generated, negatives included, ClaimGuard-scanned."""

from __future__ import annotations

from solaris_ai_nn.developmental_soak import DailyEvidencePacketBuilder


def _statuses():
    return {
        "plural_sensorium": {"event_count": 30, "active_modalities": 2},
        "perceptual_ontogenesis": {"stable_concept_count": 3,
                                   "contamination_warning_count": 1},
        "semiogenesis": {"sign_count": 4, "useful_sign_count": 2},
        "action_reaction": {"reaction_count": 2, "habit_candidate_count": 1},
    }


def test_packet_generated():
    builder = DailyEvidencePacketBuilder()
    packet = builder.build(run_day=1, active_phase="developmental_soak_30d",
                           statuses=_statuses(),
                           dev_status={"regression_count": 1,
                                       "plateau_count": 2,
                                       "structural_growth_status": "inconclusive"})
    assert packet.run_day == 1
    assert packet.operator_summary


def test_negative_result_included():
    builder = DailyEvidencePacketBuilder()
    packet = builder.build(run_day=2, active_phase="trial_24h",
                           statuses=_statuses(),
                           dev_status={"regression_count": 3,
                                       "plateau_count": 1})
    d = packet.to_dict()
    # Negative results (regressions/plateaus/contamination) are present.
    assert d["regressions"] == 3
    assert d["plateaus"] == 1
    assert d["contamination_warnings"] == 1
    assert d["growth_vs_accumulation_early_signal"] == "inconclusive"


def test_inconclusive_included():
    builder = DailyEvidencePacketBuilder()
    packet = builder.build(run_day=3, active_phase="trial_24h", statuses={},
                           dev_status={})
    assert packet.growth_vs_accumulation_early_signal == "inconclusive"


def test_claim_guard_scans_packet():
    builder = DailyEvidencePacketBuilder()
    packet = builder.build(run_day=1, active_phase="dry_run_2h",
                           statuses=_statuses(), dev_status={})
    assert packet.claim_guard_safe is True
    assert any("not proof" in lim.lower() or "does not prove" in lim.lower()
               for lim in packet.limitations)
