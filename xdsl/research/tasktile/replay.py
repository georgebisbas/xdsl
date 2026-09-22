from __future__ import annotations

from dataclasses import dataclass

from .model import TaskTileProgram


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
