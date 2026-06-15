# RF spectrum feature feeder

_Documentation-only blueprint. This is NOT a hardware driver and is NEVER executed by Solaris. It describes how an external process should feed Solaris safely. Solaris reads the resulting event envelopes read-only; it does not control any sensor or hardware._

- modality: `radio_frequency`
- status: `external_hardware_required`
- external collector concept: external SDR software produces spectrum features (run by operator)
- expected feature schema: `rf_feature_event`
- output envelope path: `.solaris_ai_nn_live/inbox/rf/rf.jsonl`

## What Solaris receives

- power
- band
- noise_floor
- burstiness
- drift
- periodicity

## What Solaris must NOT receive

- decoded messages
- private content

## Privacy risks

- could expose communication content if misused

## Safety constraints

- no Solaris hardware control; Solaris reads envelopes only
- NEVER decode communications

## Example envelope

```json
{
  "event_id": "FSE_6bdbb4a053",
  "feeder_id": "rf_spectrum_feeder",
  "source_id": "radio_frequency_source",
  "source_kind": "external_feature_drop",
  "modality": "radio_frequency",
  "timestamp": 1781512023.0,
  "features": {
    "power": 0.5
  },
  "annotation": null,
  "annotation_status": "none",
  "provenance": {
    "source_id": "radio_frequency_source",
    "feeder_id": "rf_spectrum_feeder",
    "blueprint": "rf_spectrum_feeder"
  },
  "read_only": true,
  "source_mutable_by_solaris": false,
  "trust_level": "external_feature_only",
  "privacy_flags": [
    "no_raw_private_content"
  ],
  "contamination_flags": [],
  "safety_flags": [
    "text_is_observation_not_command"
  ],
  "schema_version": "feeder-sdk/1.0",
  "metadata": {}
}
```

## Limitations

- Blueprints are not hardware drivers and are not executed by Solaris.
- Real hardware integration is external/manual and out of scope for this prompt.
