"""Legality checks for transformed TaskTile schedules."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

from .model import TaskTileProgram

_VALID_ENGINES = {"aic", "aiv", "mte", "aicpu"}
_VALID_SYNCHRONIZATION = {"fifo", "barrier", "collective"}


@dataclass(frozen=True)
class ValidationIssue:
    """One deterministic schedule-legality violation."""

    code: str
    message: str


def validate(program: TaskTileProgram) -> tuple[ValidationIssue, ...]:
    """
    Return all schedule violations in stable program order.

    Construction-time invariants (unknown references and cycles) are already
    enforced by :class:`TaskTileProgram`; this pass checks properties that are
    only meaningful after a schedule transformation has populated start/slot
    metadata.
    """

    issues: list[ValidationIssue] = []
    tasks = {task.id: task for task in program.tasks}
    buffers = {buffer.id: buffer for buffer in program.buffers}

    for task in sorted(program.tasks, key=lambda item: item.id):
        if task.engine not in _VALID_ENGINES:
            issues.append(
                ValidationIssue(
                    "task-engine", f"task {task.id} uses unknown engine {task.engine}"
                )
            )
        if any(dimension <= 0 for dimension in task.shape):
            issues.append(
                ValidationIssue(
                    "task-shape", f"task {task.id} has non-positive shape {task.shape}"
                )
            )
        if task.start is not None and task.start < 0:
            issues.append(
                ValidationIssue(
                    "task-start-negative",
                    f"task {task.id} has negative start {task.start}",
                )
            )
        if task.start is None:
            continue
        for dependency in sorted(task.dependencies):
            dependency_task = tasks[dependency]
            if dependency_task.start is not None:
                dependency_finish = dependency_task.start + dependency_task.duration
                if task.start < dependency_finish:
                    issues.append(
                        ValidationIssue(
                            "task-dependency-order",
                            f"task {task.id} starts before dependency {dependency} finishes",
                        )
                    )

    for stage in sorted(program.stages, key=lambda item: item.id):
        if stage.buffer is not None:
            buffer = buffers[stage.buffer]
            if stage.bytes is not None and stage.bytes <= 0:
                issues.append(
                    ValidationIssue(
                        "buffer-capacity",
                        f"stage {stage.id} has non-positive footprint {stage.bytes}",
                    )
                )
            elif stage.bytes is not None and stage.bytes > buffer.bytes:
                issues.append(
                    ValidationIssue(
                        "buffer-capacity",
                        f"stage {stage.id} needs {stage.bytes} bytes but buffer {buffer.id} has {buffer.bytes}",
                    )
                )
            if stage.slot < 0 or stage.slot >= buffer.slots:
                issues.append(
                    ValidationIssue(
                        "buffer-slot-range",
                        f"stage {stage.id} uses slot {stage.slot} of {buffer.slots}",
                    )
                )
        if stage.start is not None:
            if stage.start < 0:
                issues.append(
                    ValidationIssue(
                        "stage-start-negative",
                        f"stage {stage.id} has negative start {stage.start}",
                    )
                )
            task = tasks[stage.task]
            if task.start is not None and stage.start < task.start:
                issues.append(
                    ValidationIssue(
                        "stage-before-task",
                        f"stage {stage.id} starts before task {stage.task}",
                    )
                )

    intervals: dict[tuple[str, int], list[tuple[int, int, str]]] = {}
    for stage in program.stages:
        if stage.buffer is None or stage.start is None:
            continue
        key = (stage.buffer, stage.slot)
        intervals.setdefault(key, []).append(
            (stage.start, stage.start + stage.duration, stage.id)
        )
    for key, entries in sorted(intervals.items()):
        entries.sort()
        for previous, current in pairwise(entries):
            if current[0] < previous[1]:
                issues.append(
                    ValidationIssue(
                        "buffer-slot-overlap",
                        f"stages {previous[2]} and {current[2]} overlap on {key[0]} slot {key[1]}",
                    )
                )

    communication_ids = [phase.id for phase in program.communication]
    for phase_id in sorted(set(communication_ids)):
        if communication_ids.count(phase_id) > 1:
            issues.append(
                ValidationIssue(
                    "communication-id", f"communication phase {phase_id} is duplicated"
                )
            )
    scheduled_tasks = [task for task in program.tasks if task.start is not None]
    for index, first in enumerate(scheduled_tasks):
        first_finish = first.start + first.duration  # type: ignore[operator]
        first_writes = set(first.writes)
        for second in scheduled_tasks[index + 1 :]:
            second_finish = second.start + second.duration  # type: ignore[operator]
            if second.start >= first_finish or first.start >= second_finish:
                continue
            if first_writes & (set(second.reads) | set(second.writes)):
                if (
                    second.id not in first.dependencies
                    and first.id not in second.dependencies
                ):
                    issues.append(
                        ValidationIssue(
                            "task-effect-race",
                            f"scheduled tasks {first.id} and {second.id} overlap on effects",
                        )
                    )
    for phase in sorted(program.communication, key=lambda item: item.id):
        if phase.synchronization not in _VALID_SYNCHRONIZATION:
            issues.append(
                ValidationIssue(
                    "communication-synchronization",
                    f"communication phase {phase.id} uses unknown synchronization {phase.synchronization}",
                )
            )
        if len(set(phase.ranks)) != len(phase.ranks) or any(
            rank < 0 for rank in phase.ranks
        ):
            issues.append(
                ValidationIssue(
                    "communication-ranks",
                    f"communication phase {phase.id} has invalid rank set {phase.ranks}",
                )
            )

    return tuple(issues)


def assert_legal(program: TaskTileProgram) -> None:
    """Raise one deterministic error containing every legality violation."""

    issues = validate(program)
    if issues:
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        raise ValueError(f"illegal TaskTile schedule: {details}")
