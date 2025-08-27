import uuid
import asyncio
from datetime import datetime

from pinecone_query import query_pinecone
from pinecone_upsert import upsert_to_pinecone
from chat_history import store_chat_message, get_chat_history
from sentence_transformers import SentenceTransformer

# Load model once
model = SentenceTransformer("all-MiniLM-L6-v2")


async def handle_user_prompt(user_id: str, chat_id: str, prompt: str, chat_subject: str):
    # Step 1: Get recent Redis history
    redis_key = f"chat_history:{user_id}:{chat_id}"
    redis_history = await get_chat_history(redis_key, limit=20)

    # Step 2: Query Pinecone for similar embeddings
    pinecone_matches = await query_pinecone(user_id, prompt, top_k=3)

    # Step 3: Construct context
    context_parts = []

    if redis_history:
        context_parts.append("Redis History:\n" + "\n".join(
            f"Q: {msg.get('question')}\nA: {msg.get('answer')}" for msg in redis_history if "question" in msg
        ))

    if pinecone_matches:
        context_parts.append("Semantic Matches:\n" + "\n".join(
            f"Q: {m['prompt']}\nA: {m['answer']}" for m in pinecone_matches
        ))

    context_text = "\n\n".join(context_parts)
    full_input = f"{context_text}\n\nUser: {prompt}\nAssistant:"

    # Step 4: Generate response using PaLM or HuggingFace (for now, dummy output)
    # Replace with actual PaLM or local model call
    answer = f"(Simulated answer based on context)\n\n{full_input[-300:]}"  # 🔁 Replace this with actual model inference

    # Step 5: Store in Redis
    await store_chat_message(
        user_id=user_id,
        question=prompt,
        answer=answer,
        chat_id=chat_id,
        chat_subject=chat_subject
    )

    # Step 6: Store in Pinecone
    vector_id = f"{user_id}_{chat_id}_{uuid.uuid4().hex[:8]}"
    await upsert_to_pinecone(
        user_id=user_id,
        chat_id=chat_id,
        prompt=prompt,
        answer=answer,
        vector_id=vector_id
    )

    return answer
