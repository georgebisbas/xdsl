# TaskTile artifact

This document describes the standalone TaskTile research prototype. It does not
claim native PyPTO integration or Ascend performance.

## Scope

The artifact models tasks, tile stages, explicit buffers, and communication
phases. It provides deterministic validation, replay metrics, task-only and
tile-only baselines, a joint scheduler, and exhaustive topological enumeration
for programs with at most eight tasks.

The PyPTO boundary is deliberately not implemented yet. A future importer must
preserve values, effects, dependencies, memory spaces, buffer slots, rank sets,
and a source-to-generated lowering witness before hardware results are reported.

The portable checkpoint boundary is implemented by `dumps` and `loads` in
`xdsl.research.tasktile.checkpoint`. It uses schema version `1`, stable key
ordering, sorted entity lists, and the model validators on import. This is a
research interchange format, not yet a PyPTO-native exporter.

`export_pypto_checkpoint` and `import_pypto_checkpoint` define the next adapter
boundary. The adapter carries repository, revision, and pass provenance and
does not import PyPTO, CANN, or generated binaries. A native PyPTO exporter can
target this contract from a pass checkpoint.

## Public API

```python
from xdsl.research.tasktile import (
    Buffer, CommPhase, Task, TaskTileProgram, TileStage,
    replay, schedule_joint, schedule_task_only, schedule_tile_only,
)
```

All model objects are immutable. Program construction rejects duplicate IDs,
unknown references, cycles, non-positive durations or capacities, and invalid
communication ranks. `replay` returns critical path, synchronization estimate,
communication bytes, and peak on-chip memory.
It also reports deterministic aggregate engine occupancy by engine class.
Each entity may carry a lowering witness such as a PyPTO source span or generated
operation identifier. Checkpoint round trips preserve these witnesses.
For small programs, `oracle_schedule` and `heuristic_gap` provide an exhaustive
reference and critical-path ratio for scheduler-quality experiments.
`ReplayConfig` allows a separate calibration set to provide a synchronization
cost. The default remains a deterministic unit-cost model.
It also supports a non-negative transfer-time coefficient, which is reported
separately from communication bytes.

## Reproduce the smoke test

From the xDSL repository root:

```bash
PYTHONPATH=. pytest -q tests/research/test_tasktile.py tests/dialects/test_tasktile.py
```

The test suite is hardware-independent. It verifies legality failures, baseline
isolation, enumeration, dialect registration, and replay metrics.

Checkpoint round-trip tests can be run with:

```bash
PYTHONPATH=. pytest -q tests/research/test_tasktile_checkpoint.py
```

The adapter contract is covered by:

```bash
PYTHONPATH=. pytest -q tests/research/test_tasktile_pypto_adapter.py
```

## Overlap-sensitive example

The example below corresponds to `tests/data/tasktile/overlap.tasktile`:

```text
task load duration=2 engine=mte
task compute duration=3 depends=load engine=aic
buffer ub bytes=1024 slots=2 space=ub
stage load_stage task=load buffer=ub duration=2
comm phase task=compute ranks=0,1 bytes=4096 sync=fifo
```

The deterministic joint schedule starts `load` at time zero and `compute` at
time two. Its replay result is:

```text
critical_path=5
synchronization_stall=1
global_memory_bytes=4096
peak_on_chip_memory=2048
```

These are replay-model quantities, not device measurements.

## Research objective

The planned hardware experiment compares native PyPTO, task-only, tile-only,
and joint scheduling under identical correctness and memory-capacity constraints.
The current artifact establishes the representation and test harness needed for
that experiment; it does not establish a performance result.

The hardware-independent experiment harness is exposed by
`run_synthetic_experiment`. It evaluates native, task-only, tile-only, joint,
and oracle variants on five deterministic workloads: overlap, independent
tasks, fan-out with shared buffers, a multi-rank collective chain, and resource
contention. It returns JSON-compatible replay metrics. These results are model
evidence, not device-performance evidence.

Create a reproducibility manifest with `ArtifactManifest` from
`xdsl.research.tasktile.manifest`. The manifest records source revisions, the
TaskTile schema, replay calibration, test command, and whether hardware was
available. Keep it beside every captured JSON result.

For a self-contained artifact directory, run:

```bash
PYTHONPATH=. python3 -m xdsl.research.tasktile.release artifacts/local \
  --xdsl-revision <git-revision> --hardware unavailable \
  --simulation-image pypto3-hw-native-sys:sim-xdsl-tasktile@sha256:<digest>
```

The command writes `tasktile-results.json`, `tasktile-summary.json`, and
`manifest.json` together. The manifest records the exact simulation image when
provided. The summary is a table-ready projection of
native/joint/oracle critical paths and exhaustive-search diagnostics.

It is also runnable as a module:

```bash
PYTHONPATH=. python3 -m xdsl.research.tasktile.experiment \
  --sync-cost 1 --transfer-cost-per-byte 0.0 > tasktile-results.json
```
