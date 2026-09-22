import json

from xdsl.research.tasktile.experiment import main


def test_experiment_cli_emits_json(capsys) -> None:
    assert main(["--sync-cost", "3", "--transfer-cost-per-byte", "0.5"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload) == 10
    assert all(row["metrics"]["synchronization_stall"] >= 0 for row in payload)
