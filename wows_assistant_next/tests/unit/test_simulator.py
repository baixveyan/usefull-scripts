from pathlib import Path

from wows_assistant.tasks.fsm import TaskState
from wows_assistant.tasks.simulator import TaskScenario, simulate_task


def test_full_cycle_scenario_finishes_with_dry_run_records() -> None:
    path = Path(__file__).parents[1] / "fixtures" / "scenarios" / "full_cycle.yaml"
    result = simulate_task(TaskScenario.load(path))
    assert result.final.state is TaskState.COMPLETE
    assert len(result.executions) == 2
    assert all(not record.executed for record in result.executions)
    assert all(record.status == "dry_run_only" for record in result.executions)

