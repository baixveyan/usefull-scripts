from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

from wows_assistant.models import ActionIntent, ActionKind, Scene, WorldState


class TaskState(StrEnum):
    STOPPED = "stopped"
    WAIT_PORT = "wait_port"
    WAIT_QUEUE = "wait_queue"
    WAIT_LOADING = "wait_loading"
    IN_BATTLE = "in_battle"
    RESULT = "result"
    COMPLETE = "complete"
    ERROR = "error"


class TaskConfig(BaseModel):
    max_battles: int = Field(default=1, ge=1)
    max_retries: int = Field(default=2, ge=0)
    port_timeout_seconds: float = Field(default=120.0, gt=0)
    queue_timeout_seconds: float = Field(default=300.0, gt=0)
    loading_timeout_seconds: float = Field(default=300.0, gt=0)
    battle_timeout_seconds: float = Field(default=2400.0, gt=0)
    result_timeout_seconds: float = Field(default=180.0, gt=0)
    intent_ttl_seconds: float = Field(default=10.0, gt=0)


@dataclass(frozen=True)
class TaskTransition:
    previous: TaskState
    current: TaskState
    reason: str
    occurred_at: datetime


@dataclass(frozen=True)
class TaskDecision:
    state: TaskState
    transition: TaskTransition | None = None
    intents: tuple[ActionIntent, ...] = ()
    battles_completed: int = 0
    retries: int = 0


class TaskStateMachine:
    def __init__(self, config: TaskConfig | None = None) -> None:
        self.config = config or TaskConfig()
        self.state = TaskState.STOPPED
        self.entered_at: datetime | None = None
        self.battles_completed = 0
        self.retries = 0

    def start(self, now: datetime | None = None) -> TaskDecision:
        now = now or datetime.now(UTC)
        self.battles_completed = 0
        self.retries = 0
        transition = self._transition(TaskState.WAIT_PORT, "task_started", now)
        return self._decision(transition=transition)

    def stop(self, now: datetime | None = None) -> TaskDecision:
        now = now or datetime.now(UTC)
        transition = self._transition(TaskState.STOPPED, "task_stopped", now)
        return self._decision(transition=transition)

    def step(self, world: WorldState) -> TaskDecision:
        now = world.observed_at
        if self.state in {TaskState.STOPPED, TaskState.COMPLETE, TaskState.ERROR}:
            return self._decision()
        if self.entered_at is None:
            raise RuntimeError("state machine has not been started")

        elapsed = (now - self.entered_at).total_seconds()
        if elapsed < 0:
            return self._fail("observation_time_moved_backwards", now)

        if self.state is TaskState.WAIT_PORT:
            if world.scene is Scene.PORT:
                intent = self._intent(
                    ActionKind.MOUSE_CLICK,
                    "request_matchmaking",
                    now,
                    target="join_battle_button",
                )
                transition = self._transition(TaskState.WAIT_QUEUE, "port_ready", now)
                return self._decision(transition=transition, intents=(intent,))
            if elapsed > self.config.port_timeout_seconds:
                return self._fail("port_timeout", now)

        elif self.state is TaskState.WAIT_QUEUE:
            if world.scene is Scene.QUEUE:
                return self._decision()
            if world.scene is Scene.LOADING:
                transition = self._transition(TaskState.WAIT_LOADING, "loading_detected", now)
                return self._decision(transition=transition)
            if world.scene is Scene.BATTLE:
                transition = self._transition(TaskState.IN_BATTLE, "battle_detected", now)
                return self._decision(transition=transition)
            if elapsed > self.config.queue_timeout_seconds:
                return self._retry_or_fail("queue_timeout", now)

        elif self.state is TaskState.WAIT_LOADING:
            if world.scene is Scene.BATTLE:
                transition = self._transition(TaskState.IN_BATTLE, "battle_detected", now)
                return self._decision(transition=transition)
            if elapsed > self.config.loading_timeout_seconds:
                return self._retry_or_fail("loading_timeout", now)

        elif self.state is TaskState.IN_BATTLE:
            if world.scene is Scene.RESULT:
                intent = self._intent(
                    ActionKind.MOUSE_CLICK,
                    "return_to_port_after_result",
                    now,
                    target="return_to_port_button",
                )
                transition = self._transition(TaskState.RESULT, "result_detected", now)
                return self._decision(transition=transition, intents=(intent,))
            if world.scene is Scene.PORT:
                return self._finish_battle(now, "port_detected_after_battle")
            if elapsed > self.config.battle_timeout_seconds:
                return self._fail("battle_timeout", now)

        elif self.state is TaskState.RESULT:
            if world.scene is Scene.PORT:
                return self._finish_battle(now, "returned_to_port")
            if elapsed > self.config.result_timeout_seconds:
                return self._fail("result_timeout", now)

        return self._decision()

    def _finish_battle(self, now: datetime, reason: str) -> TaskDecision:
        self.battles_completed += 1
        self.retries = 0
        target = (
            TaskState.COMPLETE
            if self.battles_completed >= self.config.max_battles
            else TaskState.WAIT_PORT
        )
        transition = self._transition(target, reason, now)
        return self._decision(transition=transition)

    def _retry_or_fail(self, reason: str, now: datetime) -> TaskDecision:
        if self.retries >= self.config.max_retries:
            return self._fail(f"{reason}_retries_exhausted", now)
        self.retries += 1
        transition = self._transition(TaskState.WAIT_PORT, f"{reason}_retry", now)
        return self._decision(transition=transition)

    def _fail(self, reason: str, now: datetime) -> TaskDecision:
        transition = self._transition(TaskState.ERROR, reason, now)
        return self._decision(transition=transition)

    def _transition(self, target: TaskState, reason: str, now: datetime) -> TaskTransition:
        previous = self.state
        self.state = target
        self.entered_at = now
        return TaskTransition(previous, target, reason, now)

    def _intent(
        self,
        kind: ActionKind,
        reason: str,
        now: datetime,
        **parameters: object,
    ) -> ActionIntent:
        return ActionIntent(
            intent_id=str(uuid4()),
            created_at=now,
            expires_at=now + timedelta(seconds=self.config.intent_ttl_seconds),
            kind=kind,
            reason=reason,
            confidence=1.0,
            parameters=dict(parameters),
        )

    def _decision(
        self,
        *,
        transition: TaskTransition | None = None,
        intents: tuple[ActionIntent, ...] = (),
    ) -> TaskDecision:
        return TaskDecision(
            state=self.state,
            transition=transition,
            intents=intents,
            battles_completed=self.battles_completed,
            retries=self.retries,
        )
