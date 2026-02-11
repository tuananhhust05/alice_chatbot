"""
Retry handler with exponential backoff and jitter.

Implements proper retry policy:
- Exponential backoff: delay = base * multiplier^retry_count
- Jitter: random delay to prevent thundering herd
- Max backoff cap
- Retry count tracking
"""
import random
import asyncio
from datetime import datetime
from typing import Optional
from app.config import get_settings, is_retryable_error

settings = get_settings()


def calculate_backoff_delay(retry_count: int) -> float:
    """
    Calculate delay with exponential backoff + jitter.
    
    Formula: delay = min(base * multiplier^n + random(0, jitter), max)
    
    Example with defaults (base=1, mult=2, jitter=2, max=120):
    - Retry 1: 1*2^1 + rand(0,2) = 2-4s
    - Retry 2: 1*2^2 + rand(0,2) = 4-6s
    - Retry 3: 1*2^3 + rand(0,2) = 8-10s
    - Retry 4: 1*2^4 + rand(0,2) = 16-18s
    - Retry 5: 1*2^5 + rand(0,2) = 32-34s
    """
    # Exponential backoff
    delay = settings.RETRY_BACKOFF_BASE * (settings.RETRY_BACKOFF_MULTIPLIER ** retry_count)
    
    # Cap at max
    delay = min(delay, settings.RETRY_BACKOFF_MAX)
    
    # Add jitter (random component to prevent thundering herd)
    jitter = random.uniform(0, settings.RETRY_JITTER_MAX)
    delay += jitter
    
    return delay


def should_retry(error: Exception, retry_count: int) -> bool:
    """
    Determine if task should be retried.
    
    Returns True if:
    1. Error is transient (retryable)
    2. Retry count < max retries
    """
    # Check retry count
    if retry_count >= settings.MAX_RETRY_COUNT:
        return False
    
    # Check if error is retryable
    return is_retryable_error(error)


def create_retry_payload(
    original_data: dict,
    original_topic: str,
    error: str,
    retry_count: int = 0,
) -> dict:
    """
    Create payload for retry queue.
    
    Adds retry metadata to original message.
    """
    return {
        # Original message data
        **original_data,
        # Retry metadata
        "_retry": {
            "original_topic": original_topic,
            "retry_count": retry_count + 1,
            "max_retry": settings.MAX_RETRY_COUNT,
            "last_error": error,
            "last_attempt": datetime.utcnow().isoformat(),
            "next_delay": calculate_backoff_delay(retry_count + 1),
        }
    }


def extract_retry_info(data: dict) -> tuple[dict, Optional[dict]]:
    """
    Extract retry metadata from message.
    
    Returns: (original_data, retry_info)
    """
    retry_info = data.pop("_retry", None)
    return data, retry_info


async def wait_for_backoff(retry_count: int):
    """Wait for backoff delay before retry."""
    delay = calculate_backoff_delay(retry_count)
    print(f"[Retry] Waiting {delay:.1f}s before retry #{retry_count}")
    await asyncio.sleep(delay)
