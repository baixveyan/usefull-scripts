from datetime import UTC, datetime, timedelta

from wows_assistant.models import Scene, WorldState
from wows_assistant.tasks.fsm import TaskConfig, TaskState, TaskStateMachine


def world(now: datetime, scene: Scene) -> WorldState:
    return WorldState(observed_at=now, scene=scene, confidence=1.0, stable_frames=3)


def test_full_task_cycle_only_produces_semantic_intents() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    machine = TaskStateMachine(TaskConfig(max_battles=1))
    assert machine.start(now).state is TaskState.WAIT_PORT

    join = machine.step(world(now + timedelta(seconds=1), Scene.PORT))
    assert join.state is TaskState.WAIT_QUEUE
    assert join.intents[0].parameters == {"target": "join_battle_button"}

    assert machine.step(world(now + timedelta(seconds=2), Scene.QUEUE)).state is TaskState.WAIT_QUEUE
    assert machine.step(world(now + timedelta(seconds=3), Scene.LOADING)).state is TaskState.WAIT_LOADING
    assert machine.step(world(now + timedelta(seconds=4), Scene.BATTLE)).state is TaskState.IN_BATTLE

    result = machine.step(world(now + timedelta(seconds=5), Scene.RESULT))
    assert result.state is TaskState.RESULT
    assert result.intents[0].parameters == {"target": "return_to_port_button"}

    complete = machine.step(world(now + timedelta(seconds=6), Scene.PORT))
    assert complete.state is TaskState.COMPLETE
    assert complete.battles_completed == 1


def test_queue_timeout_retries_then_fails() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    config = TaskConfig(queue_timeout_seconds=5, max_retries=1)
    machine = TaskStateMachine(config)
    machine.start(now)
    machine.step(world(now + timedelta(seconds=1), Scene.PORT))

    retry = machine.step(world(now + timedelta(seconds=7), Scene.PORT))
    assert retry.state is TaskState.WAIT_PORT
    assert retry.retries == 1

    machine.step(world(now + timedelta(seconds=8), Scene.PORT))
    failed = machine.step(world(now + timedelta(seconds=14), Scene.PORT))
    assert failed.state is TaskState.ERROR
    assert failed.transition is not None
    assert failed.transition.reason == "queue_timeout_retries_exhausted"

