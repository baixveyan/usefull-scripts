from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Self, TextIO

from wows_assistant.models import (
    ActionIntent,
    EventEnvelope,
    PerceptionResult,
    SerializableEvent,
    WorldState,
    event_type_for,
)

EVENT_MODELS = {
    "perception": PerceptionResult,
    "world_state": WorldState,
    "action_intent": ActionIntent,
}


class JsonlRecorder:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._stream: TextIO | None = None

    def __enter__(self) -> Self:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._stream = self.path.open("a", encoding="utf-8", newline="\n")
        return self

    def write(self, event: SerializableEvent) -> None:
        if self._stream is None:
            raise RuntimeError("recorder must be used as a context manager")
        envelope = EventEnvelope(
            event_type=event_type_for(event),
            payload=event.model_dump(mode="json"),
        )
        self._stream.write(envelope.model_dump_json() + "\n")
        self._stream.flush()

    def __exit__(self, *_: object) -> None:
        if self._stream is not None:
            self._stream.close()
            self._stream = None


def replay_events(path: str | Path) -> Iterator[SerializableEvent]:
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                envelope = EventEnvelope.model_validate_json(line)
                model = EVENT_MODELS[envelope.event_type]
                yield model.model_validate(envelope.payload)
            except (ValueError, KeyError, json.JSONDecodeError) as exc:
                raise ValueError(f"无效回放记录，第 {line_number} 行: {exc}") from exc


def summarize_replay(path: str | Path) -> dict[str, int]:
    counts = Counter(event_type_for(event) for event in replay_events(path))
    return dict(sorted(counts.items()))
