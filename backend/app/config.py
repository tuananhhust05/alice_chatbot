from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # MongoDB
    MONGO_URI: str = "mongodb://alice:alice_secret@mongodb:27017/alice_chatbot?authSource=admin"
    MONGO_DB_NAME: str = "alice_chatbot"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # App
    SECRET_KEY: str = "change-me-in-production"
    FRONTEND_URL: str = "http://localhost:3009"
    BACKEND_URL: str = "http://localhost:8009"
    
    # Security
    SECURE_COOKIES: bool = False  # Set True in production with HTTPS
    CSRF_ENABLED: bool = True
    CSRF_SECRET: str = "csrf-secret-change-me-in-production"

    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_SECRET_KEY: str = "admin-secret-change-me"
    
    # Admin Login Security
    ADMIN_LOGIN_MAX_ATTEMPTS: int = 5
    ADMIN_LOGIN_LOCKOUT_MINUTES: int = 15

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_CHAT_TOPIC: str = "chat_requests"
    KAFKA_FILE_TOPIC: str = "file_requests"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10

    # Orchestrator service (for RAG data processing)
    ORCHESTRATOR_URL: str = "http://orchestrator:8001"
    
    # Rate Limiting (requests per minute)
    RATE_LIMIT_DEFAULT: int = 60           # Default API rate limit
    RATE_LIMIT_CHAT: int = 30              # Chat send message (more restrictive)
    RATE_LIMIT_AUTH: int = 20              # Auth endpoints
    RATE_LIMIT_FILE_UPLOAD: int = 10       # File uploads
    RATE_LIMIT_ADMIN: int = 100            # Admin endpoints
    RATE_LIMIT_WINDOW_SECONDS: int = 60    # Window size

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
