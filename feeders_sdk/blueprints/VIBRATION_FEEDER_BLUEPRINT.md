# Vibration rhythm feeder

_Documentation-only blueprint. This is NOT a hardware driver and is NEVER executed by Solaris. It describes how an external process should feed Solaris safely. Solaris reads the resulting event envelopes read-only; it does not control any sensor or hardware._

- modality: `vibration`
- status: `external_hardware_required`
- external collector concept: external accelerometer logger produces vibration features
- expected feature schema: `vibration_event`
- output envelope path: `.solaris_ai_nn_live/inbox/vibration/vibration.jsonl`

## What Solaris receives

- amplitude
- frequency
- rhythm_period

## What Solaris must NOT receive

- keystroke inference as truth

## Privacy risks

- low

## Safety constraints

- no Solaris hardware control; Solaris reads envelopes only

## Example envelope

```json
{
  "event_id": "FSE_13f56147da",
  "feeder_id": "vibration_feeder",
  "source_id": "vibration_source",
  "source_kind": "external_feature_drop",
  "modality": "vibration",
  "timestamp": 1781512023.0,
  "features": {
    "amplitude": 0.5
  },
  "annotation": null,
  "annotation_status": "none",
  "provenance": {
    "source_id": "vibration_source",
    "feeder_id": "vibration_feeder",
    "blueprint": "vibration_feeder"
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
