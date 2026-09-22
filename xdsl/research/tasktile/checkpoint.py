"""Versioned, deterministic TaskTile checkpoint serialization."""

from __future__ import annotations

import json
from typing import Any, cast

from .model import Buffer, CommPhase, Task, TaskTileProgram, TileStage

SCHEMA_VERSION = 1


def to_dict(program: TaskTileProgram) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tasks": [
            {
                "id": x.id,
                "duration": x.duration,
                "dependencies": list(x.dependencies),
                "engine": x.engine,
                "start": x.start,
                "witness": x.witness,
                "reads": list(x.reads),
                "writes": list(x.writes),
                "shape": list(x.shape),
            }
            for x in sorted(program.tasks, key=lambda x: x.id)
        ],
        "stages": [
            {
                "id": x.id,
                "task": x.task,
                "duration": x.duration,
                "buffer": x.buffer,
                "slot": x.slot,
                "start": x.start,
                "witness": x.witness,
                "bytes": x.bytes,
            }
            for x in sorted(program.stages, key=lambda x: x.id)
        ],
        "buffers": [
            {
                "id": x.id,
                "bytes": x.bytes,
                "slots": x.slots,
                "memory_space": x.memory_space,
                "witness": x.witness,
            }
            for x in sorted(program.buffers, key=lambda x: x.id)
        ],
        "communication": [
            {
                "id": x.id,
                "task": x.task,
                "ranks": list(x.ranks),
                "bytes": x.bytes,
                "synchronization": x.synchronization,
                "witness": x.witness,
            }
            for x in sorted(program.communication, key=lambda x: x.id)
        ],
    }


def dumps(program: TaskTileProgram) -> str:
    return json.dumps(to_dict(program), sort_keys=True, indent=2) + "\n"


def from_dict(data: dict[str, Any]) -> TaskTileProgram:
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported TaskTile schema: {data.get('schema_version')!r}")
    try:
        return TaskTileProgram(
            tasks=tuple(
                Task(
                    x["id"],
                    x["duration"],
                    tuple(x.get("dependencies", ())),
                    x.get("engine", "aic"),
                    x.get("start"),
                    x.get("witness"),
                    tuple(x.get("reads", ())),
                    tuple(x.get("writes", ())),
                    tuple(x.get("shape", ())),
                )
                for x in data["tasks"]
            ),
            stages=tuple(
                TileStage(
                    x["id"],
                    x["task"],
                    x["duration"],
                    x.get("buffer"),
                    x.get("slot", 0),
                        x.get("start"),
                        x.get("witness"),
                        x.get("bytes"),
                )
                for x in data.get("stages", ())
            ),
            buffers=tuple(
                Buffer(
                    x["id"],
                    x["bytes"],
                    x.get("slots", 1),
                    x.get("memory_space", "ub"),
                    x.get("witness"),
                )
                for x in data.get("buffers", ())
            ),
            communication=tuple(
                CommPhase(
                    x["id"],
                    x["task"],
                    tuple(x["ranks"]),
                    x["bytes"],
                    x.get("synchronization", "fifo"),
                    x.get("witness"),
                )
                for x in data.get("communication", ())
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"invalid TaskTile checkpoint: {error}") from error


def loads(payload: str) -> TaskTileProgram:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid TaskTile JSON: {error}") from error
    if not isinstance(data, dict):
        raise ValueError("TaskTile checkpoint must be a JSON object")
    return from_dict(cast(dict[str, Any], data))
