import os
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

# Load environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
PINECONE_ENV = os.getenv("PINECONE_ENV")

# Initialize Pinecone client and index
pc = Pinecone(api_key=PINECONE_API_KEY,environment=PINECONE_ENV)
index = pc.Index(PINECONE_INDEX_NAME)

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def query_pinecone(user_id: str, input_prompt: str, top_k: int = 5):
    """Query Pinecone for relevant matches to the input prompt."""
    query_vector = model.encode(input_prompt).tolist()

    response = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        filter={"user_id": user_id}
    )

    results = []
    for match in response.get("matches", []):
        metadata = match.get("metadata", {})
        results.append({
            "score": match.get("score"),
            "prompt": metadata.get("prompt"),
            "answer": metadata.get("answer"),
            "chat_id": metadata.get("chat_id"),
            "user_id": metadata.get("user_id"),
            "createdAt": metadata.get("createdAt")
        })

    return results
