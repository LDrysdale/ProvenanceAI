# redis_chat_history.py

import os
import httpx
import json
from datetime import datetime

# Load Upstash credentials from environment
UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

if not UPSTASH_REDIS_REST_URL or not UPSTASH_REDIS_REST_TOKEN:
    raise RuntimeError("Upstash Redis credentials not set in environment variables.")

HEADERS = {
    "Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"
}

async def store_chat_message(
    user_id: str,
    question: str,
    answer: str,
    chat_id: str,
    chat_subject: str,
):
    key = f"chat_history:{user_id}:{chat_id}"
    now_iso = datetime.utcnow().isoformat()
    record = {
        "question": question,
        "answer": answer,
        "createdAt": now_iso,
        "chat_id": chat_id,
        "chat_subject": chat_subject,
    }

    async with httpx.AsyncClient() as client:
        # Use LPUSH to prepend new messages to the list
        response = await client.post(
            f"{UPSTASH_REDIS_REST_URL}/lpush/{key}",
            headers=HEADERS,
            content=json.dumps(record)
        )
        if response.status_code != 200:
            raise RuntimeError(f"Failed to store chat message: {response.text}")

async def get_chat_history(key: str, limit: int = 50):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{UPSTASH_REDIS_REST_URL}/lrange/{key}/0/{limit - 1}",
            headers=HEADERS
        )
        if res.status_code == 200:
            data = res.json()
            # Redis returns a list of JSON strings, decode each
            results = data.get("result", [])
            history = []
            for item in results:
                try:
                    history.append(json.loads(item))
                except json.JSONDecodeError:
                    continue
            return history
        else:
            return []
