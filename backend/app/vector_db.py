import os
import chromadb
from typing import List, Dict

_client = chromadb.PersistentClient(path=os.path.join(os.path.dirname(__file__), "..", "chroma"))
_collection = _client.get_or_create_collection(name="tasks", metadata={"hnsw:space": "cosine"})

def upsert_embeddings(items: List[Dict]):
    """Add embeddings to the vector db""" 
    _collection.add(
        ids=[it["id"] for it in items],
        embeddings=[it["values"] for it in items],
        metadatas=[it.get("metadata", {}) for it in items],
    )

def query_embeddings(embedding: list[float], top_k: int = 5, filter: Dict | None = None):
    """Query the vector db for similar embeddings"""
    where = None
    if filter and "task" in filter and "$eq" in filter["task"]:
        where = {"task": filter["task"]["$eq"]}

    res = _collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where=where
    )
    matches = []
    for i in range(len(res.get("ids", [[]])[0])):
        meta = res["metadatas"][0][i] if res.get("metadatas") else {}
        matches.append({"metadata": meta})
    return matches