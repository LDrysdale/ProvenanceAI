# main.py

import logging
import os
import re
import uuid
from typing import List, Optional
from datetime import datetime
import json

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from langchain_community.embeddings import HuggingFaceEmbeddings

from agents.router import route_to_agent
from agents.agent_categorization import categorize_question

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

import httpx

from pinecone_query import query_pinecone
from pinecone_upsert import upsert_to_pinecone, analyze_with_gemini

from gemini_model import gemini_generate

from chat_history import get_chat_history, store_diary_activity, store_ideaboard_activity, store_chat_message
from diary_history import get_diary_history
from ideaboard_history import get_ideaboard_history

from datetime import timedelta

from google.cloud import bigquery

# Initialize BigQuery client
bq_client = bigquery.Client()

from pinecone import Pinecone

# --- Configuration ---
USE_LOCAL_DATA = os.getenv("USE_LOCAL_DATA", "0") == "1"
MOCK_USERS_FILE = os.getenv("MOCK_USERS_FILE", "tests/datasets/mock_users.json")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
RATE_LIMIT = os.getenv("RATE_LIMIT", "5/minute")
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "credentials/firebase-adminsdk.json")


PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
PINECONE_ENV = os.getenv("PINECONE_ENV")
pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
index = pc.Index(PINECONE_INDEX_NAME)

# --- Firebase Initialization ---
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

# --- Rate Limiter Setup ---
limiter = Limiter(key_func=get_remote_address)

# --- Logging Configuration ---
logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
file_handler = logging.FileHandler("app.log")
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# --- FastAPI Application ---
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global sync tracking ---
last_sync_times = {
    "diary": {},
    "ideaboard": {}
}
SYNC_INTERVAL = timedelta(minutes=30)

def can_run_sync(user_id: str, section: str):
    now = datetime.utcnow()
    last_sync = last_sync_times[section].get(user_id)

    if last_sync and now - last_sync < SYNC_INTERVAL:
        return False, {
            "status": "recent",
            "last_sync": last_sync.isoformat(),
            "next_sync_available": (last_sync + SYNC_INTERVAL).isoformat()
        }

    # Allow sync and record timestamp
    last_sync_times[section][user_id] = now
    return True, {"status": "due", "last_sync": now.isoformat()}


# --- Embedding Model ---
try:
    embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    logger.info("Embedder loaded successfully")
except Exception as e:
    logger.error(f"Failed to load embedder: {e}")
    raise RuntimeError("Failed to initialize embedding model")

# --- Firebase Auth ---
security = HTTPBearer()
async def get_user_id_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token["uid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired Firebase token")

# --- Utility Functions ---
def sanitize_input(text: str) -> str:
    clean = re.sub(r"[^\x20-\x7E\n\r\t]", "", text)
    return clean[:500].strip()

def format_chat_history_as_context(history: List[dict], max_turns: int = 5) -> str:
    context_lines = []
    for turn in history[-max_turns:]:
        q = turn.get("question", "")
        a = turn.get("answer", "")
        context_lines.append(f"User: {q}\nAI: {a}")
    return "\n".join(context_lines)

# --- Store Chat Activity ---
async def store_chat_message(user_id, question, answer, chat_id, chat_subject, timestamp):
    key = f"chat_history:{user_id}:{chat_id}"
    record = {
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "createdAt": timestamp,
        "updated_at": timestamp,
        "chat_id": chat_id,
        "chat_subject": chat_subject,
        "activityCategory": "chat",
        "timezone": None,
        "flushed_at": None
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{os.getenv('UPSTASH_REDIS_REST_URL')}/rpush/{key}",
            headers={"Authorization": f"Bearer {os.getenv('UPSTASH_REDIS_REST_TOKEN')}"},
            content=json.dumps(record),
        )
    if response.status_code != 200:
        raise Exception(f"Failed to store chat message in Redis: {response.text}")

# --- Store Diary Activity ---
async def store_diary_activity(user_id, chat_id, diary_entry, diary_status, diary_date):
    key = f"diary_history:{user_id}:{chat_id}"
    timestamp = datetime.utcnow().isoformat()
    record = {
        "user_id": user_id,
        "createdAt": timestamp,
        "updated_at": timestamp,
        "chat_id": chat_id,
        "activityCategory": "diary",
        "entry_title": diary_date,
        "entry_text": diary_entry,
        "timezone": None,
        "flushed_at": None,
        "word_count": len(diary_entry.split()) if diary_entry else 0
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{os.getenv('UPSTASH_REDIS_REST_URL')}/rpush/{key}",
            headers={"Authorization": f"Bearer {os.getenv('UPSTASH_REDIS_REST_TOKEN')}"},
            content=json.dumps(record),
        )
    if response.status_code != 200:
        raise Exception(f"Failed to store diary activity in Redis: {response.text}")

# --- Store Ideaboard Activity ---
async def store_ideaboard_activity(user_id, chat_id, entry_title, entry_text, x, y, width, height):
    key = f"ideaboard_history:{user_id}:{chat_id}"
    timestamp = datetime.utcnow().isoformat()
    record = {
        "user_id": user_id,
        "createdAt": timestamp,
        "updated_at": timestamp,
        "chat_id": chat_id,
        "activityCategory": "ideaboard",
        "entry_title": entry_title,
        "entry_text": entry_text,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "timezone": None,
        "flushed_at": None,
        "word_count": len(entry_text.split()) if entry_text else 0
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{os.getenv('UPSTASH_REDIS_REST_URL')}/rpush/{key}",
            headers={"Authorization": f"Bearer {os.getenv('UPSTASH_REDIS_REST_TOKEN')}"},
            content=json.dumps(record),
        )
    if response.status_code != 200:
        raise Exception(f"Failed to store ideaboard activity in Redis: {response.text}")

# --- Pydantic Models ---
class AskRequest(BaseModel):
    message: str
    context: Optional[str] = ""
    chat_id: Optional[str] = None
    chat_subject: Optional[str] = "General"

class DiaryEntryIn(BaseModel):
    chat_id: str
    diary_entry: str
    diary_status: str  # "Entry" or "Deletion"
    diary_date: str

class IdeaboardEntryIn(BaseModel):
    chat_id: str
    entry_title: str
    entry_text: str
    x: float
    y: float
    width: float
    height: float

# --- API Endpoints ---
@app.get("/session/me")
async def get_current_user(request: Request):
    user_id = request.headers.get("X-User-Id")
    user_email = request.headers.get("X-User-Email")
    user_role = request.headers.get("X-User-Role")
    if not user_id or not user_email or not user_role:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing user headers")
    return {"user_id": user_id, "email": user_email, "role": user_role}

# --- Chat Endpoint ---
@app.post("/ask")
@limiter.limit(RATE_LIMIT)
async def ask_endpoint(request: Request, data: AskRequest, user_id: str = Depends(get_user_id_from_token)):
    user_input = sanitize_input(data.message)
    if not user_input:
        raise HTTPException(400, detail="Empty input")
    chat_id = data.chat_id or str(uuid.uuid4())
    chat_subject = data.chat_subject or "General"
    now_iso = datetime.utcnow().isoformat()
    try:
        category = categorize_question(user_input, gemini_generate)
        redis_context = ""
        pinecone_results = query_pinecone(user_id, user_input, top_k=3)
        pinecone_context = "\n\n".join([res["prompt"] + "\n" + res["answer"] for res in pinecone_results])
        combined_context = "\n\n".join([redis_context, pinecone_context, data.context or ""]).strip()
        response_text = route_to_agent(category, user_input, gemini_generate, combined_context)
        vector_id = str(uuid.uuid4())
        await upsert_to_pinecone(user_id, chat_id, user_input, response_text, vector_id)
        try:
            await store_chat_message(user_id, user_input, response_text, chat_id, chat_subject, now_iso)
        except Exception as redis_exc:
            logger.error(f"Failed to store chat message in Redis: {redis_exc}")
    except Exception as e:
        logger.error("Ask endpoint failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
    return {
        "message": user_input,
        "category": category,
        "response": response_text,
        "chat_id": chat_id,
        "chat_subject": chat_subject,
        "createdAt": now_iso,
        "updated_at": now_iso
    }

# --- Chat History ---
@app.get("/chat/history")
async def fetch_chat_history(
    limit: int = 20,
    user_id: str = Depends(get_user_id_from_token),
    chat_id: Optional[str] = None
):
    history = await get_chat_history(user_id=user_id, chat_id=chat_id, limit=limit)
    return {
        "user_id": user_id,
        "chat_id": chat_id,
        "history": history
    }

# --- Diary Endpoint ---
@app.post("/api/diary")
async def diary_endpoint(data: DiaryEntryIn, user_id: str = Depends(get_user_id_from_token)):
    if data.diary_status not in ("Entry", "Deletion"):
        raise HTTPException(status_code=400, detail="Invalid diary_status")

    try:
        # Store in Redis
        await store_diary_activity(user_id, data.chat_id, data.diary_entry, data.diary_status, data.diary_date)

        # Store in Pinecone (only if not deletion)
        if data.diary_status == "Entry":
            vector_id = str(uuid.uuid4())
            await upsert_to_pinecone(
                user_id=user_id,
                entry_type="diary",
                text=data.diary_entry,
                vector_id=vector_id,
                chat_id=data.chat_id
            )
    except Exception as e:
        logger.error(f"Failed to process diary activity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process diary activity")

    return {"success": True}


@app.get("/diary/history")
async def fetch_diary_history(
    user_id: str = Depends(get_user_id_from_token),
    chat_id: str = None,
    limit: int = 20
):
    history = await get_diary_history(user_id=user_id, chat_id=chat_id, limit=limit)
    return {"user_id": user_id, "chat_id": chat_id, "history": history}

# --- Ideaboard Endpoint ---
@app.post("/api/ideaboard")
async def ideaboard_endpoint(data: IdeaboardEntryIn, user_id: str = Depends(get_user_id_from_token)):
    try:
        # Store in Redis
        entry_id = getattr(data, "entry_id", None)
        entry_id = await store_ideaboard_activity(
            user_id,
            data.chat_id,
            data.entry_title,
            data.entry_text,
            data.x,
            data.y,
            data.width,
            data.height,
            entry_id=entry_id
        )

        # Store in Pinecone
        vector_id = str(uuid.uuid4())
        await upsert_to_pinecone(
            user_id=user_id,
            entry_type="ideaboard",
            text=data.entry_text,
            vector_id=vector_id,
            chat_id=data.chat_id
        )

    except Exception as e:
        logger.error(f"Failed to process ideaboard activity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process ideaboard activity")

    return {"success": True, "entry_id": entry_id}


@app.get("/ideaboard/history")
async def fetch_ideaboard_history(
    user_id: str = Depends(get_user_id_from_token),
    chat_id: str = None,
    limit: int = 20
):
    history = await get_ideaboard_history(user_id=user_id, chat_id=chat_id, limit=limit)
    return {"user_id": user_id, "chat_id": chat_id, "history": history}




# --- Delete Chat ---
@app.post("/api/delete_chat")
async def delete_chat_session(request: Request, user_id: str = Depends(get_user_id_from_token)):
    try:
        data = await request.json()
        session_id = data.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session_id")
        key = f"chat_history:{user_id}:{session_id}"
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{os.getenv('UPSTASH_REDIS_REST_URL')}/del/{key}",
                                         headers={"Authorization": f"Bearer {os.getenv('UPSTASH_REDIS_REST_TOKEN')}"})
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to delete session in Redis")
        return {"status": "deleted", "session_id": session_id}
    except Exception as e:
        logger.error("Delete chat failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete chat session")


from datetime import datetime, timedelta

# --- Global sync timers ---
last_sync_times = {
    "diary": {},
    "ideaboard": {}
}
SYNC_INTERVAL = timedelta(minutes=30)


# --- Sync Diary to Pinecone ---
@app.post("/api/sync/diary-to-pinecone")
async def sync_diary_to_pinecone(
    user_id: str = Depends(get_user_id_from_token),
    chat_id: str = None
):
    # --- Timer check ---
    now = datetime.utcnow()
    last_sync = last_sync_times["diary"].get(user_id)
    if last_sync and now - last_sync < SYNC_INTERVAL:
        return {
            "status": "recent",
            "last_sync": last_sync.isoformat(),
            "next_sync_available": (last_sync + SYNC_INTERVAL).isoformat()
        }
    last_sync_times["diary"][user_id] = now

    try:
        # --- Step 1: Fetch from Redis ---
        redis_entries = await get_diary_history(user_id=user_id, chat_id=chat_id, limit=1000)

        # --- Step 2: Fetch from BigQuery ---
        query = f"""
            SELECT chat_id, entry_text, entry_title, createdAt
            FROM `{os.getenv('BIGQUERY_PROJECT')}.{os.getenv('BIGQUERY_DATASET')}.diary_entries`
            WHERE user_id = @user_id
            { "AND chat_id = @chat_id" if chat_id else "" }
        """
        query_params = [bigquery.ScalarQueryParameter("user_id", "STRING", user_id)]
        if chat_id:
            query_params.append(bigquery.ScalarQueryParameter("chat_id", "STRING", chat_id))

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        results = bq_client.query(query, job_config=job_config).result()
        bq_entries = [dict(row) for row in results]

        # --- Step 3: Combine entries ---
        all_entries = redis_entries + bq_entries

        # --- Step 4: Check Pinecone & Upsert missing entries ---
        for entry in all_entries:
            vector_id = f"{entry['chat_id']}_{entry['createdAt']}"
            res = index.fetch(ids=[vector_id])
            if vector_id in res.vectors:
                continue  # Already exists

            # Enrich with sentiment/mood
            analysis = analyze_with_gemini(entry["entry_text"])
            sentiment = analysis.get("sentiment", "neutral")
            mood_tags = analysis.get("mood_tags", [])

            # Upsert to Pinecone
            await upsert_to_pinecone(
                user_id=user_id,
                chat_id=entry["chat_id"],
                text=entry["entry_text"],
                vector_id=vector_id,
                entry_type="diary",
                sentiment=sentiment,
                mood_tags=mood_tags
            )

        return {
            "status": "ok",
            "last_sync": now.isoformat(),
            "total_entries_checked": len(all_entries)
        }

    except Exception as e:
        logger.error("Sync diary to Pinecone failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to sync diary entries")


# --- Sync Ideaboard to Pinecone ---
@app.post("/api/sync/ideaboard-to-pinecone")
async def sync_ideaboard_to_pinecone(
    user_id: str = Depends(get_user_id_from_token),
    chat_id: str = None
):
    # --- Timer check ---
    now = datetime.utcnow()
    last_sync = last_sync_times["ideaboard"].get(user_id)
    if last_sync and now - last_sync < SYNC_INTERVAL:
        return {
            "status": "recent",
            "last_sync": last_sync.isoformat(),
            "next_sync_available": (last_sync + SYNC_INTERVAL).isoformat()
        }
    last_sync_times["ideaboard"][user_id] = now

    try:
        # --- Step 1: Fetch from Redis ---
        redis_entries = await get_ideaboard_history(user_id=user_id, chat_id=chat_id, limit=1000)

        # --- Step 2: Fetch from BigQuery ---
        query = f"""
            SELECT chat_id, entry_text, entry_title, x, y, width, height, createdAt
            FROM `{os.getenv('BIGQUERY_PROJECT')}.{os.getenv('BIGQUERY_DATASET')}.ideaboard_entries`
            WHERE user_id = @user_id
            { "AND chat_id = @chat_id" if chat_id else "" }
        """
        query_params = [bigquery.ScalarQueryParameter("user_id", "STRING", user_id)]
        if chat_id:
            query_params.append(bigquery.ScalarQueryParameter("chat_id", "STRING", chat_id))

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        results = bq_client.query(query, job_config=job_config).result()
        bq_entries = [dict(row) for row in results]

        # --- Step 3: Combine entries ---
        all_entries = redis_entries + bq_entries

        # --- Step 4: Check Pinecone & Upsert missing entries ---
        for entry in all_entries:
            vector_id = f"{entry['chat_id']}_{entry['createdAt']}"
            res = index.fetch(ids=[vector_id])
            if vector_id in res.vectors:
                continue  # Already exists

            # Enrich with sentiment/mood
            analysis = analyze_with_gemini(entry["entry_text"])
            sentiment = analysis.get("sentiment", "neutral")
            mood_tags = analysis.get("mood_tags", [])

            # Upsert to Pinecone
            await upsert_to_pinecone(
                user_id=user_id,
                chat_id=entry["chat_id"],
                text=entry["entry_text"],
                vector_id=vector_id,
                entry_type="ideaboard",
                sentiment=sentiment,
                mood_tags=mood_tags
            )

        return {
            "status": "ok",
            "last_sync": now.isoformat(),
            "total_entries_checked": len(all_entries)
        }

    except Exception as e:
        logger.error("Sync ideaboard to Pinecone failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to sync ideaboard entries")
