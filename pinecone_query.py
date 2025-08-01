import os
from sentence_transformers import SentenceTransformer
import pinecone

# Load environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Initialize Pinecone
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
index = pinecone.Index(PINECONE_INDEX_NAME)

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

def query_pinecone(user_id: str, input_prompt: str, top_k: int = 5):
    # Generate embedding for the query prompt
    query_vector = model.encode(input_prompt).tolist()

    # Query Pinecone with metadata filter
    response = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        filter={"user_id": user_id}
    )

    # Extract matches
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
