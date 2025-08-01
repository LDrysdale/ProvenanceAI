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
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

from agents.router import route_to_agent
from agents.utils import categorize_question

from redis_chat_history import get_chat_history, store_diary_activity

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

import httpx

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
VECTOR_STORE_DIR = "./data/vector_store"

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

# --- Rate limiter ---
limiter = Limiter(key_func=get_remote_address)

# --- Logging ---
logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
file_handler = logging.FileHandler("app.log")
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# --- FastAPI app ---
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Load LLM ---
try:
    pipeline = LlamaCpp(
        model_path=MODEL_PATH,
        n_ctx=4086,
        n_batch=64,
        n_gpu_layers=35,
        verbose=False,
    )
    logger.info("LlamaCpp model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load LlamaCpp model: {e}")
    raise RuntimeError("Failed to initialize language model")

# --- Load embedder ---
try:
    embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    logger.info("Embedder loaded successfully")
except Exception as e:
    logger.error(f"Failed to load embedder: {e}")
    raise RuntimeError("Failed to initialize embedding model")

# --- Vector store ---
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
vector_store: Optional[FAISS] = None

def persist_vector_store():
    if vector_store:
        try:
            vector_store.save_local(VECTOR_STORE_DIR)
            logger.info("Vector store persisted.")
        except Exception as e:
            logger.error(f"Persist error: {e}")

def load_vector_store():
    global vector_store
    try:
        vector_store = FAISS.load_local(VECTOR_STORE_DIR, embedder)
        logger.info("Vector store loaded.")
    except Exception as e:
        logger.warning("No vector store found or failed to load.")
        vector_store = None

def delete_vector_store():
    try:
        if os.path.exists(VECTOR_STORE_DIR):
            shutil.rmtree(VECTOR_STORE_DIR)
        os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
        global vector_store
        vector_store = None
        logger.info("Vector store reset.")
    except Exception as e:
        logger.error(f"Failed to delete vector store: {e}")

load_vector_store()

# --- Role-based access ---
def require_role(required_roles: List[str]):
    def role_checker(request: Request):
        role = request.headers.get("X-User-Role")
        if role not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return {"role": role}
    return role_checker

# --- Sanitization ---
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

# --- Firebase Token ---
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

# --- Chat history helper ---
def format_chat_history_as_context(history: List[dict], max_turns: int = 5) -> str:
    context_lines = []
    for turn in history[-max_turns:]:
        q = turn.get("question", "")
        a = turn.get("answer", "")
        context_lines.append(f"User: {q}\nAI: {a}")
    return "\n".join(context_lines)

# --- Store chat ---
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
    global vector_store
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
        category = categorize_question(user_input, pipeline)

        redis_key = f"chat_history:{user_id}:{chat_id}"
        redis_history = await get_chat_history(redis_key, limit=10)
        redis_context = format_chat_history_as_context(redis_history)

        pinecone_context = ""
        if vector_store is not None:
            try:
                docs = vector_store.similarity_search(user_input, k=3)
                if docs:
                    pinecone_context = "\n\n".join([doc.page_content for doc in docs])
            except Exception as e:
                logger.warning(f"Vector search failed or vector store empty: {e}")
                pinecone_context = ""
        else:
            # Vector store not loaded or empty
            pinecone_context = ""

        combined_context = "\n\n".join([redis_context, pinecone_context, context or ""])

        response_text = route_to_agent(
            category, user_input, pipeline, combined_context.strip(), image_paths=saved_image_paths
        )

        doc = Document(page_content=f"Q: {user_input}\nA: {response_text}")
        if vector_store is None:
            vector_store = FAISS.from_documents([doc], embedder)
        else:
            vector_store.add_documents([doc])
        persist_vector_store()

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
    diary_status: str
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
                f"{UPSTASH_REDIS_REST_URL}/del/{key}",
                headers={"Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"}
            )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to delete session in Redis")

        return {"status": "deleted", "session_id": session_id}

    except Exception as e:
        logger.error("Delete chat failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete chat session")


# Example of role check usage (not removing, just example):
# @app.get("/admin_only")
# async def admin_only_endpoint(role_data=Depends(require_role(["admin"]))):
#     return {"message": "Welcome, admin!"}
