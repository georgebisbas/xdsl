"""Create a self-contained TaskTile experiment artifact directory."""

from __future__ import annotations

import argparse
from pathlib import Path

from .experiment import dump_synthetic_experiment
from .manifest import ArtifactManifest
from .manifest import dumps as dump_manifest
from .replay import ReplayConfig


def create_artifact(
    output: Path,
    *,
    xdsl_revision: str,
    pypto_revision: str | None = None,
    config: ReplayConfig | None = None,
    hardware: str = "unavailable",
) -> tuple[Path, Path]:
    output.mkdir(parents=True, exist_ok=True)
    config = config or ReplayConfig()
    results_path = output / "tasktile-results.json"
    manifest_path = output / "manifest.json"
    results_path.write_text(dump_synthetic_experiment(config), encoding="utf-8")
    manifest_path.write_text(
        dump_manifest(
            ArtifactManifest(
                xdsl_revision,
                pypto_revision,
                replay_config=config,
                hardware=hardware,
                test_command="PYTHONPATH=. pytest",
            )
        ),
        encoding="utf-8",
    )
    return results_path, manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a TaskTile experiment artifact"
    )
    parser.add_argument("output", type=Path)
    parser.add_argument("--xdsl-revision", required=True)
    parser.add_argument("--pypto-revision")
    parser.add_argument("--sync-cost", type=int, default=1)
    parser.add_argument("--transfer-cost-per-byte", type=float, default=0.0)
    parser.add_argument("--hardware", default="unavailable")
    args = parser.parse_args(argv)
    create_artifact(
        args.output,
        xdsl_revision=args.xdsl_revision,
        pypto_revision=args.pypto_revision,
        config=ReplayConfig(args.sync_cost, args.transfer_cost_per_byte),
        hardware=args.hardware,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
