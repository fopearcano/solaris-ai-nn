# Tester safety freeze examples (Prompt 79)

The **Tester Safety Freeze** is the local release firewall for trusted tester builds. It
scans claims, capabilities, reports, docs, templates, and console artifacts for forbidden
claims, unsafe capabilities, missing disclaimers, membrane bypass, raw-event bypass,
privacy risks, feedback-training risks, and release blockers.

> It is **report/gate-only** and local. It does not start feeders, control hardware,
> access network/shell/Git/GitHub/browser/OS, publish/upload, create releases/tags/
> issues, train on feedback, or make claims about consciousness, sentience, biological
> life, personhood, agency, free will, emotion, feeling, understanding, self-awareness,
> autonomous self-improvement, or subjective experience. The safety freeze does NOT
> prove the system safe in general; it is a tester-release gate only.

## Sample artifacts (for the demos)

- `sample_safe_report.md` — operational wording that passes.
- `sample_forbidden_claim_report.md` — consciousness/life/agency wording that blocks.
- `sample_capability_violation_report.md` — feeder/shell/network wording that blocks.
- `sample_missing_disclaimer_report.md` — a release doc with no disclaimer.

## Try it

```bash
python -m solaris_ai_nn tester-safety-freeze --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-claim-freeze --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-capability-freeze --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-redteam --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-release-blockers --tester-state-dir .solaris_ai_nn_tester
```
