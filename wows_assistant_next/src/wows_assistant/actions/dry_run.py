from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from wows_assistant.models import ActionIntent


@dataclass(frozen=True)
class ExecutionRecord:
    intent: ActionIntent
    observed_at: datetime
    executed: bool
    status: str


class DryRunExecutor:
    """Records intent decisions and deliberately performs no external action."""

    def __init__(self) -> None:
        self.records: list[ExecutionRecord] = []

    def submit(self, intent: ActionIntent, now: datetime | None = None) -> ExecutionRecord:
        record = ExecutionRecord(
            intent=intent,
            observed_at=now or datetime.now(UTC),
            executed=False,
            status="dry_run_only",
        )
        self.records.append(record)
        return record

