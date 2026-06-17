# Tester Release Candidate

The Tester Release Candidate (RC) assembly (Prompt 80) is the first local, controlled
trusted-tester build of Solaris-AI-NN. It is assembled **after** the tester packaging
doctor and the tester safety freeze pass.

## What the RC is

A local assembly step that collects, into one place, everything a trusted tester needs:
the install guide, quickstart, runbook, release notes, known issues, safety boundaries,
claim freeze, red-team checklist, release blocker report, fixture demo instructions,
live-read-only instructions, external feeder policy, feedback forms, console
instructions, an artifact manifest, a final RC checklist, a readiness report, and a local
tester bundle.

## What the RC is not

- not a public release, not a product release, and not a consciousness demo
- no live actuation, no hardware control, no feeder control
- no network/shell/Git/GitHub/browser/OS access by the Solaris runtime
- tester feedback is not training and is not ground truth
- external feeders are manual and run by the operator, never by Solaris
- the fixture demo comes first; live-read-only is optional and governance-gated
- the environmental membrane is required before any downstream live learning
- raw events are audit material, not perception; sensory impressions are operational
  boundary records, not subjective experience

## How it is assembled

```bash
python -m solaris_ai_nn tester-rc --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-rc-manifest --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-rc-readiness --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-rc-docs --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-rc-bundle --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-rc-checklist --tester-state-dir .solaris_ai_nn_tester
```

The RC readiness gate blocks on packaging, safety-freeze, membrane, and fixture failures.
Open release blockers prevent the RC; critical safety blockers cannot be silently waived.
The RC bundle is local and is shared manually only if a tester requests it -- nothing is
uploaded automatically.

_This document describes a local assembly step only. It makes no claim of consciousness,
sentience, biological life, personhood, agency, free will, emotion, feeling,
understanding, self-awareness, autonomous self-improvement, or subjective experience._
