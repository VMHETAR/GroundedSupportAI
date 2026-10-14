"""Qdrant local vector store wrapper."""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

_client = None

def get_client(path="./qdrant_data"):
    global _client
    if _client is None:
        _client = QdrantClient(path=path)
    return _client

def ensure_collection(client, name, dim):
    try:
        info = client.get_collection(name)
        if info.config.params.vectors.size != dim:
            client.recreate_collection(name, vectors_config=VectorParams(size=dim, distance=Distance.COSINE))
    except Exception:
        client.create_collection(name, vectors_config=VectorParams(size=dim, distance=Distance.COSINE))

def upsert(client, collection, ids, vectors, payloads):
    points = [PointStruct(id=ids[i] if isinstance(ids[i], str) else str(uuid.uuid4()),
                          vector=list(map(float, vectors[i])), payload=payloads[i])
              for i in range(len(vectors))]
    # Qdrant accepts UUID strings or ints; use deterministic UUID5 from chunk id
    import uuid as _uuid
    for p in points:
        try:
            _uuid.UUID(p.id)
        except Exception:
            p.id = str(_uuid.uuid5(_uuid.NAMESPACE_URL, p.id))
    client.upsert(collection_name=collection, points=points)

def search(client, collection, vector, top_n=5):
    res = client.query_points(collection_name=collection, query=list(map(float, vector)), limit=top_n).points
    out = []
    for h in res:
        out.append({"score": float(h.score), "text": h.payload.get("text", ""),
                    "source": h.payload.get("source", ""), "section": h.payload.get("section", ""),
                    "title": h.payload.get("title", "")})
    return out
