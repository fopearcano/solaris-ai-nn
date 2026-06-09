"""Solaris-AI-NN: a low-compute, continuous-learning neural laboratory.

Solaris-AI-NN is the experimental neural / low-compute / continuous-learning
substrate for the conceptual system ``fopearcano/solaris-ai``. It explores how
that architecture can gain adaptive, neural-like behaviour *without* becoming a
conventional large deep-learning chatbot.

This package is consciousness-*inspired*. It makes no claim that the software is
conscious. Every concept maps to a concrete object, metric, or experiment.

Top-level convenience imports:

    from solaris_ai_nn import ExperimentLoop, ESN, run_minimal_continuous_esn
"""

from __future__ import annotations

__version__ = "0.1.0"

from .experiments.minimal_continuous_esn import run_minimal_continuous_esn  # noqa: F401
from .reservoir.esn import ESN  # noqa: F401
from .runtime.experiment_loop import ExperimentLoop  # noqa: F401

__all__ = ["ExperimentLoop", "ESN", "run_minimal_continuous_esn", "__version__"]
