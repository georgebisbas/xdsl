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
