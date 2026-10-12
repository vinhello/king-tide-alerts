import asyncio
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from app.services.healthcheck import HealthcheckSignal
from app.services.scheduler import _run_daily_check, run_daily_check


@pytest.mark.asyncio
async def test_daily_check_signals_start_then_success():
    with (
        patch(
            "app.services.scheduler.detect_and_store_king_tides",
            new_callable=AsyncMock,
        ) as detect,
        patch("app.services.scheduler.send_alerts", new_callable=AsyncMock) as send,
        patch(
            "app.services.scheduler.ping_healthcheck", new_callable=AsyncMock
        ) as ping,
    ):
        await run_daily_check(db=MagicMock())

    detect.assert_awaited_once()
    send.assert_awaited_once()
    assert ping.await_args_list == [
        call(HealthcheckSignal.START),
        call(HealthcheckSignal.SUCCESS),
    ]


@pytest.mark.asyncio
async def test_daily_check_signals_fail_and_reraises_on_error():
    with (
        patch(
            "app.services.scheduler.detect_and_store_king_tides",
            new_callable=AsyncMock,
            side_effect=RuntimeError("NOAA unreachable"),
        ),
        patch("app.services.scheduler.send_alerts", new_callable=AsyncMock) as send,
        patch(
            "app.services.scheduler.ping_healthcheck", new_callable=AsyncMock
        ) as ping,
    ):
        with pytest.raises(RuntimeError):
            await run_daily_check(db=MagicMock())

    send.assert_not_awaited()
    assert ping.await_args_list == [
        call(HealthcheckSignal.START),
        call(HealthcheckSignal.FAIL),
    ]


@pytest.mark.asyncio
async def test_daily_check_signals_fail_when_sending_alerts_errors():
    with (
        patch(
            "app.services.scheduler.detect_and_store_king_tides",
            new_callable=AsyncMock,
        ),
        patch(
            "app.services.scheduler.send_alerts",
            new_callable=AsyncMock,
            side_effect=RuntimeError("email provider down"),
        ),
        patch(
            "app.services.scheduler.ping_healthcheck", new_callable=AsyncMock
        ) as ping,
    ):
        with pytest.raises(RuntimeError):
            await run_daily_check(db=MagicMock())

    assert ping.await_args_list[-1] == call(HealthcheckSignal.FAIL)


def test_sync_wrapper_logs_failure_and_closes_session():
    db = MagicMock()
    try:
        with (
            patch("app.services.scheduler.SessionLocal", return_value=db),
            patch(
                "app.services.scheduler.run_daily_check",
                new_callable=AsyncMock,
                side_effect=RuntimeError("boom"),
            ),
        ):
            _run_daily_check()  # must not raise: APScheduler would log a crash
    finally:
        asyncio.set_event_loop(None)

    db.close.assert_called_once()


def test_sync_wrapper_runs_check_and_closes_session():
    db = MagicMock()
    try:
        with (
            patch("app.services.scheduler.SessionLocal", return_value=db),
            patch(
                "app.services.scheduler.run_daily_check", new_callable=AsyncMock
            ) as run,
        ):
            _run_daily_check()
    finally:
        asyncio.set_event_loop(None)

    run.assert_awaited_once_with(db)
    db.close.assert_called_once()
