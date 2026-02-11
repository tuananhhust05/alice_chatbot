from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.config import get_settings
from app.database import get_db

settings = get_settings()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


async def verify_google_token(token: str) -> dict:
    """Verify Google OAuth token and return user info."""
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )

        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Invalid issuer")

        return {
            "email": idinfo["email"],
            "name": idinfo.get("name", ""),
            "picture": idinfo.get("picture", ""),
            "google_id": idinfo["sub"],
        }
    except Exception as e:
        raise ValueError(f"Invalid Google token: {str(e)}")


async def get_or_create_user(user_info: dict) -> dict:
    """Get existing user or create new one. Uses email as primary key."""
    db = get_db()
    user = await db.users.find_one({"email": user_info["email"]})

    if user:
        # Update existing user info from Google
        await db.users.update_one(
            {"email": user_info["email"]},
            {"$set": {
                "name": user_info["name"],
                "picture": user_info["picture"],
                "google_id": user_info["google_id"],
                "updated_at": datetime.utcnow(),
            }}
        )
        user = await db.users.find_one({"email": user_info["email"]})
    else:
        # Create new user
        user_doc = {
            **user_info,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        result = await db.users.insert_one(user_doc)
        user = await db.users.find_one({"_id": result.inserted_id})

    return user


def create_access_token(email: str) -> str:
    """Create JWT access token with email as key."""
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str) -> dict:
    """Decode JWT and return current user by email."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return None

        db = get_db()
        user = await db.users.find_one({"email": email})
        return user
    except JWTError:
        return None
