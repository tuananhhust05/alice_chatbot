import time
from bson import ObjectId
from app.database import get_db
from app.services.file_processor import extract_text, chunk_text, build_tabular_preview
from app.services.vectorstore import create_file_collection, store_chunks
from app.services.llm import get_embeddings
from app.services.event_emitter import emit_file_event


async def handle_file_request(data: dict) -> dict:
    """
    Process a file request from Kafka:
    1. Extract text from file
    2. Chunk text
    3. Generate embeddings
    4. Store in Weaviate
    5. Emit analytics event to kafkaflow
    6. Return chunk_count + weaviate_class
    """
    file_id = data["file_id"]
    file_path = data["file_path"]
    file_type = data["file_type"]
    start_time = time.time()
    success = True
    error_msg = None
    chunk_count_result = 0

    preview_table = None

    try:
        # Extract text
        text = extract_text(file_path, file_type)
        if not text.strip():
            raise ValueError("Could not extract any text from the file")

        # Optional preview for tabular formats (for UI table display)
        if file_type in {"csv", "xlsx", "xls"}:
            preview_table = build_tabular_preview(file_path, file_type)

        # Chunk
        chunks = chunk_text(text)
        chunk_count_result = len(chunks)

        # Create Weaviate collection
        collection_name = await create_file_collection(file_id)

        # Embeddings
        chunk_texts = [c["content"] for c in chunks]
        embeddings = await get_embeddings(chunk_texts)

        # Store in Weaviate
        for chunk in chunks:
            chunk["file_id"] = file_id
        await store_chunks(collection_name, chunks, embeddings)

        # Update file record in MongoDB
        file_record_id = data.get("file_record_id")
        if file_record_id:
            db = get_db()
            await db.files.update_one(
                {"_id": ObjectId(file_record_id)},
                {"$set": {
                    "chunk_count": len(chunks),
                    "weaviate_class": collection_name,
                    "status": "completed",
                }}
            )

    except Exception as e:
        success = False
        error_msg = str(e)
        raise

    finally:
        latency_ms = int((time.time() - start_time) * 1000)

        # Emit analytics event (fire-and-forget)
        try:
            await emit_file_event(
                conversation_id=data.get("conversation_id", ""),
                user_id=data.get("user_id", ""),
                file_id=file_id,
                file_type=file_type,
                original_name=data.get("original_name", ""),
                file_size=data.get("file_size", 0),
                chunk_count=chunk_count_result,
                latency_ms=latency_ms,
                success=success,
                error=error_msg,
            )
        except Exception as e:
            print(f"[Orchestrator] Event emit error (non-fatal): {e}")

    return {
        "chunk_count": len(chunks),
        "weaviate_class": collection_name,
        "original_name": data.get("original_name", ""),
        "file_size": data.get("file_size", 0),
        "file_type": data.get("file_type", ""),
        "conversation_id": data.get("conversation_id", ""),
        "preview_table": preview_table,
    }
