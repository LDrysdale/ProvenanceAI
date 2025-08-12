import os
import asyncio
from datetime import datetime
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec

# Load Pinecone environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Initialize Pinecone client and index
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

# Load model once
model = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_text(text, max_words=100):
    """Split text into smaller chunks of max_words length"""
    words = text.split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]

async def upsert_to_pinecone(user_id: str, chat_id: str, prompt: str, answer: str, vector_id: str):
    """Embeds and upserts a prompt/answer pair to Pinecone, with chunking if needed"""
    chunks = chunk_text(prompt)

    loop = asyncio.get_event_loop()
    tasks = []

    for i, chunk in enumerate(chunks):
        chunk_vector_id = f"{vector_id}_chunk{i}"
        embedding = model.encode(chunk).tolist()

        metadata = {
            "user_id": user_id,
            "chat_id": chat_id,
            "prompt": chunk,
            "answer": answer,
            "chunkIndex": i,
            "createdAt": datetime.utcnow().isoformat()
        }

        upsert_data = [(chunk_vector_id, embedding, metadata)]
        task = loop.run_in_executor(None, lambda: index.upsert(vectors=upsert_data))
        tasks.append(task)

    await asyncio.gather(*tasks)
