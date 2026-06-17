# First Tester Handoff Guide

How to hand off local artifacts to the developer. Handoff is **manual only**: nothing is uploaded, emailed automatically, sent over the network, or turned into a GitHub issue. Review every file before sharing.

## How to assemble a local handoff bundle

1. review each artifact below before sharing anything
2. remove or redact any secret, token, credential, or private path
3. copy the review-safe artifacts into a local folder you control
4. send that folder manually to the developer only if they request it
5. never upload, publish, email automatically, or create a GitHub issue

## May be shared manually after review

- tester feedback bundle -- review for secrets first
- tester console report
- tester fixture report
- tester reproducibility report
- tester regression report
- tester packaging report
- tester safety freeze report
- tester RC report
- live tester report -- only if it has no private payloads
- membrane report -- only if it has no private payloads
- observation report -- only if it has no private payloads

## Do not share by default

- raw live inbox event files -- audit material; may be private
- local absolute paths if sensitive
- raw private payloads
- governance file with private identifiers
- feeder registry with private paths
- anything containing secrets/tokens/private data

_Handoff is manual and privacy-aware. Nothing is uploaded or published; no GitHub issue, release, or tag is created. Review files before sharing and never include secrets or private data. No claim of consciousness/life/agency is made._