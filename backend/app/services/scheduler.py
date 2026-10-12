import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.healthcheck import HealthcheckSignal, ping_healthcheck
from app.services.king_tide_detector import detect_and_store_king_tides, send_alerts

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


async def run_daily_check(db: Session) -> None:
    """Detect new events and send alerts, reporting to the dead man's switch.

    Signals: start before the work, success once both steps finish, fail if
    either raises. The exception is re-raised after the fail signal so the
    caller still logs it.
    """
    await ping_healthcheck(HealthcheckSignal.START)
    try:
        await detect_and_store_king_tides(db)
        await send_alerts(db)
    except Exception:
        await ping_healthcheck(HealthcheckSignal.FAIL)
        raise
    await ping_healthcheck(HealthcheckSignal.SUCCESS)


def _run_daily_check() -> None:
    """Synchronous wrapper for the async daily check, called by APScheduler."""
    logger.info("Running daily king tide check...")
    db = SessionLocal()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_daily_check(db))
    except Exception as e:
        logger.error(f"Daily king tide check failed: {e}")
    finally:
        loop.close()
        db.close()
    logger.info("Daily king tide check complete")


def start_scheduler() -> None:
    """Start the background scheduler with a daily cron job at 6 AM Pacific."""
    scheduler.add_job(
        _run_daily_check,
        "cron",
        hour=6,
        minute=0,
        timezone="America/Los_Angeles",
        id="daily_king_tide_check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — daily king tide check at 6 AM Pacific")


def stop_scheduler() -> None:
    """Shut down the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
