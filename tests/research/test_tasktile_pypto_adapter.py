import json
from pathlib import Path

import pytest

from xdsl.research.tasktile import (
    Task,
    TaskTileProgram,
    export_pypto_checkpoint,
    import_pypto_checkpoint,
)


def test_pypto_adapter_preserves_provenance_and_program() -> None:
    program = TaskTileProgram(tasks=(Task("compute", 3),))
    payload = export_pypto_checkpoint(
        program, repository="pypto", revision="abc123", pass_name="LowerTasks"
    )
    restored, source = import_pypto_checkpoint(payload)
    assert restored == program
    assert source == {"repository": "pypto", "revision": "abc123", "pass": "LowerTasks"}


def test_pypto_adapter_requires_provenance() -> None:
    with pytest.raises(ValueError, match="source metadata"):
        import_pypto_checkpoint({"tasktile": {"schema_version": 1, "tasks": []}})


def test_pypto_adapter_rejects_missing_tasktile() -> None:
    with pytest.raises(ValueError, match="tasktile object"):
        import_pypto_checkpoint(
            {"source": {"repository": "pypto", "revision": "a", "pass": "p"}}
        )


def test_pypto_two_submit_fixture_round_trip_and_mutation_rejection() -> None:
    fixture = Path(__file__).parents[1] / "data/tasktile/pypto-two-submit.json"
    payload = json.loads(fixture.read_text())
    program, source = import_pypto_checkpoint(payload)
    assert source["pass"] == "post:MaterializeValidShapeSymbols"
    assert [task.id for task in program.topological_tasks()] == ["producer", "consumer"]
    assert program.stages[0].buffer == "buf0"
    assert program.buffers[0].slots == 2
    assert program.communication[0].ranks == (0, 1)

    bad_dependency = json.loads(fixture.read_text())
    bad_dependency["tasktile"]["tasks"][0]["dependencies"] = ["missing"]
    with pytest.raises(ValueError, match="unknown dependency"):
        import_pypto_checkpoint(bad_dependency)

    bad_slots = json.loads(fixture.read_text())
    bad_slots["tasktile"]["buffers"][0]["slots"] = 0
    with pytest.raises(ValueError, match="positive bytes and slots"):
        import_pypto_checkpoint(bad_slots)

    bad_ranks = json.loads(fixture.read_text())
    bad_ranks["tasktile"]["communication"][0]["ranks"] = []
    with pytest.raises(ValueError, match="invalid communication"):
        import_pypto_checkpoint(bad_ranks)
