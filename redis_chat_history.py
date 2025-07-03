# redis_chat_history.py

import os
import httpx
import json
from datetime import datetime

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

if not UPSTASH_REDIS_REST_URL or not UPSTASH_REDIS_REST_TOKEN:
    raise RuntimeError("Upstash Redis credentials not set in environment variables.")

HEADERS = {
    "Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"
}

async def store_chat_message(user_id: str, question: str, answer: str):
    key = f"chat_history:{user_id}"
    message = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": question,
        "answer": answer
    }

    async with httpx.AsyncClient() as client:
        await client.post(
            f"{UPSTASH_REDIS_REST_URL}/lpush/{key}",
            headers=HEADERS,
            json={"value": json.dumps(message)}
        )

async def get_chat_history(user_id: str, limit: int = 50):
    key = f"chat_history:{user_id}"

    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{UPSTASH_REDIS_REST_URL}/lrange/{key}/0/{limit - 1}",
            headers=HEADERS
        )
        if res.status_code == 200:
            data = res.json()
            return [json.loads(item) for item in data.get("result", [])]
        else:
            return []
