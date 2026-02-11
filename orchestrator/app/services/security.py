"""
Security utilities for input sanitization and protection.

Implements:
1. Prompt Injection Detection & Prevention
2. PII Detection & Masking
3. System Prompt Protection
4. Input Sanitization
"""
import re
from typing import Optional, Tuple, List

# ===== PROMPT INJECTION PATTERNS =====
# Patterns that indicate potential prompt injection attacks
INJECTION_PATTERNS = [
    # Direct instruction override
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    r"override\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
    
    # New instruction injection
    r"new\s+instructions?:",
    r"system\s*:\s*",
    r"assistant\s*:\s*",
    r"\[system\]",
    r"\[instruction\]",
    r"<\s*system\s*>",
    r"<\s*instruction\s*>",
    
    # Role manipulation
    r"you\s+are\s+now\s+(a\s+)?",
    r"act\s+as\s+(a\s+)?",
    r"pretend\s+(to\s+be|you\s+are)",
    r"roleplay\s+as",
    r"switch\s+(to\s+)?role",
    
    # Jailbreak attempts
    r"dan\s+mode",
    r"developer\s+mode",
    r"jailbreak",
    r"bypass\s+(safety|filter|restriction)",
    r"disable\s+(safety|filter|restriction)",
    
    # System prompt extraction
    r"(show|reveal|display|print|output)\s+(your\s+)?(system\s+)?(prompt|instructions?)",
    r"what\s+(are|is)\s+your\s+(system\s+)?(prompt|instructions?)",
    r"repeat\s+(your\s+)?(system\s+)?(prompt|instructions?)",
    r"(initial|original|first)\s+(prompt|instructions?)",
    
    # Tool/function hijacking
    r"call\s+(this\s+)?(function|tool|api)",
    r"execute\s+(this\s+)?(function|tool|command)",
    r"run\s+(this\s+)?(function|tool|command)",
]

# Compile patterns for performance
COMPILED_INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in INJECTION_PATTERNS
]


# ===== PII PATTERNS =====
# Patterns for detecting Personally Identifiable Information
PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone_us": r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "phone_vn": r"\b(?:\+84|0)(?:\d{9,10})\b",
    "ssn": r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b",
    "credit_card": r"\b(?:\d{4}[-.\s]?){3}\d{4}\b",
    "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "passport": r"\b[A-Z]{1,2}\d{6,9}\b",
}

COMPILED_PII_PATTERNS = {
    key: re.compile(pattern, re.IGNORECASE) 
    for key, pattern in PII_PATTERNS.items()
}


# ===== DANGEROUS CONTENT PATTERNS =====
DANGEROUS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"data:text/html",
    r"on\w+\s*=",  # onclick, onerror, etc.
]

COMPILED_DANGEROUS_PATTERNS = [
    re.compile(pattern, re.IGNORECASE | re.DOTALL) 
    for pattern in DANGEROUS_PATTERNS
]


def detect_prompt_injection(text: str) -> Tuple[bool, List[str]]:
    """
    Detect potential prompt injection attacks in text.
    
    Returns: (is_suspicious, matched_patterns)
    """
    if not text:
        return False, []
    
    text_lower = text.lower()
    matched = []
    
    for pattern in COMPILED_INJECTION_PATTERNS:
        if pattern.search(text_lower):
            matched.append(pattern.pattern)
    
    return len(matched) > 0, matched


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    - Removes dangerous HTML/script content
    - Escapes special instruction markers
    - Preserves legitimate content
    """
    if not text:
        return text
    
    # Remove dangerous HTML/script patterns
    for pattern in COMPILED_DANGEROUS_PATTERNS:
        text = pattern.sub("[REMOVED]", text)
    
    # Escape instruction-like markers that could confuse the LLM
    # Replace with visually similar but safe characters
    replacements = [
        ("[system]", "[sys-tem]"),
        ("[instruction]", "[instruc-tion]"),
        ("<system>", "<sys-tem>"),
        ("<instruction>", "<instruc-tion>"),
        ("system:", "sys-tem:"),
        ("assistant:", "assis-tant:"),
    ]
    
    text_lower = text.lower()
    for old, new in replacements:
        if old in text_lower:
            # Case-insensitive replace
            pattern = re.compile(re.escape(old), re.IGNORECASE)
            text = pattern.sub(new, text)
    
    return text


def sanitize_file_content(text: str, filename: str) -> str:
    """
    Sanitize file content before sending to LLM.
    
    - Detects and warns about injection attempts in files
    - Adds content boundary markers
    - Limits instruction-like content
    """
    if not text:
        return text
    
    # Check for injection patterns in file content
    is_suspicious, patterns = detect_prompt_injection(text)
    
    # Add clear boundary markers
    sanitized = f"[BEGIN FILE CONTENT: {filename}]\n"
    
    if is_suspicious:
        sanitized += "[WARNING: File contains instruction-like content which has been preserved as data only]\n"
    
    # Sanitize the content
    sanitized += sanitize_input(text)
    sanitized += f"\n[END FILE CONTENT: {filename}]"
    
    return sanitized


def mask_pii(text: str, mask_char: str = "*") -> Tuple[str, dict]:
    """
    Detect and mask PII in text.
    
    Returns: (masked_text, detection_stats)
    """
    if not text:
        return text, {}
    
    stats = {}
    masked_text = text
    
    for pii_type, pattern in COMPILED_PII_PATTERNS.items():
        matches = pattern.findall(masked_text)
        if matches:
            stats[pii_type] = len(matches)
            
            # Mask each match
            for match in matches:
                if len(match) > 4:
                    # Keep first 2 and last 2 characters
                    masked = match[:2] + mask_char * (len(match) - 4) + match[-2:]
                else:
                    masked = mask_char * len(match)
                masked_text = masked_text.replace(match, masked, 1)
    
    return masked_text, stats


def check_system_prompt_leak(response: str, system_prompt: str) -> bool:
    """
    Check if LLM response contains system prompt content.
    
    Returns: True if potential leak detected
    """
    if not response or not system_prompt:
        return False
    
    # Extract key phrases from system prompt (longer than 20 chars)
    prompt_words = system_prompt.lower().split()
    
    # Check for exact phrase matches (4+ consecutive words)
    for i in range(len(prompt_words) - 3):
        phrase = " ".join(prompt_words[i:i+4])
        if len(phrase) > 20 and phrase in response.lower():
            return True
    
    # Check for common system prompt indicators in response
    leak_indicators = [
        "my system prompt",
        "my instructions are",
        "i was instructed to",
        "my initial prompt",
        "here is my prompt",
        "my rules are",
    ]
    
    response_lower = response.lower()
    for indicator in leak_indicators:
        if indicator in response_lower:
            return True
    
    return False


def validate_user_access(user_id: str, resource_user_id: str) -> bool:
    """
    Validate user has access to resource (cross-tenant check).
    
    Returns: True if access is allowed
    """
    if not user_id or not resource_user_id:
        return False
    
    return user_id == resource_user_id


def get_security_headers() -> dict:
    """Get recommended security headers for API responses."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }


# ===== RATE LIMITING HELPERS =====
def get_rate_limit_key(user_id: str, action: str) -> str:
    """Generate rate limit key for user action."""
    return f"ratelimit:{action}:{user_id}"


# ===== LOGGING HELPERS =====
def log_security_event(
    event_type: str,
    user_id: str,
    details: dict,
    severity: str = "warning"
):
    """Log security event for monitoring."""
    import json
    from datetime import datetime
    
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": event_type,
        "user_id": user_id,
        "severity": severity,
        "details": details,
    }
    
    # In production, this would go to a security logging system
    print(f"[SECURITY][{severity.upper()}] {json.dumps(event)}")
