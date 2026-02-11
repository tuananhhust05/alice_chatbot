from fastapi import Request, HTTPException


async def get_current_user_dep(request: Request) -> dict:
    """Dependency to get current user from request state."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
