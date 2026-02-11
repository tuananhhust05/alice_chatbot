from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Groq
    GROQ_API_KEY: str = ""

    # MongoDB (shared with backend)
    MONGO_URI: str = "mongodb://alice:alice_secret@mongodb:27017/alice_chatbot?authSource=admin"
    MONGO_DB_NAME: str = "alice_chatbot"

    # Weaviate
    WEAVIATE_URL: str = "http://weaviate:8080"

    # Kafka (consume from backend)
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_CHAT_TOPIC: str = "chat_requests"
    KAFKA_FILE_TOPIC: str = "file_requests"
    KAFKA_RETRY_TOPIC: str = "retry_requests"  # Retry queue
    KAFKA_CONSUMER_GROUP: str = "orchestrator_group"

    # Kafkaflow (emit events to dataflow)
    KAFKAFLOW_BOOTSTRAP_SERVERS: str = "kafkaflow:9094"
    KAFKAFLOW_EVENTS_TOPIC: str = "chatbot.events"
    KAFKAFLOW_LLM_TOPIC: str = "llm.calls"
    KAFKAFLOW_FILE_TOPIC: str = "file.processing"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_RESULT_TTL: int = 300  # 5 minutes

    # File Upload
    UPLOAD_DIR: str = "./uploads"

    # Concurrency
    MAX_WORKERS: int = 10

    # ===== RETRY CONFIG =====
    # Max retry attempts before sending to DLQ
    MAX_RETRY_COUNT: int = 5
    
    # Exponential backoff base (seconds)
    RETRY_BACKOFF_BASE: float = 1.0
    
    # Backoff multiplier
    RETRY_BACKOFF_MULTIPLIER: float = 2.0
    
    # Max backoff delay (seconds)
    RETRY_BACKOFF_MAX: float = 120.0
    
    # Jitter range (seconds) - random delay added to backoff
    RETRY_JITTER_MAX: float = 2.0

    class Config:
        env_file = ".env"
        extra = "allow"


# Retryable error types (transient errors)
RETRYABLE_ERRORS = [
    "timeout",
    "rate_limit",
    "connection",
    "network",
    "503",
    "504",
    "429",
    "temporary",
    "unavailable",
    "overloaded",
]


def is_retryable_error(error: Exception) -> bool:
    """Check if error is transient and should be retried."""
    error_str = str(error).lower()
    for pattern in RETRYABLE_ERRORS:
        if pattern in error_str:
            return True
    return False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
