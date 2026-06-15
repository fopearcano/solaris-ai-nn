# Solaris-AI-NN External Feeder SDK (standalone scripts)

These scripts are **outside Solaris**. They are artificial sensory organs: each
one observes some environmental phenomenon and **writes** Sensory Event Envelopes
to a local JSONL file. Solaris later **reads** those files read-only through the
Live Field layer (`solaris_ai_nn.live_field`) and the Plural Sensorium.

```
outside world
  -> external feeder / sensory organ (these scripts, run by the operator)
  -> local event envelope stream (.jsonl)
  -> Solaris read-only live field
  -> plural sensorium receptors
  -> sensory field
  -> internal adaptation
```

## The boundary (non-negotiable)

- **Solaris does not start, stop, configure, or command feeders.** The operator
  runs a feeder; Solaris only reads its output file.
- **No hardware control inside Solaris.** Hardware-specific collectors (SDR,
  mmWave, ultrasound, thermal, magnetic) are **external/manual** -- see
  `blueprints/`. If you have such hardware, run the vendor's collector yourself
  and have it export **feature summaries** (never raw private content) into a
  feeder output or an inbox folder, then point `feature_file_feeder.py` at it.
- **No network, no shell, no hardware** in any script here (standard library
  only).
- **Feeders never modify or delete what they observe.** They write only to their
  own output file.
- **Annotations are not ground truth.** Human text is an *environmental stimulus*,
  never a command, never a correct-answer label.
- **No raw private content.** Feeders emit feature summaries; audio/visual feeders
  emit metadata, not raw recordings; RF feeders never decode communications.

## Scripts

| Script | Modality | What it does |
|---|---|---|
| `feeder_template.py` | machine_rhythm | minimal template for writing your own feeder |
| `manual_log_feeder.py` | human_textual | operator environmental text (observation, not command) |
| `folder_rhythm_feeder.py` | machine_rhythm | folder file-metadata / rhythm (never modifies the folder) |
| `system_rhythm_feeder.py` | machine_rhythm | harmless local machine rhythm (no privileged data) |
| `feature_file_feeder.py` | (any) | normalize external JSON/CSV feature files (never modifies source) |
| `simulated_rf_feeder.py` | radio_frequency | **simulated** RF features (NOT a real sensor) |
| `simulated_echo_feeder.py` | ultrasound_echo | **simulated** echo reflections |
| `simulated_vibration_feeder.py` | vibration | **simulated** vibration rhythm |
| `simulated_magnetic_feeder.py` | magnetic | **simulated** magnetic field + anomaly |
| `simulated_thermal_feeder.py` | thermal_gradient | **simulated** thermal gradient summaries |
| `multimodal_feeder_demo.py` | (mixed) | combine the simulated feeders into one stream |

Simulated feeders generate jitter, silence, drift, and noise and mark their
provenance `simulated_fixture`. They are for testing the feeder contract and must
not be mistaken for real sensors.

## Data contract (one JSONL line)

```json
{
  "event_id": "FSE_ab12cd34ef",
  "feeder_id": "simulated_rf_feeder",
  "source_id": "sim_rf",
  "source_kind": "fixture_replay",
  "modality": "radio_frequency",
  "timestamp": 1718000000.0,
  "features": {"power": 0.71, "band": 2.44, "noise_floor": 0.12},
  "annotation": null,
  "annotation_status": "none",
  "provenance": {"source_id": "sim_rf", "feeder_id": "simulated_rf_feeder"},
  "read_only": true,
  "source_mutable_by_solaris": false,
  "trust_level": "simulated_fixture",
  "privacy_flags": ["contains_rf_features_only", "no_raw_private_content"],
  "contamination_flags": [],
  "safety_flags": ["text_is_observation_not_command"],
  "schema_version": "feeder-sdk/1.0",
  "metadata": {}
}
```

`features` are primary; `annotation` is optional and never ground truth.
`read_only` must be `true` and `source_mutable_by_solaris` must be `false`.

See `blueprints/` for documentation-only hardware feeder designs and
`blueprints/PRIVACY_AND_SAFETY_GUIDE.md` for the privacy rules.
