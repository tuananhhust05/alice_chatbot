"""
Startup migrations — ensure required data exists.
Runs on orchestrator startup to prevent runtime errors.
"""
from datetime import datetime, timezone
from app.database import get_db
from app.services.vectorstore import ensure_ragdata_class

# Default system prompt (used if no prompt configured in DB)
DEFAULT_SYSTEM_PROMPT = """You are Alice, a helpful and intelligent AI assistant. You provide clear, accurate, and well-structured responses.

When answering questions:
- Be concise but thorough
- Use markdown formatting when appropriate
- If you're unsure about something, say so
- Be friendly and professional

If the user has uploaded a file and context from it is provided, use that context to answer their questions accurately. Always cite or reference the relevant parts of the document when answering file-related questions."""

DEFAULT_RAG_PROMPT_TEMPLATE = """You are Alice, a helpful AI assistant. You MUST prioritize the knowledge provided below over your general training knowledge.

IMPORTANT INSTRUCTIONS:
1. ALWAYS use the provided context as your PRIMARY source of information
2. If the context contains relevant information, you MUST use it - do NOT rely on your pre-trained knowledge
3. If your pre-trained knowledge conflicts with the context, ALWAYS prefer the context
4. Only use your general knowledge to supplement when the context is incomplete
5. Clearly cite which part of the context supports your answer

Here is the authoritative context from the knowledge base:

---
{context}
---

Answer the user's question based PRIMARILY on the above context. If the context directly addresses the question, use that information exclusively. Only supplement with general knowledge if absolutely necessary and clearly indicate when doing so."""


async def run_migrations():
    """Run all startup migrations."""
    await _ensure_prompts()
    await ensure_ragdata_class()
    print("[Orchestrator] Migrations completed")


async def _ensure_prompts():
    """Ensure default prompts exist in MongoDB."""
    db = get_db()
    existing = await db.prompts.find_one({"key": "system_prompts"})

    if not existing:
        await db.prompts.insert_one({
            "key": "system_prompts",
            "system_prompt": DEFAULT_SYSTEM_PROMPT,
            "rag_prompt_template": DEFAULT_RAG_PROMPT_TEMPLATE,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })
        print("[Orchestrator] Default prompts created in MongoDB")
    else:
        print("[Orchestrator] Prompts already exist in MongoDB")
