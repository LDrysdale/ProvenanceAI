# main.py

import logging
import os

from dotenv import load_dotenv
load_dotenv()  # ⬅️ This loads the .env file into os.environ

import re
import aiofiles
import shutil
from typing import List, Optional

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

from redis_chat_history import store_chat_message, get_chat_history  # ⬅️ New import

# --- Configuration constants ---
USE_LOCAL_DATA = False
RATE_LIMIT = "5/minute"
ALLOWED_ORIGINS = ["http://localhost:5173"]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_FILE_TYPES = ["image/png", "image/jpeg"]
MODEL_PATH = "mistral-7b-instruct-v0.1.Q2_K.gguf"
VECTOR_STORE_DIR = "./data/vector_store"

# --- Rate limiter ---
limiter = Limiter(key_func=get_remote_address)

# --- Logging ---
logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
file_handler = logging.FileHandler("app.log")
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# --- FastAPI setup ---
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

# --- Sanitization helpers ---
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

# --- API Endpoints ---

@app.get("/session/me")
async def get_current_user(request: Request):
    user_id = request.headers.get("X-User-Id")
    user_email = request.headers.get("X-User-Email")
    user_role = request.headers.get("X-User-Role")
    if not user_id or not user_email or not user_role:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing user headers")
    return {
        "user_id": user_id,
        "email": user_email,
        "role": user_role
    }

@app.post("/ask")
@limiter.limit(RATE_LIMIT)
async def ask_endpoint(
    request: Request,
    message: str = Form(...),
    context: Optional[str] = Form(""),
    images: Optional[List[UploadFile]] = File(None),
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

    try:
        category = categorize_question(user_input, pipeline)
        response_text = route_to_agent(
            category, user_input, pipeline, context, image_paths=saved_image_paths
        )
        doc = Document(page_content=f"Q: {user_input}\nA: {response_text}")
        if vector_store is None:
            vector_store = FAISS.from_documents([doc], embedder)
        else:
            vector_store.add_documents([doc])
        persist_vector_store()

        # Store to Redis ⬇️
        user_id = request.headers.get("X-User-Id")
        if user_id:
            await store_chat_message(user_id, user_input, response_text)

    except Exception as e:
        logger.error("Ask endpoint failed", exc_info=True)
        raise HTTPException(500, detail="Internal Server Error")

    return {
        "message": user_input,
        "category": category,
        "response": response_text,
    }

@app.get("/chat/history")
async def fetch_chat_history(request: Request, limit: int = 50):
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing user ID")

    history = await get_chat_history(user_id, limit)
    return {
        "user_id": user_id,
        "history": history
    }
