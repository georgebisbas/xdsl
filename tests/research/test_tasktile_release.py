import json

from xdsl.research.tasktile.release import create_artifact


def test_release_writes_results_and_manifest(tmp_path) -> None:
    results, summary, manifest = create_artifact(tmp_path, xdsl_revision="xdsl123")
    assert results.exists()
    assert manifest.exists()
    assert summary.exists()
    assert len(json.loads(results.read_text())) == 25
    assert len(json.loads(summary.read_text())) == 5
    metadata = json.loads(manifest.read_text())
    assert metadata["xdsl_revision"] == "xdsl123"
    assert metadata["hardware"] == "unavailable"
