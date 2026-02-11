# Security Implementation Summary

## Security Flow trong Alice Chatbot

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
│                     (User sends message/uploads file)                        │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND API                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. SecurityHeadersMiddleware                                         │   │
│  │    - X-Frame-Options: DENY                                           │   │
│  │    - X-XSS-Protection: 1; mode=block                                 │   │
│  │    - X-Content-Type-Options: nosniff                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 2. RateLimitMiddleware                                               │   │
│  │    - 60 requests/min for API                                         │   │
│  │    - 10 requests/min for file uploads                                │   │
│  │    → Block if exceeded (429 Too Many Requests)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 3. Auth Middleware                                                   │   │
│  │    - Validate JWT token                                              │   │
│  │    - Extract user_id                                                 │   │
│  │    → Block if invalid (401 Unauthorized)                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 4. Route Handlers                                                    │   │
│  │                                                                       │   │
│  │    /api/chat/send:                                                   │   │
│  │    ├─ validate_input(message) → Check XSS, length                    │   │
│  │    ├─ Cross-tenant check: user_id must match                         │   │
│  │    └─ log_security_event() if suspicious                             │   │
│  │                                                                       │   │
│  │    /api/files/extract:                                               │   │
│  │    ├─ validate_filename() → Path traversal, null bytes              │   │
│  │    ├─ Check allowed extensions                                       │   │
│  │    └─ Size limit (5MB max)                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│                          Publish to Kafka                                    │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ORCHESTRATOR                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 5. Security Input Processing (chat_handler.py)                       │   │
│  │                                                                       │   │
│  │    a. detect_prompt_injection(message)                               │   │
│  │       - "Ignore previous instructions"                               │   │
│  │       - "System:" markers                                            │   │
│  │       - Role manipulation                                            │   │
│  │       - Jailbreak attempts                                           │   │
│  │       → Log warning, sanitize and continue                           │   │
│  │                                                                       │   │
│  │    b. sanitize_input(message)                                        │   │
│  │       - Remove <script> tags                                         │   │
│  │       - Escape [system] markers                                      │   │
│  │                                                                       │   │
│  │    c. sanitize_file_content(file_content)                            │   │
│  │       - Add boundary markers                                         │   │
│  │       - Warn about instruction-like content                          │   │
│  │                                                                       │   │
│  │    d. mask_pii(message)                                              │   │
│  │       - Email: te**@example.com                                      │   │
│  │       - Phone: 55*-***-4567                                          │   │
│  │       - SSN: 12*-**-6789                                             │   │
│  │       - Credit Card: 41**-****-****-1111                             │   │
│  │       → Use masked version for analytics/logging                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│                            LLM API Call (Groq)                              │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 6. Security Response Validation                                      │   │
│  │                                                                       │   │
│  │    a. check_system_prompt_leak(response, system_prompt)              │   │
│  │       - Check if response contains system prompt phrases             │   │
│  │       - Detect "My instructions are..." patterns                     │   │
│  │       → Log CRITICAL if detected                                     │   │
│  │                                                                       │   │
│  │    b. mask_pii(response)                                             │   │
│  │       - Check if LLM leaked any PII                                  │   │
│  │       → Log for monitoring                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│                      Log security summary & Save response                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Files với Security Logic

### Backend
| File | Security Features |
|------|-------------------|
| `app/security.py` | Rate limiting, input validation, filename validation, security headers |
| `app/main.py` | Middleware registration |
| `app/routes/chat.py` | Input validation, security logging |
| `app/routes/files.py` | Filename validation, file type check |

### Orchestrator
| File | Security Features |
|------|-------------------|
| `app/services/security.py` | Prompt injection detection, PII masking, sanitization |
| `app/services/chat_handler.py` | Full security workflow integration |

## Security Events Logged

| Event Type | Severity | Trigger |
|------------|----------|---------|
| `prompt_injection_attempt` | WARNING | Injection pattern detected |
| `pii_detected` | INFO | PII found in user message |
| `system_prompt_leak` | CRITICAL | System prompt in response |
| `pii_in_response` | INFO | PII in LLM response |
| `invalid_input_blocked` | WARNING | Dangerous input rejected |
| `invalid_filename_blocked` | WARNING | Dangerous filename rejected |
| `disallowed_file_type` | INFO | Unsupported file type |
| `request_security_summary` | INFO | End of request summary |

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| API general | 60 requests | 60 seconds |
| File upload | 10 requests | 60 seconds |

## Cross-Tenant Protection

Mọi database query đều filter theo `user_id`:

```python
# Example from chat.py
conversation = await db.conversations.find_one({
    "_id": ObjectId(conversation_id),
    "user_id": user_id,  # ← Always filter by user
})
```
