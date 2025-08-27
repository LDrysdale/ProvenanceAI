# diary_history.py

import os
import json
import httpx
from google.cloud import bigquery

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")
HEADERS = {"Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"}

async def get_diary_history(user_id: str, chat_id: str, limit: int = 20):
    # --- Redis ---
    redis_key = f"chat_history:{user_id}:{chat_id}"
    redis_history = []
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{UPSTASH_REDIS_REST_URL}/lrange/{redis_key}/0/{limit-1}", headers=HEADERS)
        if res.status_code == 200:
            data = res.json()
            for item in data.get("result", []):
                try:
                    record = json.loads(item)
                    if record.get("activityCategory") == "diary":
                        redis_history.append(record)
                except json.JSONDecodeError:
                    continue

    # --- BigQuery ---
    bq_client = bigquery.Client()
    query = f"""
        SELECT diaryEntry, diaryDate, createdAt, chat_id, chat_subject, activityCategory
        FROM `{os.getenv("BQ_PROJECT")}.{os.getenv("BQ_DATASET")}.chat_history`
        WHERE user_id = @user_id
          AND chat_id = @chat_id
          AND activityCategory = 'diary'
        ORDER BY createdAt DESC
        LIMIT @limit
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
            bigquery.ScalarQueryParameter("chat_id", "STRING", chat_id),
            bigquery.ScalarQueryParameter("limit", "INT64", limit)
        ]
    )
    bigquery_history = []
    for row in bq_client.query(query, job_config=job_config).result():
        bigquery_history.append({
            "diaryEntry": row.diaryEntry,
            "diaryDate": row.diaryDate,
            "createdAt": row.createdAt.isoformat() if hasattr(row.createdAt, "isoformat") else str(row.createdAt),
            "chat_id": row.chat_id,
            "chat_subject": row.chat_subject,
            "activityCategory": row.activityCategory
        })

    # --- Merge + sort ---
    combined_history = redis_history + bigquery_history
    combined_history.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

    return combined_history[:limit]
