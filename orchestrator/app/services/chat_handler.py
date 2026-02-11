import time
from datetime import datetime
from bson import ObjectId
from app.database import get_db
from app.services.llm import (
    get_chat_completion, get_chat_completion_stream, get_embeddings,
)
from app.services.vectorstore import search_ragdata
from app.services.redis_client import stream_update
from app.services.event_emitter import emit_llm_event
from app.services.security import (
    detect_prompt_injection,
    sanitize_input,
    sanitize_file_content,
    mask_pii,
    check_system_prompt_leak,
    log_security_event,
)

# How many streaming chunks before we flush to Redis
FLUSH_INTERVAL = 10

# ===== TOKEN LIMITS =====
# Groq free tier: 12K tokens/minute for llama-3.3-70b-versatile
# We need to stay well under this limit
MAX_TOTAL_TOKENS = 8000         # Max tokens for entire request (prompt + expected response)
MAX_RESPONSE_TOKENS = 1500      # Reserve tokens for response
MAX_CONTEXT_TOKENS = 6000       # Max for system prompt + history + user message
MAX_HISTORY_MESSAGES = 10       # Limit conversation history
MAX_MESSAGE_TOKENS = 4000       # Max tokens per single message (truncate if longer)

# Rough estimate: 1 token ≈ 4 characters for English text
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Estimate token count from text length."""
    if not text:
        return 0
    return len(text) // CHARS_PER_TOKEN + 1


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to approximately max_tokens."""
    max_chars = max_tokens * CHARS_PER_TOKEN
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n... [Content truncated to fit token limit]"


def truncate_message_content(content: str, max_tokens: int = MAX_MESSAGE_TOKENS) -> str:
    """Truncate a single message content if too long."""
    # Check if message contains file content
    if "\n\nFile content:\n" in content:
        parts = content.split("\n\nFile content:\n", 1)
        user_text = parts[0]
        file_content = parts[1] if len(parts) > 1 else ""
        
        # Estimate tokens for user text (keep it fully)
        user_tokens = estimate_tokens(user_text)
        
        # Remaining tokens for file content
        remaining_tokens = max_tokens - user_tokens - 50  # 50 tokens buffer
        
        if remaining_tokens > 100:  # At least 100 tokens for file content
            truncated_file = truncate_to_tokens(file_content, remaining_tokens)
            return f"{user_text}\n\nFile content:\n{truncated_file}"
        else:
            # Not enough room for file content
            return f"{user_text}\n\n[File content omitted due to token limit]"
    
    # Regular message without file
    return truncate_to_tokens(content, max_tokens)


def build_messages_with_token_limit(
    history_messages: list[dict],
    system_prompt: str,
    max_tokens: int = MAX_CONTEXT_TOKENS,
) -> list[dict]:
    """
    Build message list that fits within token limit.
    Prioritizes: system prompt > current message > recent history
    """
    if not history_messages:
        return []
    
    # Current message (last one) is always included
    current_msg = history_messages[-1]
    history = history_messages[:-1]
    
    # Estimate system prompt tokens
    system_tokens = estimate_tokens(system_prompt)
    
    # Truncate current message if needed
    current_content = truncate_message_content(current_msg["content"], MAX_MESSAGE_TOKENS)
    current_tokens = estimate_tokens(current_content)
    
    # Available tokens for history
    available_for_history = max_tokens - system_tokens - current_tokens - 100  # buffer
    
    if available_for_history < 100:
        # Not enough room for history, just return current message
        return [{"role": current_msg["role"], "content": current_content}]
    
    # Build history from most recent, fitting within limit
    selected_history = []
    history_tokens_used = 0
    
    # Limit history length first
    history = history[-MAX_HISTORY_MESSAGES:]
    
    for msg in reversed(history):
        msg_tokens = estimate_tokens(msg["content"])
        
        # If single message is too long, truncate it
        if msg_tokens > MAX_MESSAGE_TOKENS // 2:
            msg_content = truncate_to_tokens(msg["content"], MAX_MESSAGE_TOKENS // 2)
            msg_tokens = estimate_tokens(msg_content)
        else:
            msg_content = msg["content"]
        
        if history_tokens_used + msg_tokens <= available_for_history:
            selected_history.insert(0, {"role": msg["role"], "content": msg_content})
            history_tokens_used += msg_tokens
        else:
            # No more room
            break
    
    # Add current message
    selected_history.append({"role": current_msg["role"], "content": current_content})
    
    return selected_history


async def _load_prompts() -> tuple[str, str]:
    """Load system prompt and RAG template from MongoDB."""
    db = get_db()
    prompt_doc = await db.prompts.find_one({"key": "system_prompts"})
    if prompt_doc:
        return (
            prompt_doc.get("system_prompt", "You are Alice, a helpful AI assistant."),
            prompt_doc.get("rag_prompt_template", "Context:\n---\n{context}\n---\nAnswer the user's question."),
        )
    # Fallback
    return ("You are Alice, a helpful AI assistant.", "Context:\n---\n{context}\n---\nAnswer the user's question.")


def _build_rag_prompt(template: str, context_texts: list[str], max_tokens: int = 2000) -> str:
    """Build RAG prompt from template + context, with token limit."""
    # Limit context to fit within max_tokens
    context_parts = []
    tokens_used = 0
    
    for ctx in context_texts:
        ctx_tokens = estimate_tokens(ctx)
        if tokens_used + ctx_tokens <= max_tokens:
            context_parts.append(ctx)
            tokens_used += ctx_tokens
        else:
            # Truncate this context to fit remaining
            remaining = max_tokens - tokens_used
            if remaining > 100:
                context_parts.append(truncate_to_tokens(ctx, remaining))
            break
    
    context = "\n\n".join(context_parts)
    return template.format(context=context)


async def handle_chat_request(data: dict) -> dict:
    """
    Process a chat request from Kafka with STREAMING:
    1. Security checks (prompt injection, PII)
    2. Load prompts from MongoDB
    3. Load conversation history (with token limit)
    4. Retrieve relevant data from RagData (global KB)
    5. Stream Groq LLM response
    6. Post-response security checks
    7. Emit analytics event
    
    Token management ensures we stay under Groq's 12K TPM limit.
    """
    request_id = data["request_id"]
    conversation_id = data["conversation_id"]
    message = data["message"]
    user_id = data["user_id"]
    generate_title = data.get("generate_title", False)

    db = get_db()
    start_time = time.time()
    has_rag = False
    success = True
    error_msg = None
    injection_detected = False

    # ===== SECURITY: Input Validation =====
    # 1. Check for prompt injection attempts
    is_suspicious, matched_patterns = detect_prompt_injection(message)
    if is_suspicious:
        injection_detected = True
        log_security_event(
            event_type="prompt_injection_attempt",
            user_id=user_id,
            details={
                "request_id": request_id,
                "conversation_id": conversation_id,
                "matched_patterns": matched_patterns[:3],  # Log first 3 patterns
                "message_preview": message[:200],
            },
            severity="warning"
        )
        # Don't block, but sanitize and continue with warning
    
    # 2. Sanitize input
    sanitized_message = sanitize_input(message)
    
    # 3. Handle file content separately
    if "\n\nFile content:\n" in sanitized_message:
        parts = sanitized_message.split("\n\nFile content:\n", 1)
        user_text = parts[0]
        file_content = parts[1] if len(parts) > 1 else ""
        
        # Extract filename from file content marker if present
        filename = "uploaded_file"
        file_marker_match = None
        import re
        file_marker_match = re.search(r'\[File:\s*([^\]]+)\]', file_content)
        if file_marker_match:
            filename = file_marker_match.group(1)
        
        # Sanitize file content
        sanitized_file = sanitize_file_content(file_content, filename)
        sanitized_message = f"{user_text}\n\nFile content:\n{sanitized_file}"
    
    # 4. Mask PII in message (for logging, keep original for LLM)
    masked_message, pii_stats = mask_pii(message)
    if pii_stats:
        log_security_event(
            event_type="pii_detected",
            user_id=user_id,
            details={
                "request_id": request_id,
                "pii_types": list(pii_stats.keys()),
                "counts": pii_stats,
            },
            severity="info"
        )

    # 1. Load prompts from DB
    system_prompt, rag_prompt_template = await _load_prompts()

    # 2. Load conversation
    conversation = await db.conversations.find_one({
        "_id": ObjectId(conversation_id),
        "user_id": user_id,
    })

    if not conversation:
        raise ValueError(f"Conversation {conversation_id} not found")

    # Build message history (limited)
    history_messages = []
    for msg in conversation.get("messages", [])[-MAX_HISTORY_MESSAGES:]:
        history_messages.append({
            "role": msg["role"],
            "content": msg["content"],
        })
    history_messages.append({"role": "user", "content": message})

    # 3. Collect context from RAG sources (limited)
    all_context_texts = []

    try:
        # Only search RAG if message isn't too long (file content)
        search_query = message.split("\n\nFile content:")[0][:500]  # Use only user text for search
        query_embeddings = await get_embeddings([search_query])
        ragdata_chunks = await search_ragdata(query_embeddings[0], limit=5)  # Increased for better coverage
        for chunk in ragdata_chunks:
            if chunk.get("distance", 999) < 1.0:  # Relaxed threshold (0=identical, 2=opposite)
                all_context_texts.append(
                    f"[Knowledge Base: {chunk.get('file_name', 'KB')}]\n{chunk['content']}"
                )
    except Exception as e:
        print(f"[Orchestrator] RagData search error: {e}")

    # Build final system prompt with context (limited tokens)
    if all_context_texts:
        has_rag = True
        system_prompt = _build_rag_prompt(rag_prompt_template, all_context_texts, max_tokens=1500)

    # Apply token limits to messages
    final_messages = build_messages_with_token_limit(
        history_messages,
        system_prompt,
        max_tokens=MAX_CONTEXT_TOKENS,
    )

    # Log token estimates for debugging
    total_tokens = estimate_tokens(system_prompt) + sum(estimate_tokens(m["content"]) for m in final_messages)
    print(f"[Orchestrator] Estimated tokens: {total_tokens} (limit: {MAX_CONTEXT_TOKENS})")

    # 4. Stream LLM response
    accumulated = ""
    chunk_count = 0
    await stream_update(request_id, "", finished=0)

    try:
        async for text_chunk in get_chat_completion_stream(
            messages=final_messages,
            system_prompt=system_prompt,
            max_tokens=MAX_RESPONSE_TOKENS,
        ):
            accumulated += text_chunk
            chunk_count += 1
            if chunk_count % FLUSH_INTERVAL == 0:
                await stream_update(request_id, accumulated, finished=0)
    except Exception as e:
        success = False
        error_msg = str(e)
        # Check if it's a rate limit error
        if "rate_limit" in str(e).lower() or "413" in str(e):
            error_msg = "Message too long. Please try with a shorter message or smaller file."
        raise

    ai_reply = accumulated
    latency_ms = int((time.time() - start_time) * 1000)

    # ===== SECURITY: Response Validation =====
    # Check for system prompt leak in response
    if check_system_prompt_leak(ai_reply, system_prompt):
        log_security_event(
            event_type="system_prompt_leak",
            user_id=user_id,
            details={
                "request_id": request_id,
                "conversation_id": conversation_id,
                "response_preview": ai_reply[:200],
            },
            severity="critical"
        )
        # Optionally redact or modify response
        # For now, just log for monitoring
    
    # Mask PII in response before saving (optional, based on policy)
    response_masked, response_pii = mask_pii(ai_reply)
    if response_pii:
        log_security_event(
            event_type="pii_in_response",
            user_id=user_id,
            details={
                "request_id": request_id,
                "pii_types": list(response_pii.keys()),
            },
            severity="info"
        )

    # Token estimates
    token_prompt_est = total_tokens
    token_completion_est = estimate_tokens(ai_reply)

    # Generate title if needed (separate API call with minimal tokens)
    title = None
    if generate_title:
        try:
            # Use only user text (not file content) for title
            title_text = message.split("\n\nFile content:")[0][:150]
            title_response = await get_chat_completion(
                messages=[{
                    "role": "user",
                    "content": f'Generate a short title (max 5 words) for this message. Only respond with the title: "{title_text}"',
                }],
                temperature=0.3,
                max_tokens=20,
            )
            title = title_response.strip().strip('"').strip("'")[:50]
        except Exception:
            title = None

    # Save assistant message to MongoDB
    assistant_message = {
        "role": "assistant",
        "content": ai_reply,
        "timestamp": datetime.utcnow(),
    }
    await db.conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {
            "$push": {"messages": assistant_message},
            "$set": {"updated_at": datetime.utcnow()},
        }
    )

    if title:
        await db.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {"title": title}}
        )

    # 5. Emit analytics event
    try:
        await emit_llm_event(
            conversation_id=conversation_id,
            user_id=user_id,
            message=masked_message[:500],  # Use masked version for analytics
            reply=ai_reply[:500],
            model="llama-3.3-70b-versatile",
            latency_ms=latency_ms,
            token_prompt=token_prompt_est,
            token_completion=token_completion_est,
            success=success,
            has_rag=has_rag,
            title=title,
            error=error_msg,
        )
    except Exception as e:
        print(f"[Orchestrator] Event emit error (non-fatal): {e}")

    # Log security summary if issues detected
    if injection_detected or pii_stats:
        log_security_event(
            event_type="request_security_summary",
            user_id=user_id,
            details={
                "request_id": request_id,
                "injection_detected": injection_detected,
                "pii_detected": bool(pii_stats),
                "pii_types": list(pii_stats.keys()) if pii_stats else [],
            },
            severity="info"
        )

    return {"reply": ai_reply, "title": title}
