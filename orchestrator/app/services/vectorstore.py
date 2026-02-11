import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery, Filter
from app.config import get_settings
import hashlib

settings = get_settings()

weaviate_client: weaviate.WeaviateClient = None

RAGDATA_CLASS = "RagData"


async def connect_weaviate():
    """Connect to Weaviate instance."""
    global weaviate_client
    weaviate_client = weaviate.connect_to_custom(
        http_host=settings.WEAVIATE_URL.replace("http://", "").split(":")[0],
        http_port=int(settings.WEAVIATE_URL.split(":")[-1]),
        http_secure=False,
        grpc_host=settings.WEAVIATE_URL.replace("http://", "").split(":")[0],
        grpc_port=50051,
        grpc_secure=False,
    )
    print("[Orchestrator] Connected to Weaviate")


async def close_weaviate():
    """Close Weaviate connection."""
    global weaviate_client
    if weaviate_client:
        weaviate_client.close()
        print("[Orchestrator] Disconnected from Weaviate")


# ===== RagData class (global knowledge base) =====

async def ensure_ragdata_class():
    """Migration: create RagData class in Weaviate if it doesn't exist."""
    if weaviate_client.collections.exists(RAGDATA_CLASS):
        print(f"[Orchestrator] Weaviate class '{RAGDATA_CLASS}' already exists")
        return

    weaviate_client.collections.create(
        name=RAGDATA_CLASS,
        vectorizer_config=Configure.Vectorizer.none(),
        properties=[
            Property(name="content", data_type=DataType.TEXT),
            Property(name="chunk_index", data_type=DataType.INT),
            Property(name="file_id", data_type=DataType.TEXT),
            Property(name="file_name", data_type=DataType.TEXT),
            Property(name="metadata", data_type=DataType.TEXT),
        ],
    )
    print(f"[Orchestrator] Weaviate class '{RAGDATA_CLASS}' created (dim=384, all-MiniLM-L6-v2)")


async def store_ragdata_chunks(chunks: list[dict], embeddings: list[list[float]]):
    """Store RAG data chunks with embeddings in the global RagData class."""
    collection = weaviate_client.collections.get(RAGDATA_CLASS)

    with collection.batch.dynamic() as batch:
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            batch.add_object(
                properties={
                    "content": chunk["content"],
                    "chunk_index": chunk.get("chunk_index", i),
                    "file_id": chunk.get("file_id", ""),
                    "file_name": chunk.get("file_name", ""),
                    "metadata": chunk.get("metadata", ""),
                },
                vector=embedding,
            )


async def search_ragdata(query_embedding: list[float], limit: int = 5) -> list[dict]:
    """Search for similar chunks in the global RagData knowledge base."""
    try:
        if not weaviate_client.collections.exists(RAGDATA_CLASS):
            return []

        collection = weaviate_client.collections.get(RAGDATA_CLASS)
        results = collection.query.near_vector(
            near_vector=query_embedding,
            limit=limit,
            return_metadata=MetadataQuery(distance=True),
        )

        chunks = []
        for obj in results.objects:
            chunks.append({
                "content": obj.properties["content"],
                "file_name": obj.properties.get("file_name", ""),
                "chunk_index": obj.properties.get("chunk_index", 0),
                "distance": obj.metadata.distance if obj.metadata else None,
            })
        return chunks
    except Exception as e:
        print(f"[Orchestrator] Error searching RagData: {e}")
        return []


async def delete_ragdata_by_file(file_id: str):
    """Delete all chunks from RagData for a specific file."""
    try:
        collection = weaviate_client.collections.get(RAGDATA_CLASS)
        # Weaviate batch delete by filter
        collection.data.delete_many(
            where=Filter.by_property("file_id").equal(file_id)
        )
    except Exception as e:
        print(f"[Orchestrator] Error deleting RagData: {e}")


# ===== User file collections (per-conversation) =====

def get_collection_name(file_id: str) -> str:
    """Generate a valid Weaviate collection name from file_id."""
    hash_str = hashlib.md5(file_id.encode()).hexdigest()[:12]
    return f"FileChunk_{hash_str}"


async def create_file_collection(file_id: str) -> str:
    """Create a Weaviate collection for a file's chunks."""
    collection_name = get_collection_name(file_id)

    if weaviate_client.collections.exists(collection_name):
        weaviate_client.collections.delete(collection_name)

    weaviate_client.collections.create(
        name=collection_name,
        vectorizer_config=Configure.Vectorizer.none(),
        properties=[
            Property(name="content", data_type=DataType.TEXT),
            Property(name="chunk_index", data_type=DataType.INT),
            Property(name="file_id", data_type=DataType.TEXT),
            Property(name="metadata", data_type=DataType.TEXT),
        ],
    )
    return collection_name


async def store_chunks(collection_name: str, chunks: list[dict], embeddings: list[list[float]]):
    """Store text chunks with their embeddings in Weaviate."""
    collection = weaviate_client.collections.get(collection_name)

    with collection.batch.dynamic() as batch:
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            batch.add_object(
                properties={
                    "content": chunk["content"],
                    "chunk_index": i,
                    "file_id": chunk.get("file_id", ""),
                    "metadata": chunk.get("metadata", ""),
                },
                vector=embedding,
            )


async def search_chunks(collection_name: str, query_embedding: list[float], limit: int = 5) -> list[dict]:
    """Search for similar chunks in a file collection."""
    try:
        collection = weaviate_client.collections.get(collection_name)
        results = collection.query.near_vector(
            near_vector=query_embedding,
            limit=limit,
            return_metadata=MetadataQuery(distance=True),
        )

        chunks = []
        for obj in results.objects:
            chunks.append({
                "content": obj.properties["content"],
                "chunk_index": obj.properties["chunk_index"],
                "distance": obj.metadata.distance if obj.metadata else None,
            })
        return chunks
    except Exception as e:
        print(f"[Orchestrator] Error searching Weaviate: {e}")
        return []


async def delete_file_collection(file_id: str):
    """Delete a file's collection from Weaviate."""
    collection_name = get_collection_name(file_id)
    if weaviate_client.collections.exists(collection_name):
        weaviate_client.collections.delete(collection_name)
