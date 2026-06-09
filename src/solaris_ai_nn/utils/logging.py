"""Minimal logging helper built on the stdlib ``logging`` module.

Keeps configuration in one place so experiments and runtime components log
consistently without pulling in any third-party logging framework.
"""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def get_logger(name: str = "solaris_ai_nn", level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger.

    Args:
        name: Logger name (usually the module name).
        level: Logging level for the root ``solaris_ai_nn`` logger.

    Returns:
        A ``logging.Logger`` writing concise lines to stderr.
    """
    global _CONFIGURED
    root = logging.getLogger("solaris_ai_nn")
    if not _CONFIGURED:
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        root.addHandler(handler)
        root.setLevel(level)
        root.propagate = False
        _CONFIGURED = True
    return logging.getLogger(name)
