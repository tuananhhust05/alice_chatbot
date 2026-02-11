from fastapi import APIRouter, HTTPException, Response, Request
from app.models.user import GoogleTokenPayload, UserResponse
from app.services.auth import verify_google_token, get_or_create_user, create_access_token, get_current_user
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/google", response_model=UserResponse)
async def google_login(payload: GoogleTokenPayload, response: Response):
    """Login with Google OAuth token."""
    try:
        user_info = await verify_google_token(payload.credential)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user = await get_or_create_user(user_info)
    token = create_access_token(user["email"])

    # Set token as httpOnly cookie with configurable security
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.SECURE_COOKIES,  # Configurable - True in production
        samesite="lax" if not settings.SECURE_COOKIES else "strict",
        max_age=7 * 24 * 60 * 60,  # 7 days
        path="/",
    )

    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        name=user["name"],
        picture=user.get("picture"),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(request: Request):
    """Get current user info from cookie."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = await get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        name=user["name"],
        picture=user.get("picture"),
    )


@router.post("/logout")
async def logout(response: Response):
    """Logout - clear cookie."""
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Logged out successfully"}
