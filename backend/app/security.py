"""
Security middleware and utilities for backend.

Implements:
1. Redis-based Rate limiting with per-endpoint configuration
2. Input validation
3. Security headers (including CSP)
4. Request logging
5. IP tracking and blacklisting
6. CSRF protection
7. Brute-force protection for admin login
"""
import re
import time
import hashlib
import secrets
from typing import Optional, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import get_settings

settings = get_settings()


# ===== RATE LIMITING CONSTANTS =====
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 100  # requests per window

# ===== IN-MEMORY RATE LIMITING (for testing/fallback) =====
_rate_limit_store = {}  # key -> list of timestamps


def check_rate_limit(key: str, max_requests: int = RATE_LIMIT_MAX_REQUESTS, window: int = RATE_LIMIT_WINDOW) -> bool:
    """
    Simple in-memory rate limiter (for testing or fallback when Redis unavailable).
    Returns True if request is allowed, False if rate limited.
    """
    now = time.time()
    window_start = now - window
    
    # Get or create list of timestamps for this key
    if key not in _rate_limit_store:
        _rate_limit_store[key] = []
    
    # Remove old timestamps outside window
    _rate_limit_store[key] = [ts for ts in _rate_limit_store[key] if ts > window_start]
    
    # Check if under limit
    if len(_rate_limit_store[key]) >= max_requests:
        return False
    
    # Add current timestamp
    _rate_limit_store[key].append(now)
    return True


# ===== REDIS-BASED RATE LIMITING =====
# Redis client will be initialized from redis_client module
redis_client = None


def get_redis_client():
    """Get Redis client - lazy import to avoid circular dependency."""
    global redis_client
    if redis_client is None:
        from app.services.redis_client import redis_client as rc
        redis_client = rc
    return redis_client


async def check_rate_limit_redis(key: str, max_requests: int, window_seconds: int = 60) -> Tuple[bool, int]:
    """
    Redis-based sliding window rate limiter.
    Returns: (is_allowed, remaining_requests)
    """
    rc = get_redis_client()
    if rc is None:
        # Fallback: allow if Redis not available
        return True, max_requests
    
    try:
        now = int(time.time())
        window_start = now - window_seconds
        rate_key = f"ratelimit:{key}"
        
        # Use Redis pipeline for atomic operations
        pipe = rc.pipeline()
        
        # Remove old entries outside window
        pipe.zremrangebyscore(rate_key, 0, window_start)
        
        # Count current requests in window
        pipe.zcard(rate_key)
        
        # Add current request with timestamp as score
        pipe.zadd(rate_key, {f"{now}:{secrets.token_hex(4)}": now})
        
        # Set expiry on the key
        pipe.expire(rate_key, window_seconds + 10)
        
        results = await pipe.execute()
        current_count = results[1]
        
        if current_count >= max_requests:
            # Remove the request we just added since it's over limit
            return False, 0
        
        return True, max_requests - current_count - 1
    except Exception as e:
        print(f"[Security] Rate limit Redis error: {e}")
        # Fallback: allow if Redis error
        return True, max_requests


def get_client_ip(request: Request) -> str:
    """Extract client IP from request with multiple header support."""
    # Check various proxy headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first (client) IP from the chain
        return forwarded.split(",")[0].strip()
    
    # Check other common headers
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    cf_ip = request.headers.get("CF-Connecting-IP")  # Cloudflare
    if cf_ip:
        return cf_ip.strip()
    
    return request.client.host if request.client else "unknown"


# ===== IP BLACKLIST/WHITELIST =====
async def is_ip_blacklisted(ip: str) -> bool:
    """Check if IP is blacklisted."""
    rc = get_redis_client()
    if rc is None:
        return False
    try:
        return await rc.sismember("ip:blacklist", ip)
    except Exception:
        return False


async def blacklist_ip(ip: str, reason: str = "", ttl_seconds: int = 3600):
    """Add IP to blacklist with optional TTL."""
    rc = get_redis_client()
    if rc is None:
        return
    try:
        await rc.sadd("ip:blacklist", ip)
        if ttl_seconds > 0:
            # Store with expiry
            await rc.setex(f"ip:blacklist:{ip}", ttl_seconds, reason or "blocked")
    except Exception as e:
        print(f"[Security] Blacklist error: {e}")


async def unblacklist_ip(ip: str):
    """Remove IP from blacklist."""
    rc = get_redis_client()
    if rc is None:
        return
    try:
        await rc.srem("ip:blacklist", ip)
        await rc.delete(f"ip:blacklist:{ip}")
    except Exception as e:
        print(f"[Security] Unblacklist error: {e}")


async def get_blacklisted_ips() -> list:
    """Get all blacklisted IPs."""
    rc = get_redis_client()
    if rc is None:
        return []
    try:
        return list(await rc.smembers("ip:blacklist"))
    except Exception:
        return []


# ===== BRUTE-FORCE PROTECTION =====
async def check_login_attempts(ip: str, username: str) -> Tuple[bool, int]:
    """
    Check if login is allowed based on failed attempts.
    Returns: (is_allowed, attempts_remaining)
    """
    rc = get_redis_client()
    if rc is None:
        return True, settings.ADMIN_LOGIN_MAX_ATTEMPTS
    
    try:
        key = f"login:attempts:{ip}:{username}"
        attempts = await rc.get(key)
        attempts = int(attempts) if attempts else 0
        
        if attempts >= settings.ADMIN_LOGIN_MAX_ATTEMPTS:
            return False, 0
        
        return True, settings.ADMIN_LOGIN_MAX_ATTEMPTS - attempts
    except Exception:
        return True, settings.ADMIN_LOGIN_MAX_ATTEMPTS


async def record_failed_login(ip: str, username: str):
    """Record a failed login attempt."""
    rc = get_redis_client()
    if rc is None:
        return
    try:
        key = f"login:attempts:{ip}:{username}"
        pipe = rc.pipeline()
        pipe.incr(key)
        pipe.expire(key, settings.ADMIN_LOGIN_LOCKOUT_MINUTES * 60)
        await pipe.execute()
    except Exception as e:
        print(f"[Security] Record login attempt error: {e}")


async def clear_login_attempts(ip: str, username: str):
    """Clear login attempts after successful login."""
    rc = get_redis_client()
    if rc is None:
        return
    try:
        await rc.delete(f"login:attempts:{ip}:{username}")
    except Exception:
        pass


# ===== CSRF PROTECTION =====
def generate_csrf_token(session_id: str) -> str:
    """Generate CSRF token based on session."""
    data = f"{session_id}:{settings.CSRF_SECRET}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]


def verify_csrf_token(token: str, session_id: str) -> bool:
    """Verify CSRF token."""
    if not settings.CSRF_ENABLED:
        return True
    expected = generate_csrf_token(session_id)
    return secrets.compare_digest(token, expected)


# ===== INPUT VALIDATION =====
# Dangerous patterns in input
DANGEROUS_INPUT_PATTERNS = [
    r"<script[^>]*>",
    r"javascript:",
    r"on\w+\s*=",
    r"data:text/html",
]

COMPILED_DANGEROUS_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in DANGEROUS_INPUT_PATTERNS
]


def validate_input(text: str, max_length: int = 50000) -> tuple[bool, Optional[str]]:
    """
    Validate user input.
    Returns: (is_valid, error_message)
    """
    if not text:
        return True, None
    
    # Check length
    if len(text) > max_length:
        return False, f"Input too long. Maximum: {max_length} characters"
    
    # Check for dangerous patterns
    for pattern in COMPILED_DANGEROUS_PATTERNS:
        if pattern.search(text):
            return False, "Input contains potentially dangerous content"
    
    return True, None


def validate_filename(filename: str) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded filename.
    Returns: (is_valid, error_message)
    """
    if not filename:
        return False, "Filename is required"
    
    # Check length
    if len(filename) > 255:
        return False, "Filename too long"
    
    # Check for path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        return False, "Invalid filename"
    
    # Check for null bytes
    if "\x00" in filename:
        return False, "Invalid filename"
    
    return True, None


# ===== SECURITY HEADERS =====
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://accounts.google.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://accounts.google.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    ),
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        
        return response


# ===== RATE LIMIT CONFIGURATION PER ENDPOINT =====
def get_rate_limit_config(path: str) -> Tuple[str, int]:
    """
    Get rate limit configuration for a given path.
    Returns: (rate_limit_key_prefix, max_requests_per_minute)
    """
    # Chat endpoints - more restrictive (LLM calls are expensive)
    if "/api/chat/send" in path:
        return "chat", settings.RATE_LIMIT_CHAT
    
    # File upload - restrictive
    if "/api/files" in path:
        return "file", settings.RATE_LIMIT_FILE_UPLOAD
    
    # Auth endpoints
    if "/api/auth/" in path:
        return "auth", settings.RATE_LIMIT_AUTH
    
    # Admin endpoints - higher limit
    if "/api/admin/" in path:
        return "admin", settings.RATE_LIMIT_ADMIN
    
    # Default
    return "api", settings.RATE_LIMIT_DEFAULT


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-based rate limiting middleware with per-endpoint configuration."""
    
    async def dispatch(self, request: Request, call_next):
        client_ip = get_client_ip(request)
        path = request.url.path
        
        # Check IP blacklist first
        if await is_ip_blacklisted(client_ip):
            log_security_event(
                event_type="blocked_ip_request",
                client_ip=client_ip,
                user_id=None,
                details={"path": path},
                severity="warning"
            )
            return Response(
                content='{"detail": "Access denied. Your IP has been blocked."}',
                status_code=403,
                media_type="application/json",
            )
        
        # Get rate limit config for this endpoint
        prefix, max_requests = get_rate_limit_config(path)
        key = f"{prefix}:{client_ip}"
        
        # Check rate limit
        is_allowed, remaining = await check_rate_limit_redis(
            key, max_requests, settings.RATE_LIMIT_WINDOW_SECONDS
        )
        
        if not is_allowed:
            log_security_event(
                event_type="rate_limit_exceeded",
                client_ip=client_ip,
                user_id=None,
                details={"path": path, "limit": max_requests},
                severity="warning"
            )
            return Response(
                content='{"detail": "Rate limit exceeded. Please try again later."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(settings.RATE_LIMIT_WINDOW_SECONDS),
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


# ===== CONTENT VALIDATION =====
def validate_json_content(data: dict, max_depth: int = 10) -> bool:
    """
    Validate JSON content to prevent deeply nested payloads.
    """
    def check_depth(obj, current_depth):
        if current_depth > max_depth:
            return False
        
        if isinstance(obj, dict):
            for value in obj.values():
                if not check_depth(value, current_depth + 1):
                    return False
        elif isinstance(obj, list):
            for item in obj:
                if not check_depth(item, current_depth + 1):
                    return False
        
        return True
    
    return check_depth(data, 0)


# ===== LOGGING =====
def log_security_event(
    event_type: str,
    client_ip: str,
    user_id: Optional[str],
    details: dict,
    severity: str = "warning"
):
    """Log security event."""
    import json
    from datetime import datetime
    
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": event_type,
        "client_ip": client_ip,
        "user_id": user_id,
        "severity": severity,
        "details": details,
    }
    
    print(f"[SECURITY][{severity.upper()}] {json.dumps(event)}")


# ===== IP STATISTICS TRACKING =====
async def track_ip_access(ip: str, endpoint: str, user_id: Optional[str] = None):
    """Track IP access for statistics."""
    rc = get_redis_client()
    if rc is None:
        return
    
    try:
        from datetime import datetime
        today = datetime.utcnow().strftime("%Y-%m-%d")
        hour = datetime.utcnow().strftime("%H")
        
        pipe = rc.pipeline()
        
        # Track total requests per IP (daily)
        pipe.hincrby(f"ip:stats:daily:{today}", ip, 1)
        pipe.expire(f"ip:stats:daily:{today}", 86400 * 7)  # Keep 7 days
        
        # Track requests per IP per hour
        pipe.hincrby(f"ip:stats:hourly:{today}:{hour}", ip, 1)
        pipe.expire(f"ip:stats:hourly:{today}:{hour}", 86400 * 2)  # Keep 2 days
        
        # Track unique IPs per day
        pipe.sadd(f"ip:unique:{today}", ip)
        pipe.expire(f"ip:unique:{today}", 86400 * 7)
        
        # Track endpoint access per IP
        pipe.hincrby(f"ip:endpoints:{ip}:{today}", endpoint, 1)
        pipe.expire(f"ip:endpoints:{ip}:{today}", 86400 * 7)
        
        await pipe.execute()
    except Exception as e:
        print(f"[Security] IP tracking error: {e}")


async def get_ip_statistics(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    ip_filter: Optional[str] = None,
    limit: int = 100
) -> dict:
    """Get IP access statistics."""
    rc = get_redis_client()
    if rc is None:
        return {"ips": [], "total": 0}
    
    try:
        from datetime import datetime, timedelta
        
        if not date_from:
            date_from = datetime.utcnow().strftime("%Y-%m-%d")
        if not date_to:
            date_to = date_from
        
        # Get all IPs and their request counts
        ip_data = {}
        
        # Parse dates
        start = datetime.strptime(date_from, "%Y-%m-%d")
        end = datetime.strptime(date_to, "%Y-%m-%d")
        
        current = start
        while current <= end:
            day_str = current.strftime("%Y-%m-%d")
            daily_stats = await rc.hgetall(f"ip:stats:daily:{day_str}")
            
            for ip, count in daily_stats.items():
                if ip_filter and ip_filter not in ip:
                    continue
                if ip not in ip_data:
                    ip_data[ip] = {"ip": ip, "total_requests": 0, "days": {}}
                ip_data[ip]["total_requests"] += int(count)
                ip_data[ip]["days"][day_str] = int(count)
            
            current += timedelta(days=1)
        
        # Sort by total requests
        sorted_ips = sorted(ip_data.values(), key=lambda x: x["total_requests"], reverse=True)[:limit]
        
        return {
            "ips": sorted_ips,
            "total": len(ip_data),
            "date_from": date_from,
            "date_to": date_to,
        }
    except Exception as e:
        print(f"[Security] Get IP stats error: {e}")
        return {"ips": [], "total": 0, "error": str(e)}
