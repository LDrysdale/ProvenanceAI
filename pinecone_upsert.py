import os
import asyncio
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import google.generativeai as genai

# ==========================
# Pinecone Setup
# ==========================
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
PINECONE_ENV = os.getenv("PINECONE_ENV")

pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
index = pc.Index(PINECONE_INDEX_NAME)

# ==========================
# Embedding Model
# ==========================
model = SentenceTransformer("all-MiniLM-L6-v2")

# ==========================
# Gemini Setup
# ==========================
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# ==========================
# Helpers
# ==========================
def chunk_text(text: str, max_words: int = 100):
    """Split text into smaller chunks of max_words length."""
    words = text.split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]


def analyze_with_gemini(text: str) -> dict:
    """Use Gemini to analyze sentiment and mood tags, return JSON."""
    prompt = f"""
    Analyze the following text for sentiment and mood.

    Requirements:
    - sentiment must be one of: "positive", "negative", "neutral"
    - mood_tags must be a list of 1–3 short descriptive words

    Return only valid JSON in this format:
    {{
      "sentiment": "positive|negative|neutral",
      "mood_tags": ["tag1", "tag2"]
    }}

    Text: "{text}"
    """
    response = gemini_model.generate_content(prompt)
    try:
        return json.loads(response.text)
    except Exception:
        return {"sentiment": "neutral", "mood_tags": []}

# ==========================
# Main Upsert Function
# ==========================
async def upsert_to_pinecone(
    user_id: str,
    entry_type: str,       # "diary", "ideaboard", or "qa"
    text: str,
    vector_id: str,
    chat_id: str | None = None,
    answer: str | None = None,
):
    """
    Generalized Pinecone upsert for diary, ideaboard, and Q&A.
    - Diary & Ideaboard → auto sentiment/mood tagging via Gemini
    - Q&A → can include answer and chat_id
    """
    sentiment, mood_tags = None, None

    # Enrich diary/ideaboard entries with Gemini analysis
    if entry_type in ["diary", "ideaboard"]:
        analysis = analyze_with_gemini(text)
        sentiment = analysis.get("sentiment")
        mood_tags = analysis.get("mood_tags")

    # Chunk text for embedding
    chunks = chunk_text(text)
    loop = asyncio.get_event_loop()
    tasks = []

    for i, chunk in enumerate(chunks):
        chunk_vector_id = f"{vector_id}_chunk{i}"
        embedding = model.encode(chunk).tolist()

        metadata = {
            "user_id": user_id,
            "entry_type": entry_type,
            "chunkIndex": i,
            "createdAt": datetime.utcnow().isoformat(),
            "text": chunk,
        }

        # Optional fields
        if chat_id:
            metadata["chat_id"] = chat_id
        if answer:
            metadata["answer"] = answer
        if sentiment:
            metadata["sentiment"] = sentiment
        if mood_tags:
            metadata["mood_tags"] = mood_tags

        upsert_data = [(chunk_vector_id, embedding, metadata)]
        task = loop.run_in_executor(None, lambda: index.upsert(vectors=upsert_data))
        tasks.append(task)

    await asyncio.gather(*tasks)
