# main.py

import logging
import os
import re
import aiofiles
import shutil
import uuid
from typing import List, Optional
from datetime import datetime
import json

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Depends
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from langchain_community.llms import LlamaCpp
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from gemini_model import gemini_generate

from agents.router import route_to_agent
from agents.utils import categorize_question

from redis_chat_history import get_chat_history, store_diary_activity

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

import httpx

from pinecone_query import query_pinecone
from pinecone_upsert import upsert_to_pinecone

# --- Configuration ---

USE_LOCAL_DATA = os.getenv("USE_LOCAL_DATA", "0") == "1"
MOCK_USERS_FILE = os.getenv("MOCK_USERS_FILE", "tests/datasets/mock_users.json")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
RATE_LIMIT = os.getenv("RATE_LIMIT", "5/minute")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_FILE_TYPES = os.getenv("ALLOWED_FILE_TYPES", "image/png,image/jpeg").split(",")

FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "credentials/firebase-adminsdk.json")
MODEL_PATH = os.getenv("MODEL_PATH", "mistral-7b-instruct-v0.1.Q2_K.gguf")

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

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

# --- Role-Based Access Decorator ---
def require_role(required_roles: List[str]):
    def role_checker(request: Request):
        role = request.headers.get("X-User-Role")
        if role not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return {"role": role}
    return role_checker

# --- Utility Functions for Input Sanitization ---
def sanitize_input(text: str) -> str:
    clean = re.sub(r"[^\x20-\x7E\n\r\t]", "", text)
    return clean[:500].strip()

def sanitize_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "_", os.path.basename(name))

async def save_upload_file(upload_file: UploadFile, destination: str):
    async with aiofiles.open(destination, 'wb') as out_file:
        while content := await upload_file.read(1024):
            await out_file.write(content)
    logger.info(f"Saved file: {destination}")

def validate_upload_file(upload_file: UploadFile):
    if upload_file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(400, detail=f"Unsupported file type: {upload_file.content_type}")

# --- Firebase Auth Token Verification ---
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

security = HTTPBearer()

async def get_user_id_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token["uid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired Firebase token")

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
            f"{UPSTASH_REDIS_REST_URL}/rpush/{key}",
            headers={"Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"},
            content=json.dumps(record),
        )
    if response.status_code != 200:
        raise Exception(f"Failed to store chat message in Redis: {response.text}")

# --- API Endpoints ---

@app.get("/session/me")
async def get_current_user(request: Request):
    """
    Get current authenticated user's session info.

    Headers:
        - X-User-Id: Firebase UID
        - X-User-Email: Email of the authenticated user
        - X-User-Role: Role of the user (e.g., admin, user)

    Returns:
        JSON object with user_id, email, and role.
    """
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
    message: str = Form(...),
    context: Optional[str] = Form(""),
    images: Optional[List[UploadFile]] = File(None),
    user_id: str = Depends(get_user_id_from_token),
    chat_id: Optional[str] = Form(None),
    chat_subject: Optional[str] = Form("General"),
):
    """
    Submit a user question to the AI agent, with optional images and context.

    Request:
        - message (str): User's question
        - context (Optional[str]): Additional context from client
        - images (Optional[List[UploadFile]]): Optional image files
        - chat_id (Optional[str]): Existing chat session (or new if blank)
        - chat_subject (Optional[str]): Subject label (e.g., "Therapy", "Career")

    Returns:
        - message: User's original message
        - category: Detected category of the question
        - response: AI-generated response
        - chat_id: Session ID (existing or newly generated)
        - chat_subject: Provided subject label
    """
    user_input = sanitize_input(message)
    if not user_input:
        raise HTTPException(400, detail="Empty input")

    saved_image_paths = []
    if images:
        os.makedirs("uploaded_images", exist_ok=True)
        for image in images:
            contents = await image.read()
            if len(contents) > MAX_FILE_SIZE:
                raise HTTPException(400, detail=f"File too large: {image.filename}")
            await image.seek(0)
            validate_upload_file(image)
            path = os.path.join("uploaded_images", sanitize_filename(image.filename))
            await save_upload_file(image, path)
            saved_image_paths.append(path)

    if not chat_id:
        chat_id = str(uuid.uuid4())

    try:
        category = categorize_question(user_input, gemini_generate)

        redis_key = f"chat_history:{user_id}:{chat_id}"
        redis_history = await get_chat_history(redis_key, limit=10)
        redis_context = format_chat_history_as_context(redis_history)

        pinecone_results = query_pinecone(user_id, user_input, top_k=3)
        pinecone_context = "\n\n".join([res["prompt"] + "\n" + res["answer"] for res in pinecone_results])

        combined_context = "\n\n".join([redis_context, pinecone_context, context or ""])

        response_text = route_to_agent(
            category, user_input, gemini_generate, combined_context.strip(), image_paths=saved_image_paths
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
    limit: int = 50,
    user_id: str = Depends(get_user_id_from_token),
    chat_id: Optional[str] = None
):
    """
    Fetch a user's past chat messages, either for a session or all combined.

    Query Parameters:
        - limit (int): Number of messages to return (default 50)
        - chat_id (Optional[str]): If provided, return only that session's history

    Returns:
        JSON containing user_id, optional chat_id, and message history list
    """
    key = f"chat_history:{user_id}:{chat_id}" if chat_id else f"chat_history:{user_id}"
    history = await get_chat_history(key, limit)
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
    """
    Log a diary entry or delete it from Redis.

    Body (JSON):
        - chat_id: ID of associated chat
        - diary_entry: Diary content
        - diary_status: Either "Entry" to add or "Deletion" to remove
        - diary_date: Date of diary note

    Returns:
        { "success": True } on completion
    """
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
    """
    Permanently delete a chat session for a given user.

    Body (JSON):
        - session_id: ID of the session to delete

    Returns:
        { "status": "deleted", "session_id": "..." }

    Raises:
        - 400 if session_id is missing
        - 500 if Redis deletion fails
    """
    try:
        data = await request.json()
        session_id = data.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session_id")

        key = f"chat_history:{user_id}:{session_id}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{UPSTASH_REDIS_REST_URL}/del/{key}",
                headers={"Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"}
            )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to delete session in Redis")

        return {"status": "deleted", "session_id": session_id}

    except Exception as e:
        logger.error("Delete chat failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete chat session")
