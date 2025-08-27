import os
import json
import httpx
from datetime import datetime
from typing import List, Optional

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")
HEADERS = {"Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"}


async def store_ideaboard_activity(
    user_id: str,
    chat_id: str,
    entry_title: str,
    entry_text: str,
    x: float,
    y: float,
    width: float,
    height: float,
    entry_id: Optional[str] = None,  # optional for updates
):
    key = f"ideaboard_history:{user_id}:{chat_id}"
    timestamp = datetime.utcnow().isoformat()
    entry_id = entry_id or str(uuid.uuid4())  # generate if not provided

    record = {
        "user_id": user_id,
        "createdAt": timestamp,
        "updated_at": timestamp,
        "chat_id": chat_id,
        "activityCategory": "ideaboard",
        "entry_id": entry_id,
        "entry_title": entry_title,
        "entry_text": entry_text,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "timezone": None,
        "flushed_at": None,
        "word_count": len(entry_text.split()) if entry_text else 0,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{UPSTASH_REDIS_REST_URL}/rpush/{key}",
            headers=HEADERS,
            content=json.dumps(record),
        )
    if response.status_code != 200:
        raise RuntimeError(f"Failed to store ideaboard activity: {response.text}")

    return entry_id  # return ID so frontend can reuse for updates


async def get_ideaboard_history(user_id: str, chat_id: str, limit: int = 50) -> List[dict]:
    key = f"ideaboard_history:{user_id}:{chat_id}"
    redis_history = []

    async with httpx.AsyncClient() as client:
        res = await client.get(f"{UPSTASH_REDIS_REST_URL}/lrange/{key}/0/{limit - 1}", headers=HEADERS)
        if res.status_code == 200:
            data = res.json()
            for item in data.get("result", []):
                try:
                    redis_history.append(json.loads(item))
                except json.JSONDecodeError:
                    continue

    # Deduplicate by entry_id, keep latest updated_at
    latest_entries = {}
    for entry in redis_history:
        eid = entry.get("entry_id")
        if eid:
            existing = latest_entries.get(eid)
            if not existing or entry["updated_at"] > existing["updated_at"]:
                latest_entries[eid] = entry

    # Sort by updated_at descending
    sorted_entries = sorted(latest_entries.values(), key=lambda x: x["updated_at"], reverse=True)
    return sorted_entries[:limit]
