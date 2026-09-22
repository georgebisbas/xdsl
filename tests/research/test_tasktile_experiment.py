import json

from xdsl.research.tasktile.experiment import (
    dump_synthetic_experiment,
    run_synthetic_experiment,
    summarize_synthetic_experiment,
)


def test_synthetic_experiment_is_deterministic_and_complete() -> None:
    first = run_synthetic_experiment()
    second = run_synthetic_experiment()
    assert first == second
    assert {(row["workload"], row["variant"]) for row in first} == {
        (workload, variant)
        for workload in ("overlap", "independent", "fanout", "collective", "contention")
        for variant in ("native", "task_only", "tile_only", "joint", "oracle")
    }


def test_synthetic_experiment_json_is_valid() -> None:
    payload = dump_synthetic_experiment()
    assert len(json.loads(payload)) == 25


def test_synthetic_summary_is_table_ready() -> None:
    summary = summarize_synthetic_experiment()
    assert [row["workload"] for row in summary] == [
        "overlap",
        "independent",
        "fanout",
        "collective",
        "contention",
    ]
    assert all(row["joint_gap_vs_oracle"] >= 0 for row in summary)
    assert all(row["oracle_candidates"] > 0 for row in summary)
    assert all(row["heuristic_gap"] >= 1.0 for row in summary)
