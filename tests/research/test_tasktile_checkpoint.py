import pytest

from xdsl.research.tasktile import (
    Buffer,
    CommPhase,
    Task,
    TaskTileProgram,
    TileStage,
    dumps,
    loads,
)


def test_checkpoint_round_trip_is_deterministic() -> None:
    program = TaskTileProgram(
        tasks=(
            Task("compute", 3, ("load",), "aic", 2, "pypto:submit:1"),
            Task("load", 2, engine="mte", witness="pypto:submit:0"),
        ),
        stages=(TileStage("stage", "load", 2, "ub", 1, witness="pypto:tile.load:0"),),
        buffers=(Buffer("ub", 1024, 2, witness="pypto:alloc:0"),),
        communication=(
            CommPhase("phase", "compute", (0, 1), 4096, witness="pypto:collective:0"),
        ),
    )
    payload = dumps(program)
    assert payload == dumps(loads(payload))
    assert loads(payload) == program


def test_checkpoint_rejects_unknown_schema() -> None:
    with pytest.raises(ValueError, match="unsupported TaskTile schema"):
        loads('{"schema_version": 99, "tasks": []}')


def test_checkpoint_rejects_malformed_json() -> None:
    with pytest.raises(ValueError, match="invalid TaskTile JSON"):
        loads("not json")
