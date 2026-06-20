import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

DATA_PATH = Path(__file__).parent / "data" / "questions.json"
CHROMA_PATH = Path(__file__).parent / "chroma_db"

print("Loading embedding model (first run downloads it, then it's cached locally)...")
model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=str(CHROMA_PATH))
collection = client.get_or_create_collection("interview_bank")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    questions = json.load(f)

ids = []
documents = []
embeddings = []
metadatas = []

for i, q in enumerate(questions):
    # We embed a slightly richer string than just the raw question, so the
    # model has role/company/skill context baked into the meaning it captures.
    text_to_embed = f"{q['role']} interview question for {q['company']} on {q['skill_tag']}: {q['question']}"

    ids.append(str(i))
    documents.append(q["question"])
    embeddings.append(model.encode(text_to_embed).tolist())

    # ChromaDB metadata values must be plain strings/numbers/bools - it can't
    # store a Python list directly, so rubric_points gets joined into one string
    # and split back apart again when we retrieve it in rag.py.
    metadatas.append({
        "role": q["role"],
        "company": q["company"],
        "skill_tag": q["skill_tag"],
        "difficulty": q.get("difficulty", "medium"),
        "rubric": "; ".join(q["rubric_points"]),
    })

# If you re-run this script (e.g. after editing questions.json), clear out
# whatever was there before so you don't end up with duplicate entries.
existing_ids = collection.get(include=[])["ids"]
if existing_ids:
    collection.delete(ids=existing_ids)

collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
print(f"Ingested {len(questions)} questions into ChromaDB at: {CHROMA_PATH}")