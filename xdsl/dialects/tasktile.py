"""A small TaskTile dialect used by the xDSL-PyPTO research prototype."""

from __future__ import annotations

from collections.abc import Sequence

from xdsl.dialects.builtin import ArrayAttr, IntegerAttr, IntegerType, StringAttr
from xdsl.ir import Dialect
from xdsl.irdl import IRDLOperation, irdl_op_definition, prop_def
from xdsl.utils.exceptions import VerifyException

_I64 = IntegerType(64)


def _int(value: int) -> IntegerAttr:
    return IntegerAttr(value, _I64)


@irdl_op_definition
class ProgramOp(IRDLOperation):
    name = "tasktile.program"
    name_attr = prop_def(StringAttr)

    def __init__(self, name: str = "main"):
        super().__init__(properties={"name_attr": StringAttr(name)})

    def verify_(self) -> None:
        if not self.name_attr.data:
            raise VerifyException("tasktile.program requires a non-empty name")


@irdl_op_definition
class TaskOp(IRDLOperation):
    name = "tasktile.task"
    task_id = prop_def(StringAttr)
    duration = prop_def(IntegerAttr)
    engine = prop_def(StringAttr)
    dependencies = prop_def(ArrayAttr[StringAttr])

    def __init__(
        self,
        task_id: str,
        duration: int,
        engine: str = "aic",
        dependencies: Sequence[str] = (),
    ):
        super().__init__(
            properties={
                "task_id": StringAttr(task_id),
                "duration": _int(duration),
                "engine": StringAttr(engine),
                "dependencies": ArrayAttr([StringAttr(dep) for dep in dependencies]),
            }
        )

    def verify_(self) -> None:
        if not self.task_id.data:
            raise VerifyException("tasktile.task requires a non-empty id")
        if self.duration.type != _I64 or self.duration.value.data <= 0:
            raise VerifyException("tasktile.task duration must be positive i64")
        if self.engine.data not in {"aic", "aiv", "mte", "aicpu"}:
            raise VerifyException(f"unknown TaskTile engine: {self.engine.data}")


@irdl_op_definition
class BufferOp(IRDLOperation):
    name = "tasktile.buffer"
    buffer_id = prop_def(StringAttr)
    bytes = prop_def(IntegerAttr)
    slots = prop_def(IntegerAttr)
    memory_space = prop_def(StringAttr)

    def __init__(
        self, buffer_id: str, bytes: int, slots: int = 1, memory_space: str = "ub"
    ):
        super().__init__(
            properties={
                "buffer_id": StringAttr(buffer_id),
                "bytes": _int(bytes),
                "slots": _int(slots),
                "memory_space": StringAttr(memory_space),
            }
        )

    def verify_(self) -> None:
        if not self.buffer_id.data:
            raise VerifyException("tasktile.buffer requires a non-empty id")
        if self.bytes.value.data <= 0 or self.slots.value.data <= 0:
            raise VerifyException("tasktile.buffer bytes and slots must be positive")


@irdl_op_definition
class CommOp(IRDLOperation):
    name = "tasktile.comm"
    phase_id = prop_def(StringAttr)
    task = prop_def(StringAttr)
    ranks = prop_def(ArrayAttr[IntegerAttr])
    bytes = prop_def(IntegerAttr)
    synchronization = prop_def(StringAttr)

    def __init__(
        self,
        phase_id: str,
        task: str,
        ranks: Sequence[int],
        bytes: int,
        synchronization: str = "fifo",
    ):
        super().__init__(
            properties={
                "phase_id": StringAttr(phase_id),
                "task": StringAttr(task),
                "ranks": ArrayAttr([_int(rank) for rank in ranks]),
                "bytes": _int(bytes),
                "synchronization": StringAttr(synchronization),
            }
        )

    def verify_(self) -> None:
        if not self.phase_id.data or not self.task.data:
            raise VerifyException("tasktile.comm requires phase and task ids")
        if not self.ranks.data:
            raise VerifyException("tasktile.comm requires at least one rank")
        if any(rank.value.data < 0 for rank in self.ranks.data):
            raise VerifyException("tasktile.comm ranks must be non-negative")
        if self.bytes.value.data < 0:
            raise VerifyException("tasktile.comm bytes must be non-negative")


TaskTile = Dialect([ProgramOp, TaskOp, BufferOp, CommOp], [])
