from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import connect_db, close_db
from app.services.kafka_producer import connect_kafka, close_kafka
from app.services.redis_client import connect_redis, close_redis
from app.middleware import auth_middleware
from app.security import SecurityHeadersMiddleware, RateLimitMiddleware
from app.routes import auth, chat, files, stream, admin

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    await connect_kafka()
    await connect_redis()
    print("[Backend] API gateway started")
    yield
    # Shutdown
    await close_kafka()
    await close_redis()
    await close_db()
    print("[Backend] API gateway stopped")


app = FastAPI(
    title="Alice Backend API",
    description="API gateway — auth, CRUD, Kafka producer, Redis reader",
    version="2.0.0",
    lifespan=lifespan,
)

# Security headers middleware (runs last = added first)
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Auth middleware (added first = runs second)
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

# CORS (added second = runs first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(files.router)
app.include_router(stream.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {"service": "backend", "version": "2.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "backend"}
