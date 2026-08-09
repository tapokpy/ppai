import chromadb
import httpx
from sentence_transformers import SentenceTransformer

from app.config import settings

_embedder = SentenceTransformer("all-MiniLM-L6-v2")

_chroma_url = httpx.URL(settings.chromadb_url)
_chroma_client = chromadb.HttpClient(host=_chroma_url.host, port=_chroma_url.port)
_collection = _chroma_client.get_or_create_collection("knowledge_base")


def search(query: str, top_k: int = 3) -> tuple[list[str], float]:
    embedding = _embedder.encode(query).tolist()
    result = _collection.query(query_embeddings=[embedding], n_results=top_k)

    documents = result["documents"][0] if result["documents"] else []
    distances = result["distances"][0] if result["distances"] else []
    if not distances:
        return [], 0.0

    # Chroma по умолчанию возвращает косинусное расстояние (0 = идентично).
    # Переводим в схожесть (1 = идентично) для сравнения с RAG_SCORE_THRESHOLD.
    best_similarity = 1 - min(distances)
    return documents, best_similarity
