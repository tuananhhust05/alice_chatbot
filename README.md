# Alice Chatbot

An intelligent AI-powered chatbot application with real-time streaming responses, RAG (Retrieval-Augmented Generation) capabilities, and enterprise-grade security.

**Production**: [https://alicechatbot.com/](https://alicechatbot.com/)

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Security](#security)
- [Testing](#testing)
- [Contributing](#contributing)

---

## Features

### Core Features

- **AI Chat Interface** - Real-time conversational AI with streaming responses
- **Multi-turn Conversations** - Context-aware dialogue with conversation history
- **File Upload & Analysis** - Upload PDF, DOCX, TXT, CSV, XLSX files for AI analysis
- **RAG Integration** - Retrieval-Augmented Generation for knowledge-based answers
- **Google OAuth Authentication** - Secure user authentication via Google

### User Experience

- **Real-time Streaming** - See AI responses as they're generated
- **Markdown Rendering** - Rich text formatting with code syntax highlighting
- **Conversation Management** - Create, rename, and delete conversations
- **Responsive Design** - Works on desktop, tablet, and mobile devices
- **Dark/Light Mode** - Theme support for user preference

### Enterprise Features

- **Admin Dashboard** - Manage users, view analytics, upload RAG data
- **Rate Limiting** - Protect against abuse with Redis-based rate limiting
- **Security Logging** - Comprehensive security event logging
- **IP Tracking** - Monitor and analyze access patterns
- **Multi-tenant Isolation** - Secure data separation between users

### AI Capabilities

- **Intent Detection** - Understand user intent and route appropriately
- **Tool Calling** - Execute functions based on user requests
- **Knowledge Retrieval** - Search and cite from uploaded documents
- **PII Detection** - Detect and mask sensitive information

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│    Kafka    │────▶│ Orchestrator│
│   (React)   │     │  (FastAPI)  │     │             │     │  (FastAPI)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                                       │
                           │                                       │
                           ▼                                       ▼
                    ┌─────────────┐                         ┌─────────────┐
                    │   MongoDB   │                         │  Weaviate   │
                    │             │                         │ (Vector DB) │
                    └─────────────┘                         └─────────────┘
                           │                                       │
                           │                                       │
                           ▼                                       ▼
                    ┌─────────────┐                         ┌─────────────┐
                    │    Redis    │◀────────────────────────│  Dataflow   │
                    │  (Cache)    │                         │  (Analytics)│
                    └─────────────┘                         └─────────────┘
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3009 | React SPA with Vite |
| Backend | 8009 | REST API, authentication, file handling |
| Orchestrator | 8001 | AI processing, LLM integration, RAG |
| Dataflow | 8002 | Analytics, data aggregation |
| MongoDB | 27017 | Primary database |
| Weaviate | 8080 | Vector database for RAG |
| Redis | 6379 | Caching, rate limiting, sessions |
| Kafka | 9092 | Message queue for async processing |

---

## Tech Stack

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation

### Backend
- **FastAPI** - Python web framework
- **Pydantic** - Data validation
- **Motor** - Async MongoDB driver
- **Redis** - Caching and rate limiting
- **Kafka** - Message queue

### AI/ML
- **Groq** - LLM provider (Llama 3)
- **Weaviate** - Vector database
- **Sentence Transformers** - Embeddings

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Orchestration
- **Nginx** - Reverse proxy (production)

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/alice-chatbot.git
cd alice-chatbot
```

### 2. Environment Setup

```bash
# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp orchestrator/.env.example orchestrator/.env
cp dataflow/.env.example dataflow/.env
cp frontend/.env.example frontend/.env
```

### 3. Configure Environment Variables

Edit the `.env` files with your credentials:

```bash
# backend/.env
GOOGLE_CLIENT_ID=your-google-client-id
GROQ_API_KEY=your-groq-api-key

# orchestrator/.env
GROQ_API_KEY=your-groq-api-key

# frontend/.env
VITE_GOOGLE_CLIENT_ID=your-google-client-id
VITE_API_URL=http://localhost:8009
```

### 4. Start Services

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f
```

### 5. Access Application

- **Frontend**: http://localhost:3009
- **Backend API**: http://localhost:8009
- **API Docs**: http://localhost:8009/docs

---

## Development Setup

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server with hot reload
npm run dev

# Run tests
npm run test

# Build for production
npm run build
```

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Start dev server with hot reload
uvicorn app.main:app --reload --port 8000

# Run tests
pytest
```

### Orchestrator Development

```bash
cd orchestrator

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start dev server
uvicorn app.main:app --reload --port 8001

# Run tests
pytest
```

---

## Production Deployment

### Docker Compose Production

```bash
# Build and start all services
docker compose -f docker-compose.yml up -d --build

# Scale services
docker compose up -d --scale orchestrator=3
```

### Environment Variables (Production)

```bash
# Required for production
ENVIRONMENT=production
DEBUG=false

# Security
SECRET_KEY=your-secure-secret-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-password-hash

# Database
MONGO_USERNAME=alice
MONGO_PASSWORD=secure-password

# API Keys
GOOGLE_CLIENT_ID=your-google-client-id
GROQ_API_KEY=your-groq-api-key
```

### Health Checks

```bash
# Check service health
curl http://localhost:8009/health
curl http://localhost:8001/health
```

---

## Project Structure

```
alice_chatbot/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── api/             # API client
│   │   ├── components/      # React components
│   │   ├── context/         # React context
│   │   ├── pages/           # Page components
│   │   └── types/           # TypeScript types
│   ├── Dockerfile
│   └── package.json
│
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── models/          # Data models
│   │   ├── security.py      # Security middleware
│   │   └── main.py          # App entry point
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── orchestrator/             # AI orchestration
│   ├── app/
│   │   ├── services/        # AI services
│   │   │   ├── chat_handler.py
│   │   │   ├── llm.py
│   │   │   ├── vectorstore.py
│   │   │   └── security.py
│   │   └── main.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── dataflow/                 # Analytics service
│   ├── app/
│   │   └── services/
│   ├── Dockerfile
│   └── requirements.txt
│
├── docs/                     # Documentation
│   └── SECURITY.md
│
├── docker-compose.yml        # Container orchestration
└── README.md
```

---

## API Documentation

### Authentication

```bash
# Login with Google
POST /api/auth/google
Content-Type: application/json
{
    "token": "google-id-token"
}

# Response
{
    "user": {
        "email": "user@example.com",
        "name": "User Name"
    }
}
```

### Chat

```bash
# Send message
POST /api/chat/send
Authorization: Bearer <token>
Content-Type: application/json
{
    "conversation_id": "conv_123",
    "content": "Hello, how are you?"
}

# Stream response
GET /api/stream/{request_id}
Accept: text/event-stream
```

### Files

```bash
# Extract text from file
POST /api/files/extract
Authorization: Bearer <token>
Content-Type: multipart/form-data
file: <file>

# Response
{
    "text": "extracted text content...",
    "file_type": "pdf",
    "text_length": 5000
}
```

### Interactive API Docs

- Swagger UI: http://localhost:8009/docs
- ReDoc: http://localhost:8009/redoc

---

## Security

Alice Chatbot implements multiple security layers:

- **Authentication** - Google OAuth2 with JWT sessions
- **Rate Limiting** - Redis-based sliding window
- **Input Validation** - XSS prevention, dangerous content blocking
- **Prompt Injection Protection** - Pattern-based detection
- **PII Detection & Masking** - Email, phone, SSN, credit card
- **Cross-Tenant Isolation** - User data separation
- **Security Headers** - CSP, X-Frame-Options, etc.

See [docs/SECURITY.md](docs/SECURITY.md) for detailed documentation.

---

## Testing

### Unit Tests

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm run test

# Orchestrator
cd orchestrator && pytest
```

### Test Coverage

```bash
# Backend coverage
cd backend && pytest --cov=app --cov-report=html

# Frontend coverage
cd frontend && npm run test:coverage
```

### Integration Tests

```bash
# Run with test containers
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Python: Follow PEP 8, use Black formatter
- TypeScript: ESLint + Prettier
- Commits: Conventional Commits format

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/alice-chatbot/issues)
- **Documentation**: [docs/](docs/)
- **Production**: [https://alicechatbot.com/](https://alicechatbot.com/)
