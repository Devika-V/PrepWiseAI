from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = Path(__file__).parent / "chroma_db"

# Loading the embedding model takes a couple of seconds, so we load it once
# and reuse it, rather than reloading it on every single function call.
_model = None
_collection = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        _collection = client.get_collection("interview_bank")
    return _collection


def retrieve_questions(role: str, company: str, skill_tag: str = None, top_k: int = 3):
    """
    Returns up to top_k relevant questions (with rubric points) for a given
    role + company, optionally narrowed down to one skill_tag.

    This is the function later days (LangGraph, FastAPI routes) will import
    and call - it's the only "door" into the knowledge base the rest of the
    app needs to know about.
    """
    model = _get_model()
    collection = _get_collection()

    conditions = [{"role": {"$eq": role}}, {"company": {"$eq": company}}]
    if skill_tag:
        conditions.append({"skill_tag": {"$eq": skill_tag}})
    where_filter = conditions[0] if len(conditions) == 1 else {"$and": conditions}

    query_text = f"{role} interview question for {company}"
    if skill_tag:
        query_text += f" on {skill_tag}"
    query_embedding = model.encode(query_text).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter,
    )

    matches = []
    # results["documents"][0] and results["metadatas"][0] line up index-for-index
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        matches.append({
            "question": doc,
            "skill_tag": meta["skill_tag"],
            "difficulty": meta["difficulty"],
            "rubric_points": meta["rubric"].split("; "),
        })
    return matches