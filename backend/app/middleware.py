from fastapi import Request
from fastapi.responses import JSONResponse
from app.services.auth import get_current_user
from app.services.admin_auth import verify_admin_token

# Exact-match public routes
EXACT_PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/files/limits",  # File limits info doesn't need auth
}

# Prefix-match public routes
PREFIX_PUBLIC_PATHS = [
    "/api/auth/",
    "/api/admin/login",
]


def is_public_path(path: str) -> bool:
    """Check if path is public (no auth required)."""
    if path in EXACT_PUBLIC_PATHS:
        return True
    return any(path.startswith(p) for p in PREFIX_PUBLIC_PATHS)


def is_admin_path(path: str) -> bool:
    """Check if path requires admin auth."""
    return path.startswith("/api/admin/") and path != "/api/admin/login"


async def auth_middleware(request: Request, call_next):
    """Middleware to verify JWT token from cookie — handles both user and admin auth."""
    path = request.url.path

    # Allow public routes
    if is_public_path(path):
        response = await call_next(request)
        return response

    # Admin routes — separate auth flow
    if is_admin_path(path):
        token = request.cookies.get("admin_token")
        if not token:
            # Also check Authorization header for admin
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]

        if not token or not verify_admin_token(token):
            return JSONResponse(
                status_code=401,
                content={"detail": "Admin authentication required"},
            )

        request.state.is_admin = True
        response = await call_next(request)
        return response

    # User routes — standard auth
    token = request.cookies.get("access_token")
    if not token:
        return JSONResponse(
            status_code=401,
            content={"detail": "Not authenticated"},
        )

    user = await get_current_user(token)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or expired token"},
        )

    request.state.user = user
    response = await call_next(request)
    return response
