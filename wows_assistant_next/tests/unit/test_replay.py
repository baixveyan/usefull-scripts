from datetime import UTC, datetime
from pathlib import Path

from wows_assistant.models import ActionIntent, ActionKind, Scene, WorldState
from wows_assistant.replay import JsonlRecorder, replay_events, summarize_replay


def test_jsonl_record_and_replay(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    state = WorldState(observed_at=now, scene=Scene.PORT, confidence=0.95, stable_frames=3)
    intent = ActionIntent(
        intent_id="intent-1",
        created_at=now,
        kind=ActionKind.NOOP,
        reason="offline test",
        confidence=1.0,
    )
    path = tmp_path / "events.jsonl"

    with JsonlRecorder(path) as recorder:
        recorder.write(state)
        recorder.write(intent)

    assert list(replay_events(path)) == [state, intent]
    assert summarize_replay(path) == {"action_intent": 1, "world_state": 1}

