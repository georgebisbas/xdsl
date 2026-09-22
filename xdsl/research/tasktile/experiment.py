"""Deterministic, hardware-independent TaskTile experiment harness."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Any

from .model import Buffer, CommPhase, Task, TaskTileProgram, TileStage
from .replay import ReplayConfig, replay
from .schedule import (
    enumerate_small_programs,
    heuristic_gap,
    oracle_schedule,
    schedule_joint,
    schedule_task_only,
    schedule_tile_only,
)


def synthetic_corpus() -> tuple[tuple[str, TaskTileProgram], ...]:
    """Return small workload classes used to validate the intervention matrix."""
    return (
        (
            "overlap",
            TaskTileProgram(
                tasks=(Task("load", 2, engine="mte"), Task("compute", 3, ("load",))),
                buffers=(Buffer("ub", 1024, 2),),
                stages=(TileStage("load-stage", "load", 2, "ub"),),
                communication=(CommPhase("phase", "compute", (0, 1), 4096),),
            ),
        ),
        (
            "independent",
            TaskTileProgram(
                tasks=(Task("a", 2, engine="aic"), Task("b", 4, engine="aiv"))
            ),
        ),
        (
            "fanout",
            TaskTileProgram(
                tasks=(
                    Task("load", 2, engine="mte"),
                    Task("left", 3, ("load",), engine="aic"),
                    Task("right", 4, ("load",), engine="aiv"),
                ),
                buffers=(Buffer("shared", 2048, 2),),
                stages=(
                    TileStage("left-stage", "left", 3, "shared"),
                    TileStage("right-stage", "right", 4, "shared", slot=1),
                ),
            ),
        ),
        (
            "collective",
            TaskTileProgram(
                tasks=(
                    Task("produce", 2, engine="aic"),
                    Task("exchange", 2, ("produce",), engine="mte"),
                    Task("consume", 3, ("exchange",), engine="aiv"),
                ),
                communication=(
                    CommPhase("allgather", "exchange", (0, 1, 2, 3), 8192),
                ),
            ),
        ),
        (
            "contention",
            TaskTileProgram(
                tasks=(
                    Task("root", 2, engine="mte"),
                    Task("a", 5, ("root",), engine="aic"),
                    Task("b", 4, ("root",), engine="aic"),
                    Task("c", 3, ("root",), engine="aiv"),
                    Task("join", 2, ("a", "b", "c"), engine="aic"),
                ),
                buffers=(Buffer("single-slot", 4096, 1),),
                stages=(
                    TileStage("a-stage", "a", 5, "single-slot"),
                    TileStage("b-stage", "b", 4, "single-slot"),
                    TileStage("c-stage", "c", 3, "single-slot"),
                ),
            ),
        ),
    )


def _metrics(program: TaskTileProgram, config: ReplayConfig) -> dict[str, Any]:
    cost = replay(program, config)
    return asdict(cost)


def run_synthetic_experiment(
    config: ReplayConfig | None = None,
) -> list[dict[str, Any]]:
    """Evaluate all scheduling variants on the deterministic synthetic corpus."""
    config = config or ReplayConfig()
    results: list[dict[str, Any]] = []
    for name, program in synthetic_corpus():
        variants = {
            "native": program,
            "task_only": schedule_task_only(program),
            "tile_only": schedule_tile_only(program),
            "joint": schedule_joint(program),
        }
        oracle = oracle_schedule(program)
        if oracle is not None:
            variants["oracle"] = oracle[0]
        for variant, scheduled in variants.items():
            results.append(
                {
                    "workload": name,
                    "variant": variant,
                    "metrics": _metrics(scheduled, config),
                }
            )
    return results


def dump_synthetic_experiment(config: ReplayConfig | None = None) -> str:
    return json.dumps(run_synthetic_experiment(config), indent=2, sort_keys=True) + "\n"


def summarize_synthetic_experiment(
    config: ReplayConfig | None = None,
) -> list[dict[str, Any]]:
    """Return deterministic per-workload deltas for paper table generation."""
    rows = run_synthetic_experiment(config)
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["workload"], {})[row["variant"]] = row["metrics"]
    summary: list[dict[str, Any]] = []
    for workload, variants in grouped.items():
        native = variants["native"]["critical_path"]
        joint = variants["joint"]["critical_path"]
        oracle = variants.get("oracle", variants["joint"])["critical_path"]
        summary.append(
            {
                "workload": workload,
                "oracle_candidates": len(
                    enumerate_small_programs(
                        next(program for name, program in synthetic_corpus() if name == workload)
                    )
                ),
                "heuristic_gap": heuristic_gap(
                    next(program for name, program in synthetic_corpus() if name == workload)
                ),
                "native_critical_path": native,
                "joint_critical_path": joint,
                "oracle_critical_path": oracle,
                "joint_delta_vs_native": joint - native,
                "joint_gap_vs_oracle": joint - oracle,
            }
        )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the deterministic TaskTile replay experiment"
    )
    parser.add_argument("--sync-cost", type=int, default=1)
    parser.add_argument("--transfer-cost-per-byte", type=float, default=0.0)
    args = parser.parse_args(argv)
    print(
        dump_synthetic_experiment(
            ReplayConfig(args.sync_cost, args.transfer_cost_per_byte)
        ),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
