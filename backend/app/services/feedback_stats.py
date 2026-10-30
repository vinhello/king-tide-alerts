"""In-process counters for the feedback form, shown in admin health.

They live in memory on purpose: a feedback email has no subscriber row to
hang a durable record on, and the point is to notice a failing form, not to
keep history. Counts restart with the backend; `since` says when that was.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

MAX_REASON_LENGTH = 200


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class FeedbackStats:
    since: datetime = field(default_factory=_now)
    sent: int = 0
    failed: int = 0
    bot_dropped: int = 0
    last_failure_at: Optional[datetime] = None
    last_failure_reason: Optional[str] = None

    def record_sent(self) -> None:
        self.sent += 1

    def record_failure(self, reason: str) -> None:
        self.failed += 1
        self.last_failure_at = _now()
        self.last_failure_reason = reason[:MAX_REASON_LENGTH]

    def record_bot_dropped(self) -> None:
        self.bot_dropped += 1

    def snapshot(self) -> dict:
        return asdict(self)

    def reset(self) -> None:
        self.since = _now()
        self.sent = 0
        self.failed = 0
        self.bot_dropped = 0
        self.last_failure_at = None
        self.last_failure_reason = None


feedback_stats = FeedbackStats()
