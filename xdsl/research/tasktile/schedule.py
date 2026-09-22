from __future__ import annotations

from dataclasses import replace
from itertools import permutations

from .model import Task, TaskTileProgram
from .replay import ReplayCost, replay


def schedule_task_only(program: TaskTileProgram) -> TaskTileProgram:
    finish: dict[str, int] = {}
    tasks: list[Task] = []
    for task in program.topological_tasks():
        start = max((finish[dep] for dep in task.dependencies), default=0)
        scheduled = replace(task, start=start)
        finish[task.id] = start + task.duration
        tasks.append(scheduled)
    return program.with_tasks(tuple(tasks))


def schedule_tile_only(program: TaskTileProgram) -> TaskTileProgram:
    slots = {buffer.id: buffer.slots for buffer in program.buffers}
    stages = tuple(
        replace(stage, slot=index % slots[stage.buffer]) if stage.buffer else stage
        for index, stage in enumerate(program.stages)
    )
    return replace(program, stages=stages)


def schedule_joint(program: TaskTileProgram) -> TaskTileProgram:
    candidates = tuple(enumerate_small_programs(program))
    if not candidates:
        return schedule_tile_only(schedule_task_only(program))
    # All candidates are legal and deterministic. The first minimum preserves
    # stable output when replay costs tie.
    return min(
        (schedule_tile_only(schedule_task_only(candidate)) for candidate in candidates),
        key=lambda candidate: _cost_key(replay(candidate)),
    )


def enumerate_small_programs(
    program: TaskTileProgram, *, max_tasks: int = 8
) -> tuple[TaskTileProgram, ...]:
    """
    Enumerate legal topological orders for small programs.

    The bound is intentional: this is an oracle for scheduler tests and
    heuristic-gap experiments, not a production search algorithm.
    """
    tasks = program.tasks
    if len(tasks) > max_tasks:
        return ()
    candidates: list[TaskTileProgram] = []
    for order in permutations(tasks):
        position = {task.id: index for index, task in enumerate(order)}
        if any(
            position[dep] >= position[task.id]
            for task in tasks
            for dep in task.dependencies
        ):
            continue
        candidates.append(program.with_tasks(tuple(order)))
    return tuple(candidates)


def oracle_schedule(
    program: TaskTileProgram, *, max_tasks: int = 8
) -> tuple[TaskTileProgram, ReplayCost] | None:
    """Return the minimum replay-cost legal schedule for a small program."""
    candidates = enumerate_small_programs(program, max_tasks=max_tasks)
    if not candidates:
        return None
    scheduled = tuple(
        schedule_tile_only(schedule_task_only(candidate)) for candidate in candidates
    )
    best = min(scheduled, key=lambda candidate: _cost_key(replay(candidate)))
    return best, replay(best)


def heuristic_gap(program: TaskTileProgram, *, max_tasks: int = 8) -> float | None:
    """Return joint critical-path ratio against the small-instance oracle."""
    oracle = oracle_schedule(program, max_tasks=max_tasks)
    if oracle is None:
        return None
    optimal = oracle[1].critical_path
    return replay(schedule_joint(program)).critical_path / optimal if optimal else 0.0


def _cost_key(
    cost: ReplayCost,
) -> tuple[int, int, int, int, tuple[tuple[str, int], ...]]:
    return (
        cost.critical_path,
        cost.synchronization_stall,
        cost.global_memory_bytes,
        cost.peak_on_chip_memory,
        cost.engine_occupancy,
    )
