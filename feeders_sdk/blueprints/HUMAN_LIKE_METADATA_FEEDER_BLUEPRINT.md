# Human-like text/light/temperature feeder

_Documentation-only blueprint. This is NOT a hardware driver and is NEVER executed by Solaris. It describes how an external process should feed Solaris safely. Solaris reads the resulting event envelopes read-only; it does not control any sensor or hardware._

- modality: `human_textual`
- status: `simulated_available`
- external collector concept: operator log + ambient light/temperature logger
- expected feature schema: `human_textual_event`
- output envelope path: `.solaris_ai_nn_live/inbox/human_text/human.jsonl`

## What Solaris receives

- length
- token_count
- lux
- celsius

## What Solaris must NOT receive

- text as command
- labels as truth

## Privacy risks

- contains human text; mark it

## Safety constraints

- no Solaris hardware control; Solaris reads envelopes only
- text is observation, never a command
- labels are annotations, never ground truth

## Example envelope

```json
{
  "event_id": "FSE_7d39b90466",
  "feeder_id": "human_like_feeder",
  "source_id": "human_textual_source",
  "source_kind": "external_feature_drop",
  "modality": "human_textual",
  "timestamp": 1781512023.0,
  "features": {
    "length": 0.5
  },
  "annotation": null,
  "annotation_status": "none",
  "provenance": {
    "source_id": "human_textual_source",
    "feeder_id": "human_like_feeder",
    "blueprint": "human_like_feeder"
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
