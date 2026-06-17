# Tester live-read-only examples (Prompt 75)

This directory holds the example assets for the **tester live-read-only** path — the
safe bridge from the fixture-only tester demo (Prompt 74) to trusted live-read-only
testing.

> **Architectural rule:** Solaris does not run feeders. Feeders are dumb external
> scripts or manual files created by the tester/operator. Solaris validates the JSONL
> events that appear in `.solaris_ai_nn_live/inbox/` and the Environmental Membrane
> turns accepted events into sensory impressions. Solaris never starts, stops,
> schedules, controls, or edits a feeder.

## Contents

- `LIVE_READONLY_GOVERNANCE.tester.template.json` — a **SAFE-OFF** governance template.
  It ships with `live_readonly_enabled=false` and `operator_approved=false`. The tester
  must enable and approve it **by hand**. Do not approve a source you do not understand.
- `FEEDER_REGISTRY.tester.template.json` — descriptive feeder metadata. Every feeder is
  external, read-only, operator-started, and never controlled by Solaris.
- `sample_safe_events/live_safe_events.jsonl` — events that should be **accepted**.
- `sample_unsafe_events/live_unsafe_events.jsonl` — events that should be
  **quarantined** (read_only=false, is_command=true, secrets, forbidden sources, …).
- `sample_mixed_events/live_mixed_events.jsonl` — a mix that should **partially** accept
  and **partially** quarantine.

## Try it

```bash
python -m solaris_ai_nn tester-live-init --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester/live
# Then edit .solaris_ai_nn_live/governance/LIVE_READONLY_GOVERNANCE.json by hand:
#   set "live_readonly_enabled": true and "operator_approved": true
python -m solaris_ai_nn tester-live-doctor --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester/live
python -m solaris_ai_nn tester-live-samples --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester/live
# Manually run external feeders (Solaris never runs them):
python tools/external_feeders/chronos_absence_feeder.py --out .solaris_ai_nn_live/inbox/chronos_absence.jsonl
python -m solaris_ai_nn tester-live-run --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester/live --run-birth --run-membrane --run-integration --run-observation
python -m solaris_ai_nn tester-live-bundle --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester/live
```

A successful live-read-only run is operational evidence; it is **not** evidence of
consciousness, sentience, biological life, personhood, agency, free will, emotion,
feeling, understanding, self-awareness, autonomous self-improvement, or subjective
experience.
