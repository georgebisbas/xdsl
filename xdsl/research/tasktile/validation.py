"""Legality checks for transformed TaskTile schedules."""

from __future__ import annotations

from dataclasses import dataclass

from .model import TaskTileProgram


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

    return tuple(issues)


def assert_legal(program: TaskTileProgram) -> None:
    """Raise one deterministic error containing every legality violation."""

    issues = validate(program)
    if issues:
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        raise ValueError(f"illegal TaskTile schedule: {details}")
