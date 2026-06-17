# Tester Safety Boundaries

This document states the safety boundaries for the first trusted tester release of
Solaris-AI-NN. The first tester release is **local and controlled**.

- This is **not** a public release; there are **no** public claims.
- The system makes **no** claim of consciousness, sentience, biological life,
  personhood, agency, free will, emotion, feeling, understanding, self-awareness,
  autonomous self-improvement, autonomous intent, autonomous desire, subjective
  experience, or real-world autonomy.
- There is **no** live actuation and **no** hardware control.
- Solaris does **not** start, stop, schedule, or control feeders.
- The Solaris runtime does **not** access the network, shell, Git/GitHub, browser, or
  OS APIs.
- Tester feedback is **not** training, **not** RLHF, and **not** ground truth.
- External feeders are **manual**: dumb external scripts or files the tester runs.
- The Environmental Membrane is **required** before any downstream live learning.
- Raw events are **audit material, not perception**.
- Sensory impressions are **operational boundary records, not subjective experience**.

The Tester Safety Freeze (`tester-safety-freeze`) is the local release gate that checks
these boundaries before a tester release candidate. It is report/gate-only and does not
prove the system safe in general.
