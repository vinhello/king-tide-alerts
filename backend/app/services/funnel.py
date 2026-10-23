"""Signup-to-delivery funnel for the admin page.

Read-only. The tables involved hold hundreds of rows, so the numbers are
computed in Python over plain rows; that keeps SQLite tests and Postgres in
agreement and avoids dialect-specific date arithmetic.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from statistics import median
from urllib.parse import urlparse

from app.models.email_event import EmailEventType
from app.models.notification_sent import NotificationType

NOT_RECORDED = "(not recorded)"
DIRECT = "direct"
WEEKS = 12
MAX_RUNS = 12


@dataclass(frozen=True)
class SubscriberRow:
    created_at: datetime
    confirmed: bool
    confirmed_at: datetime | None
    unsubscribed_at: datetime | None
    utm_source: str | None
    referrer: str | None
    landing_path: str | None
    nudged_at: datetime | None  # first confirmation reminder, if any


@dataclass(frozen=True)
class SendRow:
    notification_type: NotificationType
    sent_at: datetime
    outcomes: frozenset[EmailEventType]


@dataclass(frozen=True)
class Stage:
    signups: int
    confirmed: int
    confirmation_rate: float
    median_hours_to_confirm: float | None
    unsubscribed: int
    nudged: int
    confirmed_after_nudge: int


@dataclass(frozen=True)
class SourceCount:
    source: str
    signups: int
    confirmed: int


@dataclass(frozen=True)
class WeekCount:
    week_start: str
    signups: int
    confirmed: int
    unsubscribed: int


@dataclass(frozen=True)
class RunCount:
    date: str
    notification_type: str
    sent: int
    delivered: int
    bounced: int
    complained: int
    no_outcome: int


def aware(value: datetime | None) -> datetime | None:
    """SQLite hands back naive datetimes; Postgres aware ones. Compare as UTC."""
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=timezone.utc)


def aware_required(value: datetime) -> datetime:
    """Same as aware() for a column that is never null."""
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def source_label(utm_source: str | None, referrer: str | None, landing_path: str | None) -> str:
    """Where a signup came from, as the admin page groups it."""
    if utm_source and utm_source.strip():
        return utm_source.strip().lower()
    if referrer and referrer.strip():
        host = urlparse(referrer.strip()).netloc or referrer.strip()
        host = host.lower()
        return host[4:] if host.startswith("www.") else host
    if landing_path is None:
        # Rows from before the signup source was captured at all.
        return NOT_RECORDED
    return DIRECT


def ever_confirmed(row: SubscriberRow) -> bool:
    # An unsubscribe clears the confirmed flag but keeps confirmed_at.
    return bool(row.confirmed) or row.confirmed_at is not None


def stage(rows: list[SubscriberRow], since: datetime | None) -> Stage:
    """Funnel numbers for signups since a moment (None = all time).

    Unsubscribes and nudges are counted by when they happened in the same
    window, across all subscribers, since churn is not tied to signup date.
    """
    def in_window(moment: datetime | None) -> bool:
        return moment is not None and (since is None or moment >= since)

    cohort = [r for r in rows if in_window(r.created_at)]
    confirmed = [r for r in cohort if ever_confirmed(r)]
    hours = [
        (r.confirmed_at - r.created_at).total_seconds() / 3600
        for r in confirmed
        if r.confirmed_at is not None and r.confirmed_at >= r.created_at
    ]
    nudged = [r for r in rows if in_window(r.nudged_at)]
    converted = [
        r for r in nudged
        if r.confirmed_at is not None and r.nudged_at is not None and r.confirmed_at > r.nudged_at
    ]
    return Stage(
        signups=len(cohort),
        confirmed=len(confirmed),
        confirmation_rate=round(len(confirmed) / len(cohort), 3) if cohort else 0.0,
        median_hours_to_confirm=round(median(hours), 1) if hours else None,
        unsubscribed=sum(1 for r in rows if in_window(r.unsubscribed_at)),
        nudged=len(nudged),
        confirmed_after_nudge=len(converted),
    )


def by_source(rows: list[SubscriberRow]) -> list[SourceCount]:
    counts: dict[str, list[int]] = {}
    for r in rows:
        label = source_label(r.utm_source, r.referrer, r.landing_path)
        entry = counts.setdefault(label, [0, 0])
        entry[0] += 1
        if ever_confirmed(r):
            entry[1] += 1
    ordered = sorted(counts.items(), key=lambda item: (-item[1][0], item[0]))
    return [SourceCount(source=k, signups=v[0], confirmed=v[1]) for k, v in ordered]


def _week_start(moment: datetime) -> date:
    day = moment.date()
    return day - timedelta(days=day.weekday())


def weekly(rows: list[SubscriberRow], now: datetime, weeks: int = WEEKS) -> list[WeekCount]:
    """One entry per week for the trailing window, zeros included."""
    first = _week_start(now) - timedelta(weeks=weeks - 1)
    buckets: dict[date, list[int]] = {
        first + timedelta(weeks=i): [0, 0, 0] for i in range(weeks)
    }
    for r in rows:
        for index, moment in enumerate((r.created_at, r.confirmed_at, r.unsubscribed_at)):
            if moment is None:
                continue
            week = _week_start(moment)
            if week in buckets:
                buckets[week][index] += 1
    return [
        WeekCount(week_start=week.isoformat(), signups=v[0], confirmed=v[1], unsubscribed=v[2])
        for week, v in sorted(buckets.items())
    ]


def runs(sends: list[SendRow], limit: int = MAX_RUNS) -> list[RunCount]:
    """Delivery outcome per alert run (one row per day and alert type), newest first."""
    grouped: dict[tuple[str, str], list[SendRow]] = {}
    for s in sends:
        if s.notification_type is NotificationType.CONFIRMATION:
            continue
        key = (s.sent_at.date().isoformat(), s.notification_type.value)
        grouped.setdefault(key, []).append(s)
    result = []
    for (day, kind), items in sorted(grouped.items(), reverse=True)[:limit]:
        result.append(
            RunCount(
                date=day,
                notification_type=kind,
                sent=len(items),
                delivered=sum(1 for s in items if EmailEventType.DELIVERED in s.outcomes),
                bounced=sum(1 for s in items if EmailEventType.BOUNCED in s.outcomes),
                complained=sum(1 for s in items if EmailEventType.COMPLAINED in s.outcomes),
                no_outcome=sum(1 for s in items if not s.outcomes),
            )
        )
    return result
