import json

import pytest

from xdsl.research.tasktile.manifest import ArtifactManifest, dumps
from xdsl.research.tasktile.replay import ReplayConfig


def test_manifest_is_deterministic_and_records_calibration() -> None:
    manifest = ArtifactManifest(
        "xdsl123", "pypto456", replay_config=ReplayConfig(3, 0.5),
        simulation_image="pypto3-hw-native-sys:sim-xdsl-tasktile@sha256:test",
    )
    payload = dumps(manifest)
    data = json.loads(payload)
    assert data["tasktile_schema_version"] == 1
    assert data["replay_config"] == {
        "synchronization_cost": 3,
        "transfer_cost_per_byte": 0.5,
    }
    assert data["simulation_image"].endswith("sha256:test")
    assert dumps(manifest) == payload


def test_manifest_rejects_missing_revision() -> None:
    with pytest.raises(ValueError, match="xdsl_revision"):
        ArtifactManifest("")
