import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import bigquery
import httpx
import uuid

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_ID")
CHAT_TABLE_ID = os.getenv("BQ_CHAT_TABLE_ID")
DIARY_TABLE_ID = os.getenv("BQ_DIARY_TABLE_ID")
IDEABOARD_TABLE_ID = os.getenv("BQ_IDEABOARD_TABLE_ID")

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

if not (PROJECT_ID and DATASET_ID and CHAT_TABLE_ID and DIARY_TABLE_ID and IDEABOARD_TABLE_ID):
    raise RuntimeError("BigQuery environment variables must be set.")

if not (UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN):
    raise RuntimeError("Upstash Redis credentials must be set.")

HEADERS = {"Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"}
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


async def fetch_redis_list(key: str):
    """Fetch all items from a Redis list."""
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{UPSTASH_REDIS_REST_URL}/lrange/{key}/0/-1", headers=HEADERS)
        if res.status_code == 200:
            data = res.json()
            items = []
            for item in data.get("result", []):
                try:
                    items.append(json.loads(item))
                except json.JSONDecodeError:
                    continue
            return items
        else:
            print(f"[{datetime.utcnow().isoformat()}] Failed to fetch Redis data for {key}: {res.text}")
            return []


async def clear_redis_list(key: str):
    """Delete a Redis list."""
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{UPSTASH_REDIS_REST_URL}/del/{key}", headers=HEADERS)
        if res.status_code == 200:
            print(f"[{datetime.utcnow().isoformat()}] Cleared Redis key {key}")
        else:
            print(f"[{datetime.utcnow().isoformat()}] Failed to clear Redis key {key}: {res.text}")


async def flush_category(user_id: str, category: str, table_id: str):
    key = f"{category}_history:{user_id}"
    items = await fetch_redis_list(key)
    if not items:
        print(f"[{datetime.utcnow().isoformat()}] [{user_id}] No {category} history to flush.")
        return

    # For ideaboard, deduplicate by entry_id, keep latest
    if category == "ideaboard":
        latest_entries = {}
        for entry in items:
            eid = entry.get("entry_id")
            if eid:
                existing = latest_entries.get(eid)
                if not existing or entry["updated_at"] > existing["updated_at"]:
                    latest_entries[eid] = entry
        items = list(latest_entries.values())

    # Prepare rows for BigQuery
    rows_to_insert = []
    for item in items:
        row = {"user_id": user_id, "createdAt": item.get("createdAt")}
        row.update(item)  # include all fields
        rows_to_insert.append(row)

    table_ref = client.dataset(DATASET_ID).table(table_id)
    errors = client.insert_rows_json(table_ref, rows_to_insert)
    if errors:
        print(f"[{datetime.utcnow().isoformat()}] [{user_id}] Failed to insert {category} into BigQuery: {errors}")
    else:
        print(f"[{datetime.utcnow().isoformat()}] [{user_id}] Successfully flushed {len(rows_to_insert)} {category} rows to BigQuery.")
        await clear_redis_list(key)


async def flush_user(user_id: str):
    for category, table_id in [("chat", CHAT_TABLE_ID), ("diary", DIARY_TABLE_ID), ("ideaboard", IDEABOARD_TABLE_ID)]:
        try:
            await flush_category(user_id, category, table_id)
        except Exception as e:
            print(f"[{datetime.utcnow().isoformat()}] Error flushing {category} for user {user_id}: {e}")


async def main():
    keys = await scan_all_keys("*_history:*")
    if not keys:
        print(f"[{datetime.utcnow().isoformat()}] No user history keys found in Redis.")
        return

    user_ids = set(key.split("_history:")[1] for key in keys)
    for user_id in user_ids:
        try:
            await flush_user(user_id)
        except Exception as e:
            print(f"[{datetime.utcnow().isoformat()}] Error flushing user {user_id}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
