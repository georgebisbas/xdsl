# TaskTile hardware handoff

This document begins only after the simulation artifact has passed. It does
not claim that Ascend hardware is available in the current environment.

## Pinned software boundary

- xDSL branch: `georgebisbas/tasktile-xdsl-pypto`
- PyPTO exporter branch: `georgebisbas/tasktile-xdsl-pypto`
- PyPTO exporter revision: `3b866d5ae`
- export boundary: `post:MaterializeValidShapeSymbols`
- simulation image: `pypto3-hw-native-sys:sim-xdsl-tasktile`
- verified image digest: `sha256:c3d417274cc6fc37bba818cdb89c4ece4522e7b172c39232d87c69a31d05e5eb`
- PTOAS: `v0.65`

The non-NPU fallback remains the simulation Dockerfile documented in
`tasktile-artifact.md`; do not substitute a host-side CMake build.

## Hardware run requirements

For each native, task-only, tile-only, and joint variant, preserve:

1. compiler/runtime/firmware revisions and flags;
2. tensor shapes, rank placement, clock/power mode, and warm-up policy;
3. correctness output and numerical tolerances;
4. generated PTO, orchestration, pass dumps, and failure logs;
5. repeated latency samples, profiler traces, synchronization stalls, engine
   overlap, memory traffic, peak on-chip memory, and compile time.

Compare distributions, not a single timing. Keep development and held-out
workloads separate, and do not convert replay or PTOAS acceptance into a device
speedup claim.

## Exit criteria

The hardware thesis is supported only if at least two shapes and two workload
classes reproduce the predicted mechanism, with correctness and memory-capacity
checks passing. Otherwise retire or narrow the performance claim while keeping
the compiler-analysis artifact and its negative results.
