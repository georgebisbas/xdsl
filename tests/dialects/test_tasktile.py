import pytest

from xdsl.dialects import get_all_dialects
from xdsl.dialects.tasktile import BufferOp, CommOp, TaskOp
from xdsl.utils.exceptions import VerifyException


def test_tasktile_ops_verify() -> None:
    TaskOp("compute", 4, "aic", ("load",)).verify()
    BufferOp("ub", 1024, 2).verify()
    CommOp("phase", "compute", (0, 1), 4096).verify()


def test_tasktile_rejects_invalid_engine() -> None:
    with pytest.raises(VerifyException, match="unknown TaskTile engine"):
        TaskOp("compute", 4, "gpu").verify()


def test_tasktile_rejects_empty_ranks() -> None:
    with pytest.raises(VerifyException, match="at least one rank"):
        CommOp("phase", "compute", (), 1).verify()


def test_tasktile_is_registered() -> None:
    assert get_all_dialects()["tasktile"]().operations
