from groq import AsyncGroq
from typing import List, Optional, AsyncGenerator
from sentence_transformers import SentenceTransformer
from app.config import get_settings

settings = get_settings()

groq_client: AsyncGroq = None
embed_model: SentenceTransformer = None


def init_groq():
    """Initialize Groq client."""
    global groq_client
    groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)


def init_embeddings():
    """Initialize sentence-transformers embedding model."""
    global embed_model
    print("[Orchestrator] Loading all-MiniLM-L6-v2 embedding model...")
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    print("[Orchestrator] Embedding model loaded (dim=384)")


async def get_chat_completion(
    messages: List[dict],
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """Get chat completion from Groq LLM (non-streaming)."""
    if not groq_client:
        init_groq()

    formatted_messages = []
    if system_prompt:
        formatted_messages.append({"role": "system", "content": system_prompt})
    formatted_messages.extend(messages)

    response = await groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=formatted_messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


async def get_chat_completion_stream(
    messages: List[dict],
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> AsyncGenerator[str, None]:
    """Stream chat completion from Groq LLM."""
    if not groq_client:
        init_groq()

    formatted_messages = []
    if system_prompt:
        formatted_messages.append({"role": "system", "content": system_prompt})
    formatted_messages.extend(messages)

    stream = await groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=formatted_messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


def get_embeddings_sync(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using all-MiniLM-L6-v2 (synchronous)."""
    global embed_model
    if not embed_model:
        init_embeddings()
    embeddings = embed_model.encode(texts, show_progress_bar=False)
    return [emb.tolist() for emb in embeddings]


async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings (async wrapper)."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_embeddings_sync, texts)
