from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.king_tide_event import KingTideEvent
from app.models.notification_sent import NotificationSent
from app.schemas.tide import (
    CurrentTideStatus,
    HistoryEvent,
    HistoryResponse,
    TidePrediction,
    UpcomingTidesResponse,
)
from app.services.ics_generator import generate_ics
from app.services.noaa import (
    fetch_current_water_level,
    fetch_hourly_tide_predictions,
    fetch_next_high_tide,
    get_king_tides,
)

router = APIRouter(prefix="/api/tides", tags=["tides"])


@router.get("/upcoming", response_model=UpcomingTidesResponse)
async def upcoming_tides(days: int = Query(default=14, ge=1, le=30)):
    predictions = await fetch_hourly_tide_predictions(days_ahead=days)

    tide_predictions = [
        TidePrediction(
            datetime=p["datetime"],
            height=p["height"],
            is_king_tide=p["height"] >= settings.KING_TIDE_HEIGHT,
        )
        for p in predictions
    ]

    return UpcomingTidesResponse(
        predictions=tide_predictions,
        threshold=settings.KING_TIDE_THRESHOLD,
        king_tide_height=settings.KING_TIDE_HEIGHT,
        station_id=settings.NOAA_STATION_ID,
    )


@router.get("/history", response_model=HistoryResponse)
async def tide_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    filter: Literal["all", "upcoming", "past"] = Query("all"),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    notification_count = func.count(NotificationSent.id).label("notifications_sent")
    query = (
        db.query(KingTideEvent, notification_count)
        .outerjoin(
            NotificationSent,
            NotificationSent.king_tide_event_id == KingTideEvent.id,
        )
        .group_by(KingTideEvent.id)
    )

    if filter == "upcoming":
        query = query.filter(KingTideEvent.event_datetime >= now)
    elif filter == "past":
        query = query.filter(KingTideEvent.event_datetime < now)

    total = query.count()

    rows = (
        query.order_by(KingTideEvent.event_datetime.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    events = [
        HistoryEvent(
            id=str(event.id),
            event_datetime=event.event_datetime.isoformat(),
            predicted_height=event.predicted_height,
            is_king_tide=event.predicted_height >= settings.KING_TIDE_HEIGHT,
            seven_day_alert_sent=event.seven_day_alert_sent,
            forty_eight_hour_alert_sent=event.forty_eight_hour_alert_sent,
            notifications_sent=count,
        )
        for event, count in rows
    ]

    return HistoryResponse(
        events=events,
        total=total,
        threshold=settings.KING_TIDE_THRESHOLD,
        king_tide_height=settings.KING_TIDE_HEIGHT,
    )


@router.get("/calendar.ics")
async def tide_calendar(
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    cutoff = now.replace(tzinfo=timezone.utc)
    end = now + timedelta(days=days)

    db_events = (
        db.query(KingTideEvent)
        .filter(
            KingTideEvent.event_datetime >= cutoff,
            KingTideEvent.event_datetime <= end,
        )
        .order_by(KingTideEvent.event_datetime)
        .all()
    )

    if db_events:
        ics_events = [
            {
                "event_datetime": event.event_datetime,
                "predicted_height": event.predicted_height,
            }
            for event in db_events
        ]
    else:
        noaa_tides = await get_king_tides(days_ahead=days)
        ics_events = []
        for tide in noaa_tides:
            try:
                dt = datetime.strptime(tide["datetime"], "%Y-%m-%d %H:%M").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                dt = datetime.fromisoformat(tide["datetime"])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            ics_events.append(
                {
                    "event_datetime": dt,
                    "predicted_height": tide["height"],
                }
            )

    ics_content = generate_ics(ics_events, station_id=settings.NOAA_STATION_ID)

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=king-tide-alerts.ics"},
    )


@router.get("/current", response_model=CurrentTideStatus)
async def current_tide():
    current = await fetch_current_water_level()
    if current is None:
        raise HTTPException(
            status_code=503, detail="Unable to fetch current conditions"
        )

    next_high = await fetch_next_high_tide()

    height = current["height"]
    if height >= settings.KING_TIDE_THRESHOLD:
        status = "flooded"
    elif height >= settings.KING_TIDE_THRESHOLD - 1.0:
        status = "caution"
    else:
        status = "safe"

    hours_until_high_tide = None
    next_high_tide_time = None
    next_high_tide_height = None

    if next_high is not None:
        next_high_tide_time = next_high["datetime"]
        next_high_tide_height = next_high["height"]

        try:
            # NOAA returns local time strings; compare as naive datetimes
            next_dt = datetime.strptime(next_high["datetime"], "%Y-%m-%d %H:%M")
            now_str = current["timestamp"]
            now_dt = datetime.strptime(now_str, "%Y-%m-%d %H:%M")
            diff = (next_dt - now_dt).total_seconds() / 3600
            hours_until_high_tide = round(max(diff, 0), 1)
        except (ValueError, TypeError):
            pass

    return CurrentTideStatus(
        current_height=height,
        current_time=current["timestamp"],
        next_high_tide_time=next_high_tide_time,
        next_high_tide_height=next_high_tide_height,
        hours_until_high_tide=hours_until_high_tide,
        status=status,
        threshold=settings.KING_TIDE_THRESHOLD,
    )
