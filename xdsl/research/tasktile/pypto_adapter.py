"""Dependency-free adapter contract for a future PyPTO checkpoint exporter."""

from __future__ import annotations

from typing import Any, cast

from .checkpoint import from_dict, to_dict
from .model import TaskTileProgram


def import_pypto_checkpoint(
    data: dict[str, Any],
) -> tuple[TaskTileProgram, dict[str, str]]:
    """
    Import a normalized PyPTO checkpoint without importing PyPTO itself.

    The native exporter must provide ``source`` metadata and a ``tasktile``
    object using the portable schema. Keeping this boundary dependency-free
    allows fixture tests to run on machines without CANN or PyPTO binaries.
    """
    raw_source = data.get("source")
    if not isinstance(raw_source, dict):
        raise ValueError("PyPTO checkpoint requires source metadata")
    source = cast(dict[str, Any], raw_source)
    required = ("repository", "revision", "pass")
    if any(not isinstance(source.get(key), str) or not source[key] for key in required):
        raise ValueError(
            "PyPTO source metadata requires repository, revision, and pass"
        )
    tasktile = data.get("tasktile")
    if not isinstance(tasktile, dict):
        raise ValueError("PyPTO checkpoint requires a tasktile object")
    return from_dict(cast(dict[str, Any], tasktile)), {key: source[key] for key in required}


def export_pypto_checkpoint(
    program: TaskTileProgram, *, repository: str, revision: str, pass_name: str
) -> dict[str, Any]:
    """Wrap a TaskTile program with the provenance a native exporter must emit."""
    if not repository or not revision or not pass_name:
        raise ValueError("PyPTO checkpoint provenance fields must be non-empty")
    return {
        "source": {"repository": repository, "revision": revision, "pass": pass_name},
        "tasktile": to_dict(program),
    }
