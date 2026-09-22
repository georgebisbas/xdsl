from __future__ import annotations

from dataclasses import dataclass

from .model import TaskTileProgram


@dataclass(frozen=True)
class ReplayEvent:
    """A deterministic event explaining one replayed schedule decision."""

    kind: str
    identifier: str
    start: int
    finish: int
    detail: str


@dataclass(frozen=True)
class ReplayCost:
    critical_path: int
    synchronization_stall: int
    global_memory_bytes: int
    peak_on_chip_memory: int
    engine_occupancy: tuple[tuple[str, int], ...]
    transfer_time: float


@dataclass(frozen=True)
class ReplayConfig:
    """Device-independent calibration parameters for replay experiments."""

    synchronization_cost: int = 1
    transfer_cost_per_byte: float = 0.0

    def __post_init__(self) -> None:
        if self.synchronization_cost < 0 or self.transfer_cost_per_byte < 0:
            raise ValueError("replay calibration costs must be non-negative")


def replay(program: TaskTileProgram, config: ReplayConfig | None = None) -> ReplayCost:
    config = config or ReplayConfig()
    finish: dict[str, int] = {}
    for task in program.topological_tasks():
        start = (
            task.start
            if task.start is not None
            else max((finish[dep] for dep in task.dependencies), default=0)
        )
        finish[task.id] = start + task.duration
    phase_bytes = sum(phase.bytes for phase in program.communication)
    return ReplayCost(
        critical_path=max(finish.values(), default=0),
        synchronization_stall=sum(
            max(0, len(phase.ranks) - 1) * config.synchronization_cost
            for phase in program.communication
        ),
        global_memory_bytes=phase_bytes,
        peak_on_chip_memory=sum(
            buffer.bytes * buffer.slots
            for buffer in program.buffers
            if any(stage.buffer == buffer.id for stage in program.stages)
        ),
        engine_occupancy=tuple(
            sorted(
                (
                    engine,
                    sum(
                        task.duration for task in program.tasks if task.engine == engine
                    ),
                )
                for engine in {task.engine for task in program.tasks}
            )
        ),
        transfer_time=phase_bytes * config.transfer_cost_per_byte,
    )


def replay_trace(program: TaskTileProgram) -> tuple[ReplayEvent, ...]:
    """Return deterministic task, stage, and communication replay events."""
    finish: dict[str, int] = {}
    events: list[ReplayEvent] = []
    for task in program.topological_tasks():
        start = (
            task.start
            if task.start is not None
            else max((finish[dep] for dep in task.dependencies), default=0)
        )
        task_finish = start + task.duration
        finish[task.id] = task_finish
        dependencies = ",".join(sorted(task.dependencies)) or "none"
        events.append(
            ReplayEvent(
                "task", task.id, start, task_finish, f"dependencies={dependencies}"
            )
        )
    tasks = {task.id: task for task in program.tasks}
    for stage in sorted(program.stages, key=lambda item: item.id):
        start = (
            stage.start
            if stage.start is not None
            else (tasks[stage.task].start if tasks[stage.task].start is not None else 0)
        )
        events.append(
            ReplayEvent(
                "stage",
                stage.id,
                start,
                start + stage.duration,
                f"task={stage.task},buffer={stage.buffer},slot={stage.slot}",
            )
        )
    for phase in sorted(program.communication, key=lambda item: item.id):
        task = tasks[phase.task]
        start = task.start if task.start is not None else 0
        events.append(
            ReplayEvent(
                "communication",
                phase.id,
                start,
                start + task.duration,
                f"task={phase.task},ranks={','.join(map(str, phase.ranks))},bytes={phase.bytes}",
            )
        )
    return tuple(
        sorted(events, key=lambda event: (event.start, event.kind, event.identifier))
    )
