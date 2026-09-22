"""Reproducibility manifest for TaskTile experiment artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from .checkpoint import SCHEMA_VERSION
from .replay import ReplayConfig


@dataclass(frozen=True)
class ArtifactManifest:
    xdsl_revision: str
    pypto_revision: str | None = None
    tasktile_schema_version: int = SCHEMA_VERSION
    replay_config: ReplayConfig = field(default_factory=ReplayConfig)
    hardware: str = "unavailable"
    simulation_image: str | None = None
    test_command: str = "PYTHONPATH=. pytest"

    def __post_init__(self) -> None:
        if not self.xdsl_revision:
            raise ValueError("xdsl_revision must be non-empty")
        if self.tasktile_schema_version != SCHEMA_VERSION:
            raise ValueError("manifest schema must match TaskTile schema")

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["replay_config"] = asdict(self.replay_config)
        return data


def dumps(manifest: ArtifactManifest) -> str:
    return json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n"
