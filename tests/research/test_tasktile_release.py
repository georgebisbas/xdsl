import json

from xdsl.research.tasktile.release import create_artifact


def test_release_writes_results_and_manifest(tmp_path) -> None:
    results, summary, manifest = create_artifact(
        tmp_path,
        xdsl_revision="xdsl123",
        simulation_image="sim@test",
    )
    assert results.exists()
    assert manifest.exists()
    assert summary.exists()
    ablations = tmp_path / "tasktile-ablations.json"
    assert ablations.exists()
    assert len(json.loads(ablations.read_text())) == 15
    traces = tmp_path / "tasktile-traces.json"
    assert traces.exists()
    assert set(json.loads(traces.read_text())) == {
        "overlap",
        "independent",
        "fanout",
        "collective",
        "contention",
    }
    assert len(json.loads(results.read_text())) == 25
    summary_rows = json.loads(summary.read_text())
    assert len(summary_rows) == 5
    assert all("joint_binding_changes" in row for row in summary_rows)
    assert any(row["joint_binding_changes"] > 0 for row in summary_rows)
    metadata = json.loads(manifest.read_text())
    assert metadata["xdsl_revision"] == "xdsl123"
    assert metadata["hardware"] == "unavailable"
    assert metadata["simulation_image"] == "sim@test"
