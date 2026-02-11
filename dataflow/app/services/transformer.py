"""
Transform raw events into standardized analytics schema.
- Normalize fields
- Enrich with metadata
- Mask/hash PII if needed
"""
import hashlib
from datetime import datetime, timezone


def transform_llm_event(raw: dict) -> dict:
    """Transform raw LLM_RESPONSE event → analytics_events document."""
    timestamp = _parse_timestamp(raw.get("timestamp"))

    return {
        "event_type": "LLM_RESPONSE",
        "timestamp": timestamp,
        "conversation_id": raw.get("conversation_id", ""),
        "user_id": raw.get("user_id", ""),
        "user_id_hash": _hash_pii(raw.get("user_id", "")),
        "model": raw.get("model", "unknown"),
        "latency_ms": raw.get("latency_ms", 0),
        "token_prompt": raw.get("token_prompt", 0),
        "token_completion": raw.get("token_completion", 0),
        "token_total": raw.get("token_prompt", 0) + raw.get("token_completion", 0),
        "success": raw.get("success", True),
        "has_rag": raw.get("has_rag", False),
        "message_length": raw.get("message_length", 0),
        "reply_length": raw.get("reply_length", 0),
        "error": raw.get("error"),
        "environment": "production",
        "service": "orchestrator",
        "processed_at": datetime.now(timezone.utc),
    }


def transform_file_event(raw: dict) -> dict:
    """Transform raw FILE_PROCESSED event → analytics_events document."""
    timestamp = _parse_timestamp(raw.get("timestamp"))

    return {
        "event_type": "FILE_PROCESSED",
        "timestamp": timestamp,
        "conversation_id": raw.get("conversation_id", ""),
        "user_id": raw.get("user_id", ""),
        "user_id_hash": _hash_pii(raw.get("user_id", "")),
        "file_id": raw.get("file_id", ""),
        "file_type": raw.get("file_type", ""),
        "original_name": raw.get("original_name", ""),
        "file_size": raw.get("file_size", 0),
        "file_size_kb": round(raw.get("file_size", 0) / 1024, 2),
        "chunk_count": raw.get("chunk_count", 0),
        "latency_ms": raw.get("latency_ms", 0),
        "success": raw.get("success", True),
        "error": raw.get("error"),
        "environment": "production",
        "service": "orchestrator",
        "processed_at": datetime.now(timezone.utc),
    }


def transform_generic_event(raw: dict) -> dict:
    """Transform generic conversation lifecycle event."""
    timestamp = _parse_timestamp(raw.get("timestamp"))

    return {
        "event_type": raw.get("event_type", "UNKNOWN"),
        "timestamp": timestamp,
        "conversation_id": raw.get("conversation_id", ""),
        "user_id": raw.get("user_id", ""),
        "user_id_hash": _hash_pii(raw.get("user_id", "")),
        "metadata": {k: v for k, v in raw.items()
                     if k not in ("event_type", "timestamp", "conversation_id", "user_id")},
        "environment": "production",
        "service": "orchestrator",
        "processed_at": datetime.now(timezone.utc),
    }


def _parse_timestamp(ts) -> datetime:
    """Parse ISO timestamp string to datetime."""
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    return datetime.now(timezone.utc)


def _hash_pii(value: str) -> str:
    """Hash PII for anonymized analytics."""
    if not value:
        return ""
    return hashlib.sha256(value.encode()).hexdigest()[:16]
