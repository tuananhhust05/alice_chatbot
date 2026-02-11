"""Admin authentication — completely separate from user auth."""
from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.config import get_settings

settings = get_settings()

ADMIN_ALGORITHM = "HS256"
ADMIN_TOKEN_EXPIRE_HOURS = 12


def verify_admin_credentials(username: str, password: str) -> bool:
    """Check admin credentials from env config."""
    return username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD


def create_admin_token() -> str:
    """Create admin JWT — uses separate secret key from user tokens."""
    expire = datetime.utcnow() + timedelta(hours=ADMIN_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": "admin",
        "role": "admin",
        "exp": expire,
    }
    return jwt.encode(payload, settings.ADMIN_SECRET_KEY, algorithm=ADMIN_ALGORITHM)


def verify_admin_token(token: str) -> bool:
    """Verify admin JWT token."""
    try:
        payload = jwt.decode(token, settings.ADMIN_SECRET_KEY, algorithms=[ADMIN_ALGORITHM])
        return payload.get("role") == "admin"
    except JWTError:
        return False
