# Feeder Privacy and Safety Guide

This guide governs every external feeder, hardware blueprint, and simulated
feeder in the SDK. The core boundary: **a feeder is an artificial sensory organ
outside Solaris; Solaris reads its event envelopes read-only and controls
nothing.**

## The safety boundary

- Solaris does **not** start, stop, configure, or command any feeder.
- Solaris controls **no** hardware: no SDR, radar, microphone, camera, OS
  device, browser, robotics, or network.
- No real-world actuation. No shell execution. No source modification.
- Feeder events are **observations, never operator commands**. Sensory text is
  never executed.
- Human labels are **annotations, never ground truth**.
- Event envelopes must never carry executable payloads.

## Privacy rules by modality

- **RF / mmWave:** export spectrum/reflection **features** only (power, band,
  noise floor, burstiness, drift, periodicity; distance, reflectivity, Doppler,
  cluster count). **Never decode communication content.** Decoded messages or
  plaintext are forbidden.
- **Audio:** export **metadata/features** (loudness, band energy, onset rate),
  never raw speech or transcripts.
- **Visual:** export **metadata/features** (brightness, motion estimate, region
  count), never raw images. Raw imagery is out of scope and would require a
  separate, future, explicitly-approved process.
- **Thermal:** export **gradient summaries**, never thermal imagery of people.
- **Vibration / magnetic / pressure:** export feature summaries only; do not
  infer keystrokes or device identity as ground truth.
- **Human text:** may contain human text, but it must be marked
  (`contains_human_text`) and treated as observation only.

## Privacy flags

Every envelope carries `privacy_flags`. Use the most specific applicable flag and
always include `no_raw_private_content` when true:

`no_raw_private_content`, `metadata_only`, `contains_human_text`,
`contains_file_metadata`, `contains_rf_features_only`,
`contains_audio_metadata_only`, `contains_visual_metadata_only`,
`contains_external_annotation`, `unknown_privacy_risk`.

A `PrivacyFilter` (`solaris_ai_nn.feeder_sdk.privacy`) blocks any envelope that
appears to carry raw/private content (`decoded_message`, `plaintext`,
`transcript`, `raw_audio`, `raw_video`, `raw_image`, `private_content`,
`payload`).

## Provenance

Provenance is mandatory: every envelope must record its `source_id` and
`feeder_id`. Replayed events must be marked `replayed`; simulated events must be
marked `simulated_fixture`. Provenance is never hidden.

## What this enables

Following this guide makes **real peculiar perception possible** -- RF, echo,
vibration, thermal, magnetic, human-like, machine-rhythm -- **without granting
Solaris any control over sensors, hardware, processes, source files, the network,
or the real world.**
