# Solaris-AI-NN: Appendices

## Appendix A -- Prompt Roadmap (Prompts 41-66)

| prompt | module | label | status |
| --- | --- | --- | --- |
| 41 | plural_sensorium | Plural Sensorium | implemented |
| 42 | organismic_demo | Minimal Field Organism Demo | implemented |
| 43 | live_field | Real Read-Only Environmental Feeder Pack / Live Field | implemented |
| 44 | sensorium_lab | Sensorium Differentiation Lab | implemented |
| 45 | feeder_sdk | External Feeder SDK | implemented |
| 46 | perceptual_metabolism | Perceptual Metabolism | implemented |
| 47 | perceptual_ontogenesis | Sensorium-Native Ontogenesis | implemented |
| 48 | semiogenesis | Sensorium-Native Semiogenesis | implemented |
| 49 | sensorium_cognition | Sensorium-Native Cognition | implemented |
| 50 | self_boundary | Sensorium-Native Self-Boundary | implemented |
| 51 | desire_formation | Valence / Desire Formation | implemented |
| 52 | action_reaction | Action-Reaction / Consequence Learning | implemented |
| 53 | developmental_life | Long-Horizon Developmental Runtime | implemented |
| 54 | developmental_soak | Month-Scale Developmental Soak Protocol | implemented |
| 55 | developmental_replication | Cross-Run Replication and Falsification Lab | implemented |
| 56 | architecture_evolution | Architecture Evolution Lab | implemented |
| 57 | experiment_compiler | Experiment Compiler | implemented |
| 58 | implementation_intake | Implementation Intake | implemented |
| 59 | post_merge_assimilation | Post-Merge Assimilation | implemented |
| 60 | research_baseline | Versioned Research Baseline | implemented |
| 61 | research_cycle | Closed Research Cycle Orchestrator | implemented |
| 62 | scientific_claims | Scientific Claim Registry | implemented |
| 63 | independent_review | Independent Reproducibility Review | implemented |
| 64 | review_assimilation | Reviewer Feedback Assimilation | implemented |
| 65 | alpha_system | Alpha Research System Assembly and Unified CLI | implemented |
| 66 | architecture_book | Technical Whitepaper and Architecture Book | implemented |

## Appendix B -- Module-to-Package Mapping

| module | package path | required |
| --- | --- | --- |
| plural_sensorium | solaris_ai_nn.plural_sensorium | False |
| organismic_demo | solaris_ai_nn.organismic_demo | False |
| live_field | solaris_ai_nn.live_field | False |
| sensorium_lab | solaris_ai_nn.sensorium_lab | False |
| feeder_sdk | solaris_ai_nn.feeder_sdk | False |
| perceptual_metabolism | solaris_ai_nn.perceptual_metabolism | False |
| perceptual_ontogenesis | solaris_ai_nn.perceptual_ontogenesis | False |
| semiogenesis | solaris_ai_nn.semiogenesis | False |
| sensorium_cognition | solaris_ai_nn.sensorium_cognition | False |
| self_boundary | solaris_ai_nn.self_boundary | False |
| desire_formation | solaris_ai_nn.desire_formation | False |
| action_reaction | solaris_ai_nn.action_reaction | False |
| developmental_life | solaris_ai_nn.developmental_life | False |
| developmental_soak | solaris_ai_nn.developmental_soak | False |
| developmental_replication | solaris_ai_nn.developmental_replication | False |
| architecture_evolution | solaris_ai_nn.architecture_evolution | False |
| experiment_compiler | solaris_ai_nn.experiment_compiler | False |
| implementation_intake | solaris_ai_nn.implementation_intake | False |
| post_merge_assimilation | solaris_ai_nn.post_merge_assimilation | False |
| research_baseline | solaris_ai_nn.research_baseline | False |
| research_cycle | solaris_ai_nn.research_cycle | False |
| scientific_claims | solaris_ai_nn.scientific_claims | False |
| independent_review | solaris_ai_nn.independent_review | False |
| review_assimilation | solaris_ai_nn.review_assimilation | False |
| alpha_system | solaris_ai_nn.alpha_system | True |
| architecture_book | solaris_ai_nn.architecture_book | True |

## Appendix C -- Artifact Directory Mapping

| directory | contents | present |
| --- | --- | --- |
| `.solaris_ai_nn_alpha/` | Alpha system state + reports | False |
| `.solaris_ai_nn_claims/` | Scientific claim reports | False |
| `.solaris_ai_nn_research_baseline/` | Research baseline reports | True |
| `.solaris_ai_nn_research_cycle/` | Research cycle reports | True |
| `.solaris_ai_nn_review/` | Independent review pack | False |
| `.solaris_ai_nn_review_assimilation/` | Reviewer feedback assimilation | False |
| `.solaris_ai_nn_soak/` | Developmental soak dossiers | True |
| `.solaris_ai_nn_replication/` | Replication / falsification reports | True |
| `.solaris_ai_nn_arch_evolution/` | Architecture evolution reports | False |
| `.solaris_ai_nn_docs/` | Documentation manifest + build report | True |

## Appendix D -- CLI Command Reference

All commands run via `python -m solaris_ai_nn <command> --state-dir ...` (local-only).

| command | purpose |
| --- | --- |
| `init` | initialize the alpha state layout |
| `doctor` | run the read-only system check |
| `modules` | print the module registry |
| `run-demo` | run the bounded fixture end-to-end demo |
| `artifact-index` | print/write the artifact index |
| `cycle-status` | print the alpha cycle status |
| `build-runbook` | generate the operator runbook |
| `build-report` | generate the alpha report from artifacts |
| `build-docs` | build the whitepaper / architecture book documents |
| `docs-index` | print the documentation index |
| `whitepaper` | build or print the technical whitepaper path |

## Appendix E -- Safety Rule Index

- no real-world actuation
- no hardware control
- no feeder control or auto-start
- no network/shell/browser/OS access
- no Git/GitHub call or command
- no branch/tag/release/PR creation
- no upload or publishing
- no external agent execution
- no source self-rewrite
- no Human Feedback / Teaching Loop
- no sensory text as command
- no human label as ground truth
- no unsupported consciousness/life/agency claim

## Appendix F -- Forbidden Claim Index

The system never asserts (only ever disclaims) any of the following:

- does not claim consciousness
- does not claim sentience
- does not claim biological life
- does not claim personhood
- does not claim agency
- does not claim free will
- does not claim emotion
- does not claim feeling
- does not claim understanding
- does not claim self-awareness
- does not claim autonomous self-improvement
- does not claim subjective experience

## Appendix G -- Example / Evidence Artifact Index

287 runnable example(s) under `examples/`. A representative subset:

- `examples/run_absence_stimulus_bridge.py`
- `examples/run_accumulation_vs_growth_demo.py`
- `examples/run_action_inhibition_demo.py`
- `examples/run_action_reaction_demo.py`
- `examples/run_active_perception_demo.py`
- `examples/run_adversarial_review_demo.py`
- `examples/run_alpha_cycle_status_demo.py`
- `examples/run_alpha_doctor_demo.py`
- `examples/run_alpha_e2e_demo.py`
- `examples/run_alpha_module_registry_demo.py`
- `examples/run_alpha_report_demo.py`
- `examples/run_anomaly_nursery_demo.py`
- `examples/run_architecture_book_demo.py`
- `examples/run_architecture_inventory_demo.py`
- `examples/run_architecture_review_demo.py`
- `examples/run_architecture_snapshot_demo.py`
- `examples/run_artifact_graph_demo.py`
- `examples/run_artifact_sanitizer_demo.py`
- `examples/run_assurance_case_demo.py`
- `examples/run_auto_determination_demo.py`
- `examples/run_autoregeneration_diagnostics_demo.py`
- `examples/run_autoregeneration_safety_demo.py`
- `examples/run_baseline_comparison_demo.py`
- `examples/run_baseline_registry_demo.py`
- `examples/run_benchmark_suite.py`

## Appendix H -- Open Research Questions

- Does sensorium-native structure survive passive-parser controls?
- Does it survive shuffled temporal order and random labels?
- Does growth track development or merely log accumulation?
- Does live read-only data change the result versus fixtures?
- Which single experiment would falsify the central claim?


_Appendices are generated from static prompt metadata and local artifacts; missing artifacts are listed. No publication or upload occurred and no consciousness/life/agency claim is made._
