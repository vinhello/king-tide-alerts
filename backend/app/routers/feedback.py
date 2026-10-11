from fastapi import APIRouter, BackgroundTasks, Request

from app.rate_limit import limiter
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.notification import send_feedback

router = APIRouter(prefix="/api", tags=["feedback"])

# Per client address, then a cap shared by everyone as a backstop in case
# client addresses are ever not visible to the app.
FEEDBACK_PER_CLIENT_LIMIT = "3/hour;10/day"
FEEDBACK_GLOBAL_LIMIT = "60/hour"
SUCCESS_MESSAGE = "Thanks, your feedback has been sent."


def _global_key(request: Request) -> str:
    return "feedback-global"


@router.post("/feedback", response_model=FeedbackResponse)
@limiter.limit(FEEDBACK_PER_CLIENT_LIMIT)
@limiter.limit(FEEDBACK_GLOBAL_LIMIT, key_func=_global_key)
async def submit_feedback(
    request: Request,
    data: FeedbackRequest,
    background_tasks: BackgroundTasks,
):
    # Honeypot filled in: almost certainly a bot. Report success, send nothing.
    if data.website:
        return FeedbackResponse(message=SUCCESS_MESSAGE)

    background_tasks.add_task(
        send_feedback,
        message=data.message,
        subject=data.subject,
        reply_email=data.email,
    )
    return FeedbackResponse(message=SUCCESS_MESSAGE)
