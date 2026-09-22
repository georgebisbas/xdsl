import pytest

from xdsl.research.tasktile import (
    Buffer,
    Task,
    TaskTileProgram,
    TileStage,
    assert_legal,
    validate,
)


def test_scheduled_program_is_legal() -> None:
    program = TaskTileProgram(
        tasks=(Task("load", 2), Task("compute", 3, ("load",))),
        stages=(TileStage("load-stage", "load", 2, "ub", 0, 0),),
        buffers=(Buffer("ub", 1024, 1),),
    )

    assert validate(program) == ()
    assert_legal(program)


def test_validator_reports_dependency_start_violation() -> None:
    program = TaskTileProgram(
        tasks=(Task("load", 2, start=4), Task("compute", 3, ("load",), start=2))
    )

    issues = validate(program)

    assert [issue.code for issue in issues] == ["task-dependency-order"]


def test_validator_reports_invalid_buffer_slot() -> None:
    program = TaskTileProgram(
        tasks=(Task("load", 2),),
        stages=(TileStage("stage", "load", 2, "ub", 2),),
        buffers=(Buffer("ub", 1024, 2),),
    )

    assert [issue.code for issue in validate(program)] == ["buffer-slot-range"]


def test_assert_legal_exposes_all_violations() -> None:
    program = TaskTileProgram(
        tasks=(Task("load", 2, start=-1),),
        stages=(TileStage("stage", "load", 2, "ub", -1, -2),),
        buffers=(Buffer("ub", 1024, 1),),
    )

    with pytest.raises(ValueError, match=r"task-start-negative.*buffer-slot-range"):
        assert_legal(program)
