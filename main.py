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
from agents.utils import categorize_question

from redis_chat_history import get_chat_history, store_diary_activity

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

import httpx

from pinecone_query import query_pinecone
from pinecone_upsert import upsert_to_pinecone

from gemini_model import gemini_generate


# --- Configuration ---

USE_LOCAL_DATA = os.getenv("USE_LOCAL_DATA", "0") == "1"
MOCK_USERS_FILE = os.getenv("MOCK_USERS_FILE", "tests/datasets/mock_users.json")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
RATE_LIMIT = os.getenv("RATE_LIMIT", "5/minute")

FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "credentials/firebase-adminsdk.json")

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

# Enable CORS for specified frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Embedding Model ---
try:
    embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    logger.info("Embedder loaded successfully")
except Exception as e:
    logger.error(f"Failed to load embedder: {e}")
    raise RuntimeError("Failed to initialize embedding model")

# --- Firebase Auth Token Verification ---
security = HTTPBearer()

async def get_user_id_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token["uid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired Firebase token")

# --- Utility Functions for Input Sanitization ---
def sanitize_input(text: str) -> str:
    clean = re.sub(r"[^\x20-\x7E\n\r\t]", "", text)
    return clean[:500].strip()

# --- Format Chat History into Context Window ---
def format_chat_history_as_context(history: List[dict], max_turns: int = 5) -> str:
    context_lines = []
    for turn in history[-max_turns:]:
        q = turn.get("question", "")
        a = turn.get("answer", "")
        context_lines.append(f"User: {q}\nAI: {a}")
    return "\n".join(context_lines)

# --- Store Chat Message in Redis ---
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
            f"{os.getenv('UPSTASH_REDIS_REST_URL')}/rpush/{key}",
            headers={"Authorization": f"Bearer {os.getenv('UPSTASH_REDIS_REST_TOKEN')}"},
            content=json.dumps(record),
        )
    if response.status_code != 200:
        raise Exception(f"Failed to store chat message in Redis: {response.text}")

# --- Pydantic model for /ask JSON input ---
class AskRequest(BaseModel):
    message: str
    context: Optional[str] = ""
    chat_id: Optional[str] = None
    chat_subject: Optional[str] = "General"

# --- API Endpoints ---

@app.get("/session/me")
async def get_current_user(request: Request):
    user_id = request.headers.get("X-User-Id")
    user_email = request.headers.get("X-User-Email")
    user_role = request.headers.get("X-User-Role")
    if not user_id or not user_email or not user_role:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing user headers")
    return {"user_id": user_id, "email": user_email, "role": user_role}

@app.post("/ask")
@limiter.limit(RATE_LIMIT)
async def ask_endpoint(
    request: Request,
    data: AskRequest,
    user_id: str = Depends(get_user_id_from_token),
):
    """
    Submit a user question to the AI agent.

    JSON Body:
        - message (str): User's question
        - context (Optional[str]): Additional context
        - chat_id (Optional[str]): Existing chat session ID or new if blank
        - chat_subject (Optional[str]): Subject label

    Returns:
        - message: sanitized user message
        - category: detected category
        - response: AI generated response
        - chat_id: session ID
        - chat_subject: subject label
    """
    user_input = sanitize_input(data.message)
    if not user_input:
        raise HTTPException(400, detail="Empty input")

    chat_id = data.chat_id or str(uuid.uuid4())
    chat_subject = data.chat_subject or "General"

    try:
        category = categorize_question(user_input, gemini_generate)

        # Option A: NO chat history context
        redis_context = ""

        # Option B: if you want chat history as context, pass proper args:
        # redis_history = await get_chat_history(user_id, chat_id, limit=10)
        # redis_context = format_chat_history_as_context(redis_history)


        pinecone_results = query_pinecone(user_id, user_input, top_k=3)
        pinecone_context = "\n\n".join([res["prompt"] + "\n" + res["answer"] for res in pinecone_results])

        combined_context = "\n\n".join([redis_context, pinecone_context, data.context or ""]).strip()

        response_text = route_to_agent(
            category, user_input, gemini_generate, combined_context
        )

        vector_id = str(uuid.uuid4())
        await upsert_to_pinecone(user_id, chat_id, user_input, response_text, vector_id)

        try:
            await store_chat_message(user_id, user_input, response_text, chat_id, chat_subject)
        except Exception as redis_exc:
            logger.error(f"Failed to store chat message in Redis: {redis_exc}")

    except Exception as e:
        logger.error("Ask endpoint failed", exc_info=True)
        raise HTTPException(500, detail="Internal Server Error")

    return {
        "message": user_input,
        "category": category,
        "response": response_text,
        "chat_id": chat_id,
        "chat_subject": chat_subject
    }

@app.get("/chat/history")
async def fetch_chat_history(
    limit: int = 20,
    user_id: str = Depends(get_user_id_from_token),
    chat_id: Optional[str] = None
):
    key = f"chat_history:{user_id}:{chat_id}" if chat_id else f"chat_history:{user_id}"
    history = await get_chat_history(user_id=user_id, chat_id=chat_id, limit=limit)
    return {
        "user_id": user_id,
        "chat_id": chat_id,
        "history": history
    }

class DiaryEntryIn(BaseModel):
    chat_id: str
    diary_entry: str
    diary_status: str  # "Entry" or "Deletion"
    diary_date: str

@app.post("/api/diary")
async def diary_endpoint(
    data: DiaryEntryIn,
    user_id: str = Depends(get_user_id_from_token),
):
    if data.diary_status not in ("Entry", "Deletion"):
        raise HTTPException(status_code=400, detail="Invalid diary_status")
    try:
        await store_diary_activity(
            user_id=user_id,
            chat_id=data.chat_id,
            diary_entry=data.diary_entry,
            diary_status=data.diary_status,
            diary_date=data.diary_date,
        )
    except Exception as e:
        logger.error(f"Failed to store diary activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to store diary activity")
    return {"success": True}

@app.post("/api/delete_chat")
async def delete_chat_session(
    request: Request,
    user_id: str = Depends(get_user_id_from_token)
):
    try:
        data = await request.json()
        session_id = data.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session_id")

        key = f"chat_history:{user_id}:{session_id}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{os.getenv('UPSTASH_REDIS_REST_URL')}/del/{key}",
                headers={"Authorization": f"Bearer {os.getenv('UPSTASH_REDIS_REST_TOKEN')}"}
            )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to delete session in Redis")

        return {"status": "deleted", "session_id": session_id}

    except Exception as e:
        logger.error("Delete chat failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete chat session")
