"""JSON serialization for the Inner MAP model.

Plain JSON only -- the self-model must stay inspectable. Integrates with the
runtime ``PersistenceManager`` so checkpoints can include ``inner_map.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Union

from .model import InnerMapModel


def inner_map_to_json(model: InnerMapModel) -> str:
    """Serialise an Inner MAP model to a pretty JSON string."""
    return json.dumps(model.to_dict(), indent=2, default=str)


def inner_map_from_json(data: Union[str, bytes, Dict[str, Any]]) -> InnerMapModel:
    """Rebuild an Inner MAP model from a JSON string/bytes or an already-parsed dict."""
    if isinstance(data, (str, bytes)):
        data = json.loads(data)
    return InnerMapModel.from_dict(data)


def save_inner_map(model: InnerMapModel, path: Union[str, Path]) -> None:
    """Write the model to ``path`` as JSON (parent dirs created as needed)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(inner_map_to_json(model))


def load_inner_map(path: Union[str, Path]) -> InnerMapModel:
    """Load an Inner MAP model from a JSON file written by :func:`save_inner_map`."""
    with open(path, "r", encoding="utf-8") as fh:
        return inner_map_from_json(fh.read())
