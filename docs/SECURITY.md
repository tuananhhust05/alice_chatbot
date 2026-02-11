# Security Implementation

This document describes the security mechanisms implemented in Alice Chatbot to protect against common attacks and ensure data privacy.

## Table of Contents

- [Security Architecture](#security-architecture)
- [Authentication & Authorization](#authentication--authorization)
- [Rate Limiting](#rate-limiting)
- [Input Validation & Sanitization](#input-validation--sanitization)
- [Prompt Injection Protection](#prompt-injection-protection)
- [PII Detection & Masking](#pii-detection--masking)
- [Cross-Tenant Data Protection](#cross-tenant-data-protection)
- [Security Headers](#security-headers)
- [File Upload Security](#file-upload-security)
- [Admin Security](#admin-security)
- [Security Logging & Monitoring](#security-logging--monitoring)

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
│                     (User sends message/uploads file)                        │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND API                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. SecurityHeadersMiddleware                                         │   │
│  │    - X-Frame-Options: DENY                                           │   │
│  │    - X-XSS-Protection: 1; mode=block                                 │   │
│  │    - X-Content-Type-Options: nosniff                                 │   │
│  │    - Content-Security-Policy                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 2. RateLimitMiddleware (Redis-based)                                 │   │
│  │    - 60 requests/min for API                                         │   │
│  │    - 10 requests/min for file uploads                                │   │
│  │    - 5 requests/min for admin login                                  │   │
│  │    → Block if exceeded (429 Too Many Requests)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 3. Authentication Middleware                                         │   │
│  │    - Google OAuth2 token validation                                  │   │
│  │    - JWT token verification                                          │   │
│  │    → Block if invalid (401 Unauthorized)                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 4. Input Validation                                                  │   │
│  │    - Message length limits                                           │   │
│  │    - Dangerous content blocking                                      │   │
│  │    - Filename validation                                             │   │
│  │    → Block if invalid (400 Bad Request)                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│                            Process Request                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ORCHESTRATOR                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 5. Security Input Processing                                         │   │
│  │    - detect_prompt_injection(message)                                │   │
│  │    - detect_pii(message) → mask_pii()                                │   │
│  │    - sanitize_input(message)                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│                            LLM Processing                                    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 6. Security Response Validation                                      │   │
│  │    - check_system_prompt_leak(response)                              │   │
│  │    - detect_pii(response) → log for monitoring                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Authentication & Authorization

### Google OAuth2 Integration

Users authenticate via Google OAuth2:

```python
# Token validation flow
1. User signs in with Google on frontend
2. Frontend receives Google ID token
3. Backend verifies token with Google
4. Backend creates/retrieves user record
5. Backend issues session cookie
```

### Protected Endpoints

All chat and file endpoints require authentication:

```python
@router.post("/send")
async def send_message(
    request: ChatRequest,
    user: dict = Depends(get_current_user_dep),  # Auth required
):
```

---

## Rate Limiting

### Redis-Based Sliding Window

Rate limiting uses Redis sorted sets for accurate sliding window implementation:

```python
# Sliding window algorithm
1. Remove entries outside current window
2. Count entries in window
3. If under limit, add new entry
4. Return allow/deny decision
```

### Rate Limit Configuration

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| API General | 60 requests | 60 seconds |
| File Upload | 10 requests | 60 seconds |
| Admin Login | 5 attempts | 60 seconds |
| Chat Send | 30 messages | 60 seconds |

### Response Headers

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1699123456
```

---

## Input Validation & Sanitization

### Message Validation

```python
# Validation rules
MAX_MESSAGE_LENGTH = 10000  # characters
DANGEROUS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"data:text/html",
    r"on\w+\s*=",  # onclick, onerror, etc.
]
```

### Dangerous Content Blocking

Input containing XSS patterns is rejected:

```python
def contains_dangerous_content(text: str) -> bool:
    for pattern in COMPILED_DANGEROUS_PATTERNS:
        if pattern.search(text):
            return True
    return False
```

---

## Prompt Injection Protection

### Detection Patterns

The system detects various prompt injection techniques:

```python
INJECTION_PATTERNS = [
    # Direct instruction override
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
    
    # Role manipulation
    r"you\s+are\s+now\s+(a\s+)?",
    r"act\s+as\s+(a\s+)?",
    r"pretend\s+(to\s+be|you\s+are)",
    
    # Jailbreak attempts
    r"dan\s+mode",
    r"developer\s+mode",
    r"jailbreak",
    r"bypass\s+(safety|filter|restriction)",
    
    # System prompt extraction
    r"(show|reveal|display|print)\s+(your\s+)?(system\s+)?prompt",
    r"what\s+(are|is)\s+your\s+(system\s+)?instructions?",
    
    # Tool hijacking
    r"call\s+(this\s+)?(function|tool|api)",
    r"execute\s+(this\s+)?(command|function)",
]
```

### Handling Detected Injections

When injection is detected:
1. Log security event with WARNING severity
2. Continue processing (may still answer benign parts)
3. System prompt is protected and not exposed

---

## PII Detection & Masking

### Detected PII Types

```python
PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone_us": r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "phone_vn": r"\b(?:\+84|0)(?:\d{9,10})\b",
    "ssn": r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",
    "credit_card": r"\b(?:\d{4}[-.\s]?){3}\d{4}\b",
    "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
}
```

### Masking Examples

```
# Input
john.doe@email.com → jo**********om
+1-555-123-4567   → +1**********67
4111-2222-3333-4444 → 41**************44
```

### PII in LLM Responses

Responses are checked for PII leakage and logged for monitoring.

---

## Cross-Tenant Data Protection

### User Isolation

All database queries filter by `user_id`:

```python
# Every query includes user filter
conversation = await db.conversations.find_one({
    "_id": ObjectId(conversation_id),
    "user_id": user_id,  # ← Always filter by authenticated user
})

# User cannot access other users' data
if not conversation:
    raise HTTPException(status_code=404, detail="Not found")
```

### Access Validation

```python
def validate_user_access(user_id: str, resource_user_id: str) -> bool:
    return user_id == resource_user_id
```

---

## Security Headers

### Applied Headers

```python
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}
```

---

## File Upload Security

### Validation Rules

```python
ALLOWED_EXTENSIONS = {"pdf", "txt", "csv", "docx", "xlsx"}
MAX_FILE_SIZE_MB = 5

# Filename validation
- No path traversal (../)
- No null bytes
- Alphanumeric + safe characters only
- Maximum 255 characters
```

### Processing Flow

```python
# File upload security flow
1. Validate filename format
2. Check file extension against whitelist
3. Verify file size limit
4. Create temporary file for processing
5. Extract text content only
6. Delete temporary file immediately
7. Return extracted text (file NOT stored)
```

---

## Admin Security

### Admin Authentication

```python
# Separate admin authentication
- Username/password stored in environment variables
- Password hashed with bcrypt
- Session stored in Redis with TTL
```

### Brute Force Protection

```python
# Admin login rate limiting
MAX_ADMIN_LOGIN_ATTEMPTS = 5
LOCKOUT_WINDOW = 60  # seconds
LOCKOUT_DURATION = 300  # 5 minutes

# After 5 failed attempts, account is locked for 5 minutes
```

### Admin Session Management

```python
# Session configuration
SESSION_TTL = 3600  # 1 hour
SESSION_REFRESH = True  # Refresh on activity
```

---

## Security Logging & Monitoring

### Logged Security Events

| Event Type | Severity | Trigger |
|------------|----------|---------|
| `prompt_injection_attempt` | WARNING | Injection pattern detected |
| `pii_detected` | INFO | PII found in user message |
| `system_prompt_leak` | CRITICAL | System prompt in LLM response |
| `pii_in_response` | INFO | PII detected in LLM response |
| `invalid_input_blocked` | WARNING | Dangerous input rejected |
| `invalid_filename_blocked` | WARNING | Dangerous filename rejected |
| `disallowed_file_type` | INFO | Unsupported file type |
| `rate_limit_exceeded` | WARNING | Rate limit hit |
| `admin_login_failed` | WARNING | Failed admin login |
| `admin_login_success` | INFO | Successful admin login |

### Log Format

```json
{
    "timestamp": "2024-01-15T10:30:45.123Z",
    "type": "prompt_injection_attempt",
    "client_ip": "192.168.1.100",
    "user_id": "user@example.com",
    "severity": "warning",
    "details": {
        "matched_patterns": ["ignore previous instructions"],
        "message_preview": "ignore previous instructions..."
    }
}
```

### IP Tracking

```python
# IP statistics tracked in Redis
- Total requests per IP (daily)
- Requests per IP per hour
- Unique IPs per day
- Endpoint access per IP
```

---

## Security Files Reference

### Backend

| File | Security Features |
|------|-------------------|
| `app/security.py` | Rate limiting, input validation, security headers, IP tracking |
| `app/middleware.py` | Middleware registration |
| `app/routes/auth.py` | Google OAuth2 authentication |
| `app/routes/files.py` | Filename validation, file type whitelist |
| `app/services/admin_auth.py` | Admin authentication, brute force protection |

### Orchestrator

| File | Security Features |
|------|-------------------|
| `app/services/security.py` | Prompt injection detection, PII masking, sanitization |
| `app/services/chat_handler.py` | Full security workflow integration |

---

## Security Best Practices

1. **Never log sensitive data** - PII is masked before logging
2. **Fail securely** - Errors don't expose internal details
3. **Defense in depth** - Multiple security layers
4. **Least privilege** - Users only access their own data
5. **Secure defaults** - Security enabled by default
6. **Regular updates** - Dependencies kept up to date
