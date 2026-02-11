"""
Handle RAG data file processing from admin uploads.
Chunks by sentence boundaries respecting model token limits.
"""
from bson import ObjectId
from app.database import get_db
from app.services.file_processor import extract_text
from app.services.llm import get_embeddings
from app.services.vectorstore import store_ragdata_chunks

# all-MiniLM-L6-v2 max token = 256 tokens ≈ ~200 words ≈ ~1000 chars
MAX_CHUNK_CHARS = 1000
OVERLAP_CHARS = 100


def chunk_by_sentences(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[dict]:
    """
    Chunk text by sentence boundaries.
    If a sentence exceeds max_chars, split at word boundary.
    """
    import re

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = ""
    chunk_index = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # If single sentence exceeds limit, split by words
        if len(sentence) > max_chars:
            if current_chunk:
                chunks.append({"content": current_chunk.strip(), "chunk_index": chunk_index})
                chunk_index += 1
                current_chunk = ""

            words = sentence.split()
            word_chunk = ""
            for word in words:
                if len(word_chunk) + len(word) + 1 > max_chars:
                    if word_chunk:
                        chunks.append({"content": word_chunk.strip(), "chunk_index": chunk_index})
                        chunk_index += 1
                    word_chunk = word
                else:
                    word_chunk = f"{word_chunk} {word}" if word_chunk else word
            if word_chunk:
                current_chunk = word_chunk
            continue

        # Normal case: add sentence to current chunk
        if len(current_chunk) + len(sentence) + 1 > max_chars:
            if current_chunk:
                chunks.append({"content": current_chunk.strip(), "chunk_index": chunk_index})
                chunk_index += 1
            current_chunk = sentence
        else:
            current_chunk = f"{current_chunk} {sentence}" if current_chunk else sentence

    # Don't forget last chunk
    if current_chunk.strip():
        chunks.append({"content": current_chunk.strip(), "chunk_index": chunk_index})

    return chunks


async def handle_ragdata_request(data: dict) -> dict:
    """
    Process RAG data file from admin upload:
    1. Extract text from file
    2. Chunk by sentences (respecting model token limits)
    3. Vectorize with all-MiniLM-L6-v2
    4. Store in Weaviate RagData class
    5. Update MongoDB record
    """
    file_id = data["file_id"]
    record_id = data["record_id"]
    file_path = data["file_path"]
    file_type = data["file_type"]
    original_name = data.get("original_name", "")

    db = get_db()

    # 1. Extract text
    text = extract_text(file_path, file_type)
    if not text.strip():
        raise ValueError("Could not extract any text from the file")

    # 2. Chunk by sentences
    chunks = chunk_by_sentences(text)

    # Add metadata
    for chunk in chunks:
        chunk["file_id"] = file_id
        chunk["file_name"] = original_name

    # 3. Vectorize
    chunk_texts = [c["content"] for c in chunks]
    embeddings = await get_embeddings(chunk_texts)

    # 4. Store in Weaviate
    await store_ragdata_chunks(chunks, embeddings)

    # 5. Update MongoDB record
    await db.ragdata.update_one(
        {"_id": ObjectId(record_id)},
        {"$set": {
            "chunk_count": len(chunks),
            "status": "completed",
        }}
    )

    return {
        "chunk_count": len(chunks),
        "original_name": original_name,
    }
