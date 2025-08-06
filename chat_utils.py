
from typing import List
from datetime import datetime
import json
import httpx
import os

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")


def format_chat_history_as_context(history: List[dict], max_turns: int = 5) -> str:
    context_lines = []
    for turn in history[-max_turns:]:
        q = turn.get("question", "")
        a = turn.get("answer", "")
        context_lines.append(f"User: {q}\nAI: {a}")
    return "\n".join(context_lines)


async def store_chat_message(user_id, question, answer, chat_id, chat_subject):
    key = f"chat_history:{user_id}:{chat_id}"
    now_iso = datetime.utcnow().isoformat()
    record = {
        "question": question,
        "answer": answer,
        "createdAt": now_iso,
        "chat_id": chat_id,
        "chat_subject": chat_subject,
        "activityCategory": "Chat",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{UPSTASH_REDIS_REST_URL}/rpush/{key}",
            headers={"Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"},
            content=json.dumps(record),
        )
    if response.status_code != 200:
        raise Exception(f"Failed to store chat message in Redis: {response.text}")
