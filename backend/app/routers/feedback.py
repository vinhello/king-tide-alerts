from fastapi import APIRouter, HTTPException, Request

from app.rate_limit import limiter
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.feedback_stats import feedback_stats
from app.services.notification import EmailSendError, send_feedback

router = APIRouter(prefix="/api", tags=["feedback"])

# Per client address, then a cap shared by everyone as a backstop in case
# client addresses are ever not visible to the app.
FEEDBACK_PER_CLIENT_LIMIT = "3/hour;10/day"
FEEDBACK_GLOBAL_LIMIT = "60/hour"
SUCCESS_MESSAGE = "Thanks, your feedback has been sent."
FAILURE_MESSAGE = (
    "We couldn't send your message just now. Please try again in a few minutes."
)


def _global_key(request: Request) -> str:
    return "feedback-global"


@router.post("/feedback", response_model=FeedbackResponse)
@limiter.limit(FEEDBACK_PER_CLIENT_LIMIT)
@limiter.limit(FEEDBACK_GLOBAL_LIMIT, key_func=_global_key)
async def submit_feedback(request: Request, data: FeedbackRequest):
    # Honeypot filled in: almost certainly a bot. Report success, send nothing.
    if data.website:
        feedback_stats.record_bot_dropped()
        return FeedbackResponse(message=SUCCESS_MESSAGE)

    # Sent before answering, so a visitor whose message did not go out is told
    # so instead of being thanked for an email that never left.
    try:
        await send_feedback(
            message=data.message,
            subject=data.subject,
            reply_email=data.email,
        )
    except EmailSendError as e:
        feedback_stats.record_failure(str(e))
        raise HTTPException(status_code=503, detail=FAILURE_MESSAGE)

    feedback_stats.record_sent()
    return FeedbackResponse(message=SUCCESS_MESSAGE)
