from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_user_dep
from app.models.chat import StreamResponse
from app.services.redis_client import get_result, delete_result

router = APIRouter(prefix="/api", tags=["stream"])


@router.get("/stream", response_model=StreamResponse)
async def poll_result(
    request_id: str = Query(..., description="Request ID to poll for result"),
    user: dict = Depends(get_current_user_dep),
):
    """
    Poll for streaming result by request_id.
    - status="processing": not started yet
    - status="streaming", finished=0: LLM is generating, reply has partial content
    - status="completed", finished=1: done, reply has full content
    - status="error", finished=1: error occurred

    When finished=1, backend deletes the result from Redis (cleanup).
    """
    result = await get_result(request_id)

    if not result:
        return StreamResponse(status="processing")

    # If finished, clean up from Redis
    if result.get("finished") == 1:
        await delete_result(request_id)

    return StreamResponse(**result)
