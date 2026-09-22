import pytest

from xdsl.research.tasktile import (
    Buffer,
    CommPhase,
    ReplayConfig,
    Task,
    TaskTileProgram,
    TileStage,
    heuristic_gap,
    replay,
    replay_trace,
    schedule_joint,
    schedule_task_only,
    schedule_tile_only,
)
from xdsl.research.tasktile.schedule import enumerate_small_programs, oracle_schedule


def test_joint_schedule_replays_dependencies_and_resources() -> None:
    program = TaskTileProgram(
        tasks=(Task("load", 2, engine="mte"), Task("compute", 3, ("load",))),
        buffers=(Buffer("ub", 1024, 2),),
        stages=(TileStage("load-stage", "load", 2, "ub"),),
        communication=(CommPhase("phase", "compute", (0, 1), 4096),),
    )

    cost = replay(schedule_joint(program))

    assert cost.critical_path == 5
    assert cost.synchronization_stall == 1
    assert cost.global_memory_bytes == 4096
    assert cost.peak_on_chip_memory == 2048
    assert cost.engine_occupancy == (("aic", 3), ("mte", 2))


def test_cycles_are_rejected() -> None:
    with pytest.raises(ValueError, match="cycle"):
        TaskTileProgram(
            tasks=(Task("a", 1, ("b",)), Task("b", 1, ("a",))),
        )


def test_unknown_buffer_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown buffer"):
        TaskTileProgram(
            tasks=(Task("a", 1),),
            stages=(TileStage("s", "a", 1, "missing"),),
        )


def test_scheduler_baselines_change_only_their_owned_decisions() -> None:
    program = TaskTileProgram(
        tasks=(Task("b", 1), Task("a", 1)),
        buffers=(Buffer("ub", 8, 2),),
        stages=(TileStage("s0", "a", 1, "ub"), TileStage("s1", "b", 1, "ub")),
    )
    task_only = schedule_task_only(program)
    tile_only = schedule_tile_only(program)
    assert tuple(task.id for task in task_only.tasks) == ("a", "b")
    assert tuple(task.start for task in tile_only.tasks) == (None, None)
    assert tuple(stage.slot for stage in tile_only.stages) == (0, 1)


def test_small_instance_enumerator_returns_all_topological_orders() -> None:
    program = TaskTileProgram(tasks=(Task("a", 1), Task("b", 1)))
    candidates = enumerate_small_programs(program)
    assert len(candidates) == 2
    assert {tuple(task.id for task in candidate.tasks) for candidate in candidates} == {
        ("a", "b"),
        ("b", "a"),
    }


def test_oracle_and_heuristic_gap_are_reported() -> None:
    program = TaskTileProgram(tasks=(Task("a", 2), Task("b", 3)))
    result = oracle_schedule(program)
    assert result is not None
    assert result[1].critical_path == 3
    assert heuristic_gap(program) == 1.0


def test_replay_calibration_changes_only_calibrated_cost() -> None:
    program = TaskTileProgram(
        tasks=(Task("a", 1),),
        communication=(CommPhase("phase", "a", (0, 1, 2), 8),),
    )
    default = replay(program)
    calibrated = replay(program, ReplayConfig(synchronization_cost=5))
    assert default.critical_path == calibrated.critical_path
    assert calibrated.synchronization_stall == 10
    assert (
        replay(program, ReplayConfig(transfer_cost_per_byte=0.5)).transfer_time == 4.0
    )


def test_replay_trace_explains_task_stage_and_communication() -> None:
    program = TaskTileProgram(
        tasks=(Task("a", 2, start=3),),
        stages=(TileStage("stage", "a", 1, "ub", 0, 3),),
        buffers=(Buffer("ub", 8),),
        communication=(CommPhase("phase", "a", (0, 1), 4),),
    )

    events = replay_trace(program)

    assert [(event.kind, event.identifier) for event in events] == [
        ("communication", "phase"),
        ("stage", "stage"),
        ("task", "a"),
    ]
    assert events[-1].detail == "dependencies=none"
