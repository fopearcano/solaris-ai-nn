"""Appendix builder -- prompt roadmap, module/artifact maps, indexes.

:class:`ArchitectureAppendixBuilder` generates the appendices (prompt roadmap
41-66, module-to-package mapping, artifact directory mapping, CLI reference, safety
rule index, forbidden claim index, evidence artifact index, example/test indexes,
open research questions). Appendices are built from static prompt metadata and
local artifacts; missing artifacts are listed.
"""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .doc_manifest import PROMPTS

_PACKAGE_ROOT = "solaris_ai_nn"

_ARTIFACT_DIRS = (
    (".solaris_ai_nn_alpha", "Alpha system state + reports"),
    (".solaris_ai_nn_claims", "Scientific claim reports"),
    (".solaris_ai_nn_research_baseline", "Research baseline reports"),
    (".solaris_ai_nn_research_cycle", "Research cycle reports"),
    (".solaris_ai_nn_review", "Independent review pack"),
    (".solaris_ai_nn_review_assimilation", "Reviewer feedback assimilation"),
    (".solaris_ai_nn_soak", "Developmental soak dossiers"),
    (".solaris_ai_nn_replication", "Replication / falsification reports"),
    (".solaris_ai_nn_arch_evolution", "Architecture evolution reports"),
    (".solaris_ai_nn_docs", "Documentation manifest + build report"),
)

_CLI_COMMANDS = (
    ("init", "initialize the alpha state layout"),
    ("doctor", "run the read-only system check"),
    ("modules", "print the module registry"),
    ("run-demo", "run the bounded fixture end-to-end demo"),
    ("artifact-index", "print/write the artifact index"),
    ("cycle-status", "print the alpha cycle status"),
    ("build-runbook", "generate the operator runbook"),
    ("build-report", "generate the alpha report from artifacts"),
    ("build-docs", "build the whitepaper / architecture book documents"),
    ("docs-index", "print the documentation index"),
    ("whitepaper", "build or print the technical whitepaper path"),
)

_FORBIDDEN_CLAIMS = (
    "consciousness", "sentience", "biological life", "personhood", "agency",
    "free will", "emotion", "feeling", "understanding", "self-awareness",
    "autonomous self-improvement", "subjective experience",
)

_SAFETY_RULES = (
    "no real-world actuation", "no hardware control", "no feeder control or "
    "auto-start", "no network/shell/browser/OS access", "no Git/GitHub call or "
    "command", "no branch/tag/release/PR creation", "no upload or publishing",
    "no external agent execution", "no source self-rewrite", "no Human Feedback "
    "/ Teaching Loop", "no sensory text as command", "no human label as ground "
    "truth", "no unsupported consciousness/life/agency claim",
)

_OPEN_QUESTIONS = (
    "Does sensorium-native structure survive passive-parser controls?",
    "Does it survive shuffled temporal order and random labels?",
    "Does growth track development or merely log accumulation?",
    "Does live read-only data change the result versus fixtures?",
    "Which single experiment would falsify the central claim?",
)


@dataclass
class ArchitectureAppendixBuilder:
    """Builds the appendices document."""

    repo_root: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.repo_root:
            here = os.path.dirname(os.path.abspath(__file__))
            self.repo_root = os.path.abspath(os.path.join(here, "..", "..", ".."))

    def _available(self, pkg_path: str) -> bool:
        try:
            return importlib.util.find_spec(pkg_path) is not None
        except Exception:
            return False

    def build(self) -> str:
        lines = ["# Solaris-AI-NN: Appendices", ""]
        lines += self._prompt_roadmap()
        lines += self._module_mapping()
        lines += self._artifact_mapping()
        lines += self._cli_reference()
        lines += self._safety_index()
        lines += self._forbidden_index()
        lines += self._example_index()
        lines += self._open_questions()
        lines.append("")
        lines.append("_Appendices are generated from static prompt metadata and "
                     "local artifacts; missing artifacts are listed. No "
                     "publication or upload occurred and no consciousness/life/"
                     "agency claim is made._")
        return "\n".join(lines) + "\n"

    def _prompt_roadmap(self) -> List[str]:
        lines = ["## Appendix A -- Prompt Roadmap (Prompts 41-66)", "",
                 "| prompt | module | label | status |",
                 "| --- | --- | --- | --- |"]
        for num, key, label, pkg, _req in PROMPTS:
            status = "implemented" if self._available(pkg) else "planned/missing"
            lines.append(f"| {num} | {key} | {label} | {status} |")
        lines.append("")
        return lines

    def _module_mapping(self) -> List[str]:
        lines = ["## Appendix B -- Module-to-Package Mapping", "",
                 "| module | package path | required |",
                 "| --- | --- | --- |"]
        for _num, key, _label, pkg, req in PROMPTS:
            lines.append(f"| {key} | {pkg} | {req} |")
        lines.append("")
        return lines

    def _artifact_mapping(self) -> List[str]:
        lines = ["## Appendix C -- Artifact Directory Mapping", "",
                 "| directory | contents | present |",
                 "| --- | --- | --- |"]
        for d, desc in _ARTIFACT_DIRS:
            present = os.path.isdir(os.path.join(self.repo_root, d))
            lines.append(f"| `{d}/` | {desc} | {present} |")
        lines.append("")
        return lines

    def _cli_reference(self) -> List[str]:
        lines = ["## Appendix D -- CLI Command Reference", "",
                 "All commands run via `python -m solaris_ai_nn <command> "
                 "--state-dir ...` (local-only).", "",
                 "| command | purpose |", "| --- | --- |"]
        for cmd, desc in _CLI_COMMANDS:
            lines.append(f"| `{cmd}` | {desc} |")
        lines.append("")
        return lines

    def _safety_index(self) -> List[str]:
        lines = ["## Appendix E -- Safety Rule Index", ""]
        lines += [f"- {r}" for r in _SAFETY_RULES]
        lines.append("")
        return lines

    def _forbidden_index(self) -> List[str]:
        lines = ["## Appendix F -- Forbidden Claim Index", "",
                 "The system never asserts (only ever disclaims) any of the "
                 "following:", ""]
        # Each item is phrased as an explicit disclaimer so the enumeration is
        # not itself read as an assertion.
        lines += [f"- does not claim {c}" for c in _FORBIDDEN_CLAIMS]
        lines.append("")
        return lines

    def _example_index(self) -> List[str]:
        examples_dir = os.path.join(self.repo_root, "examples")
        lines = ["## Appendix G -- Example / Evidence Artifact Index", ""]
        if os.path.isdir(examples_dir):
            names = sorted(f for f in os.listdir(examples_dir)
                           if f.startswith("run_") and f.endswith(".py"))
            lines.append(f"{len(names)} runnable example(s) under `examples/`. "
                         "A representative subset:")
            lines.append("")
            lines += [f"- `examples/{n}`" for n in names[:25]]
        else:
            lines.append("- examples/ directory not present (missing artifact)")
        lines.append("")
        return lines

    def _open_questions(self) -> List[str]:
        lines = ["## Appendix H -- Open Research Questions", ""]
        lines += [f"- {q}" for q in _OPEN_QUESTIONS]
        lines.append("")
        return lines

    def summary(self) -> Dict[str, Any]:
        present_dirs = sum(1 for d, _ in _ARTIFACT_DIRS
                           if os.path.isdir(os.path.join(self.repo_root, d)))
        return {
            "appendix_count": 8,
            "prompt_count": len(PROMPTS),
            "artifact_dir_count": len(_ARTIFACT_DIRS),
            "present_artifact_dir_count": present_dirs,
            "forbidden_claim_count": len(_FORBIDDEN_CLAIMS),
            "note": "appendices are generated from static prompt metadata and "
                    "local artifacts; missing artifacts are listed",
        }
