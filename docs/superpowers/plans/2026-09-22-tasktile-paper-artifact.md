# TaskTile Paper and Artifact Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a minimal reproducible TaskTile research artifact and a paper draft whose claims are limited to the implemented IR, legality checks, replay model, and scheduling baselines.

**Architecture:** Add a standalone Python research package under `xdsl/research/tasktile/`. It will use ordinary typed Python data classes for the schedule model and an xDSL dialect for serialized IR, keeping the prototype independent of PyPTO and suitable for unit tests without Ascend hardware. The notes repository will contain the paper draft and an artifact README that explains how native PyPTO export can be added later.

**Tech Stack:** Python 3.10+, xDSL IRDL, pytest, standard library only for the optimizer and replay model.

**Spec:** `/home/georgios/workspace/hw-native-sys/pypto-3.0-notes/xdsl-pypto-ideas/README.md`

## Progress

| Step | Status | Evidence |
| --- | --- | --- |
| 1. Data model | Complete | `xdsl/research/tasktile/model.py`; model and replay tests |
| 2. xDSL dialect | Complete | `xdsl/dialects/tasktile.py`; dialect verifier and registration tests |
| 3. Replay model | Complete | `xdsl/research/tasktile/replay.py`; replay assertions and engine occupancy |
| 4. Schedulers | Complete | deterministic baselines, bounded topological enumerator, 9-test focused suite |
| 5. Artifact docs/example | Complete | `docs/research/tasktile-artifact.md`; `tests/data/tasktile/overlap.tasktile` |
| 6. Paper draft | Complete | sibling notes repo `xdsl-pypto-ideas/tasktile-paper.md` |
| 7. Portable checkpoint boundary | Complete | `xdsl/research/tasktile/checkpoint.py`; 3 round-trip/schema tests |
| 8. PyPTO adapter contract | Complete | dependency-free provenance wrapper and 3 adapter tests |
| 9. Scheduler quality oracle | Complete | exhaustive small-instance oracle, heuristic-gap metric, regression test |
| 10. Lowering witnesses | Complete | optional entity provenance preserved by model and checkpoint round trips |
| 11. Calibrated replay | Complete | parameterized synchronization cost with default deterministic behavior |
| 12. Synthetic experiment harness | Complete | deterministic corpus and five-variant JSON result runner |
| 13. Experiment CLI | Complete | reproducible module command with calibration flags and JSON output |
| 14. Reproducibility manifest | Complete | revision, schema, calibration, hardware, and test-command manifest |
| 15. Artifact release command | Complete | paired results and manifest directory writer with CLI |

Latest verification command:

```bash
PYTHONPATH=. pytest -q tests/research/test_tasktile.py tests/dialects/test_tasktile.py
```

Observed result: `9 passed in 0.13s`.

## Global Constraints

- Do not claim device speedups or PyPTO integration until hardware and native integration exist.
- Preserve xDSL style and add focused unit tests for every public verifier and scheduler behavior.
- Keep the artifact deterministic: stable parsing, stable schedule output, and no network dependencies.
- Do not modify PyPTO or PTOAS in this first prototype.

### Task 1: Define the research data model [complete]

**Files:**
- Create: `xdsl/research/tasktile/model.py`
- Create: `tests/research/test_tasktile_model.py`

Implement immutable records for `Task`, `TileStage`, `Buffer`, `CommPhase`, and `TaskTileProgram`. Include explicit IDs, dependencies, engine class, buffer bytes, slot count, rank set, and phase order. Add deterministic topological ordering and reject duplicate IDs, unknown references, dependency cycles, negative sizes, and non-positive slot counts.

### Task 2: Add the xDSL TaskTile dialect [complete]

**Files:**
- Create: `xdsl/dialects/tasktile.py`
- Modify: `xdsl/dialects/__init__.py`
- Create: `tests/dialects/test_tasktile.py`

Define a minimal `tasktile.program`, `tasktile.task`, `tasktile.stage`, `tasktile.buffer`, and `tasktile.comm` dialect using IRDL. Attributes must encode engine, memory space, ranks, and synchronization kind. Verifiers must check local invariants and provide readable diagnostics. Test construction, verification, parse-print round trips, and invalid references.

### Task 3: Implement schedule replay and cost model [complete]

**Files:**
- Create: `xdsl/research/tasktile/replay.py`
- Create: `tests/research/test_tasktile_replay.py`

Replay a valid program into task critical path, synchronization stall estimate, global-memory bytes, peak on-chip memory, and engine occupancy. Keep the model explicit and deterministic. Expose `ReplayCost` and `replay(program)`. Test independent tasks, dependency chains, slot pressure, and communication overlap.

### Task 4: Implement baseline and joint schedulers [complete]

**Files:**
- Create: `xdsl/research/tasktile/schedule.py`
- Create: `tests/research/test_tasktile_schedule.py`

Expose `schedule_task_only`, `schedule_tile_only`, `schedule_joint`, and `enumerate_small_programs`. Use deterministic greedy decisions for normal programs and exhaustive enumeration only below a documented size limit. Return a schedule plus replay cost. Test that task-only and tile-only change only their intended decisions and that joint scheduling can select a different legal schedule.

### Task 5: Add artifact documentation and examples [complete]

**Files:**
- Create: `docs/research/tasktile-artifact.md`
- Create: `tests/data/tasktile/overlap.tasktile`

Document the IR schema, command examples, objective, legality assumptions, and the exact boundary between this prototype and native PyPTO. Include one small overlap-sensitive example with an expected replay result. Do not report hardware performance.

### Task 6: Draft the paper [complete]

**Files:**
- Create: `/home/georgios/workspace/hw-native-sys/pypto-3.0-notes/xdsl-pypto-ideas/tasktile-paper.md`

Write an introduction, system model, TaskTile IR, legality and replay model, scheduler algorithms, experimental protocol, limitations, related work, and artifact appendix. Every performance statement must be marked as a hypothesis until measured on Ascend hardware.

### Verification

Run:

```bash
pytest -q tests/research/test_tasktile_model.py tests/dialects/test_tasktile.py tests/research/test_tasktile_replay.py tests/research/test_tasktile_schedule.py
git diff --check
```

The current artifact is complete only when all tests pass and the paper states clearly that native PyPTO import and Ascend measurements remain future integration work.

### Task 7: Portable checkpoint boundary [complete]

**Files:**
- Create: `xdsl/research/tasktile/checkpoint.py`
- Create: `tests/research/test_tasktile_checkpoint.py`
- Modify: `docs/research/tasktile-artifact.md`

The checkpoint format is schema-versioned JSON with deterministic entity ordering. Import invokes the TaskTile model validators. This milestone does not claim native PyPTO import or export.

### Task 8: PyPTO adapter contract [complete]

**Files:**
- Create: `xdsl/research/tasktile/pypto_adapter.py`
- Create: `tests/research/test_tasktile_pypto_adapter.py`
- Modify: `docs/research/tasktile-artifact.md`

The adapter requires repository, revision, and pass provenance and wraps the portable TaskTile schema. It is intentionally independent of PyPTO imports, CANN, and hardware. The next milestone is implementing a native PyPTO exporter at a selected pass boundary.
