from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # MongoDB (shared with all services)
    MONGO_URI: str = "mongodb://alice:alice_secret@mongodb:27017/alice_chatbot?authSource=admin"
    MONGO_DB_NAME: str = "alice_chatbot"

    # Kafkaflow (consume events from orchestrator)
    KAFKAFLOW_BOOTSTRAP_SERVERS: str = "kafkaflow:9094"
    KAFKAFLOW_EVENTS_TOPIC: str = "chatbot.events"
    KAFKAFLOW_LLM_TOPIC: str = "llm.calls"
    KAFKAFLOW_FILE_TOPIC: str = "file.processing"
    KAFKAFLOW_CONSUMER_GROUP: str = "dataflow_group"

    # Processing
    MAX_WORKERS: int = 5
    METRIC_WINDOW_MINUTES: int = 5  # Aggregation window size

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
