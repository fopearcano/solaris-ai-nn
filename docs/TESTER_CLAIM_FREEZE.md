# Tester Claim Freeze

The claim freeze scans local tester-release text artifacts (README, docs, install
guides, console/fixture/live/membrane/observation/feedback/packaging reports) for
forbidden claims and missing disclaimers.

- Forbidden consciousness/life/agency/personhood/free-will/emotion/feeling/
  understanding/self-awareness/subjective-experience/autonomous claims are **release
  blockers**.
- Control/feedback-training/raw-event/membrane-bypass implications are **blockers**.
- Missing disclaimers in tester-release docs are **blockers**.

The freeze reads only local text and executes nothing. Replace metaphysical language
with operational language (see `ALLOWED_OPERATIONAL_LANGUAGE.md`). Describe optional
learning layers as operational records only. Run with:

```bash
python -m solaris_ai_nn tester-claim-freeze --tester-state-dir .solaris_ai_nn_tester
```

This is a tester-release gate only; it does not prove the system safe in general, and it
makes no claim of consciousness, life, or agency.
