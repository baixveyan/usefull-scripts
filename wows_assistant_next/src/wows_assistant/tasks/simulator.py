from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from wows_assistant.actions.dry_run import DryRunExecutor, ExecutionRecord
from wows_assistant.models import Scene, WorldState
from wows_assistant.tasks.fsm import TaskConfig, TaskDecision, TaskStateMachine


class ScenarioFrame(BaseModel):
    scene: Scene
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    seconds_after_previous: float = Field(default=1.0, ge=0.0)
    repeat: int = Field(default=1, ge=1)


class TaskScenario(BaseModel):
    name: str
    task: TaskConfig = Field(default_factory=TaskConfig)
    frames: list[ScenarioFrame]

    @classmethod
    def load(cls, path: str | Path) -> TaskScenario:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(data)


@dataclass(frozen=True)
class SimulationResult:
    scenario: str
    decisions: tuple[TaskDecision, ...]
    executions: tuple[ExecutionRecord, ...]

    @property
    def final(self) -> TaskDecision:
        return self.decisions[-1]


def simulate_task(scenario: TaskScenario) -> SimulationResult:
    machine = TaskStateMachine(scenario.task)
    executor = DryRunExecutor()
    now = datetime(2026, 1, 1, tzinfo=UTC)
    decisions: list[TaskDecision] = [machine.start(now)]
    for scenario_frame in scenario.frames:
        for _ in range(scenario_frame.repeat):
            now += timedelta(seconds=scenario_frame.seconds_after_previous)
            world = WorldState(
                observed_at=now,
                scene=scenario_frame.scene,
                confidence=scenario_frame.confidence,
                stable_frames=scenario_frame.repeat,
            )
            decision = machine.step(world)
            decisions.append(decision)
            for intent in decision.intents:
                executor.submit(intent, now)
    return SimulationResult(scenario.name, tuple(decisions), tuple(executor.records))

