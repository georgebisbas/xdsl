import json

from xdsl.research.tasktile.experiment import (
    dump_synthetic_experiment,
    run_synthetic_experiment,
)


def test_synthetic_experiment_is_deterministic_and_complete() -> None:
    first = run_synthetic_experiment()
    second = run_synthetic_experiment()
    assert first == second
    assert {(row["workload"], row["variant"]) for row in first} == {
        (workload, variant)
        for workload in ("overlap", "independent", "fanout", "collective")
        for variant in ("native", "task_only", "tile_only", "joint", "oracle")
    }


def test_synthetic_experiment_json_is_valid() -> None:
    payload = dump_synthetic_experiment()
    assert len(json.loads(payload)) == 20
