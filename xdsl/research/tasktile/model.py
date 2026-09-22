from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

Engine = Literal["aic", "aiv", "mte", "aicpu"]


@dataclass(frozen=True)
class Task:
    id: str
    duration: int
    dependencies: tuple[str, ...] = ()
    engine: Engine = "aic"
    start: int | None = None
    witness: str | None = None
    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    shape: tuple[int, ...] = ()
    generated_witness: str | None = None


@dataclass(frozen=True)
class TileStage:
    id: str
    task: str
    duration: int
    buffer: str | None = None
    slot: int = 0
    start: int | None = None
    witness: str | None = None
    bytes: int | None = None
    generated_witness: str | None = None


@dataclass(frozen=True)
class Buffer:
    id: str
    bytes: int
    slots: int = 1
    memory_space: str = "ub"
    witness: str | None = None
    generated_witness: str | None = None


@dataclass(frozen=True)
class CommPhase:
    id: str
    task: str
    ranks: tuple[int, ...]
    bytes: int
    synchronization: str = "fifo"
    witness: str | None = None
    generated_witness: str | None = None


@dataclass(frozen=True)
class TaskTileProgram:
    tasks: tuple[Task, ...]
    stages: tuple[TileStage, ...] = ()
    buffers: tuple[Buffer, ...] = ()
    communication: tuple[CommPhase, ...] = ()

    def __post_init__(self) -> None:
        ids = [task.id for task in self.tasks]
        if len(ids) != len(set(ids)):
            raise ValueError("task IDs must be unique")
        task_ids = set(ids)
        for task in self.tasks:
            if task.duration <= 0:
                raise ValueError(f"task {task.id} has non-positive duration")
            if any(dep not in task_ids for dep in task.dependencies):
                raise ValueError(f"task {task.id} references an unknown dependency")
        buffer_ids = {buffer.id for buffer in self.buffers}
        if len(buffer_ids) != len(self.buffers):
            raise ValueError("buffer IDs must be unique")
        for buffer in self.buffers:
            if buffer.bytes <= 0 or buffer.slots <= 0:
                raise ValueError(f"buffer {buffer.id} needs positive bytes and slots")
        for stage in self.stages:
            if stage.task not in task_ids or stage.duration <= 0:
                raise ValueError(f"invalid stage {stage.id}")
            if stage.buffer is not None and stage.buffer not in buffer_ids:
                raise ValueError(f"stage {stage.id} references an unknown buffer")
        for phase in self.communication:
            if phase.task not in task_ids or phase.bytes < 0 or not phase.ranks:
                raise ValueError(f"invalid communication phase {phase.id}")
        self.topological_tasks()

    def topological_tasks(self) -> tuple[Task, ...]:
        remaining = {task.id: task for task in self.tasks}
        ordered: list[Task] = []
        while remaining:
            ready = [
                task
                for task in remaining.values()
                if all(dep not in remaining for dep in task.dependencies)
            ]
            if not ready:
                raise ValueError("task dependency graph contains a cycle")
            for task in sorted(ready, key=lambda item: item.id):
                ordered.append(task)
                del remaining[task.id]
        return tuple(ordered)

    def with_tasks(self, tasks: tuple[Task, ...]) -> TaskTileProgram:
        return replace(self, tasks=tasks)
