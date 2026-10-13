import logging

import resend
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.services import email_events

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/resend")
async def resend_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive delivery outcomes from Resend.

    Every request is checked against the webhook signing secret before any
    of it is read. A verified event is recorded once (Resend retries reuse
    the svix-id), and a hard bounce or spam complaint stops all further
    sending to that subscriber. Nothing here sends email.
    """
    if not settings.RESEND_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook not configured")

    # The signature covers the raw body; it must not be re-serialized.
    payload = (await request.body()).decode("utf-8", errors="replace")
    headers = {
        "id": request.headers.get("svix-id", ""),
        "timestamp": request.headers.get("svix-timestamp", ""),
        "signature": request.headers.get("svix-signature", ""),
    }
    try:
        event = resend.Webhooks.verify(
            {
                "payload": payload,
                "headers": headers,
                "webhook_secret": settings.RESEND_WEBHOOK_SECRET,
            }
        )
    except ValueError as e:
        logger.warning(f"Rejected Resend webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    result = email_events.record_event(db, svix_id=headers["id"], event=event)
    return {"status": "ok", "result": result}
