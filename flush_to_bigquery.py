import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import bigquery
import httpx

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_ID")
TABLE_ID = os.getenv("BQ_TABLE_ID")

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

if not (PROJECT_ID and DATASET_ID and TABLE_ID):
    raise RuntimeError("BigQuery environment variables must be set.")

if not (UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN):
    raise RuntimeError("Upstash Redis credentials must be set.")

HEADERS = {
    "Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"
}

client = bigquery.Client()

async def scan_all_keys(match_pattern: str):
    """Scan all Redis keys matching a pattern."""
    cursor = "0"
    all_keys = []
    async with httpx.AsyncClient() as client:
        while True:
            res = await client.get(
                f"{UPSTASH_REDIS_REST_URL}/scan/{cursor}?match={match_pattern}&count=100",
                headers=HEADERS,
            )
            if res.status_code != 200:
                print(f"[{datetime.utcnow().isoformat()}] Redis SCAN failed: {res.text}")
                break
            data = res.json()
            cursor = data.get("cursor")
            keys = data.get("result", [])
            all_keys.extend(keys)
            if cursor == "0":
                break
    return all_keys

async def get_chat_history(user_id: str):
    key = f"chat_history:{user_id}"
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{UPSTASH_REDIS_REST_URL}/lrange/{key}/0/-1",
            headers=HEADERS,
        )
        if res.status_code == 200:
            data = res.json()
            return [json.loads(item) for item in data.get("result", [])]
        else:
            print(f"[{datetime.utcnow().isoformat()}] Failed to fetch Redis data for {user_id}: {res.text}")
            return []

async def clear_chat_history(user_id: str):
    key = f"chat_history:{user_id}"
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{UPSTASH_REDIS_REST_URL}/ltrim/{key}/1/0",
            headers=HEADERS,
        )
        if res.status_code == 200:
            print(f"[{datetime.utcnow().isoformat()}] Cleared Redis chat history for {user_id}")
        else:
            print(f"[{datetime.utcnow().isoformat()}] Failed to clear Redis data for {user_id}: {res.text}")

async def flush_user_history(user_id: str):
    history = await get_chat_history(user_id)
    if not history:
        print(f"[{datetime.utcnow().isoformat()}] [{user_id}] No chat history to flush.")
        return

    rows_to_insert = [
        {
            "user_id": user_id,
            "timestamp": item["timestamp"],
            "question": item["question"],
            "answer": item["answer"],
        }
        for item in history
    ]

    table_ref = client.dataset(DATASET_ID).table(TABLE_ID)
    errors = client.insert_rows_json(table_ref, rows_to_insert)

    if errors:
        print(f"[{datetime.utcnow().isoformat()}] [{user_id}] Failed to insert into BigQuery: {errors}")
    else:
        print(f"[{datetime.utcnow().isoformat()}] [{user_id}] Successfully flushed {len(rows_to_insert)} rows to BigQuery.")
        await clear_chat_history(user_id)

async def main():
    keys = await scan_all_keys("chat_history:*")
    if not keys:
        print(f"[{datetime.utcnow().isoformat()}] No chat history keys found in Redis.")
        return

    user_ids = [key.split("chat_history:")[1] for key in keys if key.startswith("chat_history:")]
    for user_id in user_ids:
        try:
            await flush_user_history(user_id)
        except Exception as e:
            print(f"[{datetime.utcnow().isoformat()}] Error flushing user {user_id}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
