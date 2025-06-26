# Main.py
import logging
import os
import re
import aiofiles
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from langchain_community.llms import LlamaCpp
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

from agents.router import route_to_agent
from agents.utils import categorize_question

import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Environment config ---
RATE_LIMIT = os.getenv("RATE_LIMIT", "5/minute")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", "5")) * 1024 * 1024  # 5MB default
ALLOWED_FILE_TYPES = os.getenv("ALLOWED_FILE_TYPES", "image/png,image/jpeg").split(",")

# --- Rate limiter setup ---
limiter = Limiter(key_func=get_remote_address)

# --- Logger setup ---
logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.DEBUG)
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

# --- Load language model ---
try:
    pipeline = LlamaCpp(
        model_path="mistral-7b-instruct-v0.1.Q2_K.gguf",
        n_ctx=4086,
        n_batch=64,
        n_gpu_layers=35,
        verbose=False,
    )
    logger.info("LlamaCpp model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load LlamaCpp model: {e}")
    raise RuntimeError("Failed to initialize language model")

# --- Load embedding model ---
try:
    embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    logger.info("Embedder loaded successfully")
except Exception as e:
    logger.error(f"Failed to load embedder: {e}")
    raise RuntimeError("Failed to initialize embedding model")

# --- Vector store setup ---
VECTOR_STORE_DIR = "./data/vector_store"
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

vector_store = None  # type: Optional[FAISS]

def persist_vector_store():
    global vector_store
    if vector_store:
        try:
            vector_store.save_local(VECTOR_STORE_DIR)
            logger.info("Vector store persisted to disk.")
        except Exception as e:
            logger.error(f"Failed to persist vector store: {e}")

def load_vector_store():
    global vector_store
    index_path = os.path.join(VECTOR_STORE_DIR, "index.faiss")
    if os.path.exists(index_path):
        try:
            vector_store = FAISS.load_local(VECTOR_STORE_DIR, embedder)
            logger.info("Vector store loaded from disk.")
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            vector_store = None
    else:
        logger.warning("No vector store found on disk to load.")
        vector_store = None

def delete_vector_store():
    global vector_store
    try:
        if os.path.exists(VECTOR_STORE_DIR):
            shutil.rmtree(VECTOR_STORE_DIR)
            logger.info("Vector store deleted from disk.")
        os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
        vector_store = None
    except Exception as e:
        logger.error(f"Failed to delete vector store: {e}")

load_vector_store()

# --- Input sanitization helpers ---
def sanitize_input(user_input: str) -> str:
    """
    Sanitize user input by removing control characters and limiting length.
    """
    sanitized = re.sub(r"[^\x20-\x7E\n\r\t]", "", user_input)  # Remove control chars except newline/tab
    max_length = 500
    if len(sanitized) > max_length:
        logger.warning(f"Input truncated to {max_length} characters.")
        sanitized = sanitized[:max_length]
    sanitized = sanitized.strip()
    return sanitized

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and disallow unsafe characters.
    """
    filename = os.path.basename(filename)
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    return filename

async def save_upload_file(upload_file: UploadFile, destination: str):
    """
    Asynchronously save uploaded file to disk in chunks to prevent large memory usage.
    """
    try:
        async with aiofiles.open(destination, 'wb') as out_file:
            while content := await upload_file.read(1024):
                await out_file.write(content)
        logger.info(f"File saved to {destination}")
    except Exception as e:
        logger.error(f"Failed to save file {upload_file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

def validate_upload_file(upload_file: UploadFile):
    """
    Validate uploaded file type and size.
    """
    if upload_file.content_type not in ALLOWED_FILE_TYPES:
        logger.warning(f"Unsupported file type upload attempt: {upload_file.content_type}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {upload_file.content_type}. Allowed types: {ALLOWED_FILE_TYPES}"
        )

# --- API Endpoint ---
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
        logger.warning("Empty or invalid input received at /ask endpoint")
        raise HTTPException(status_code=400, detail="Invalid or empty input")

    saved_image_paths = []
    if images:
        os.makedirs("uploaded_images", exist_ok=True)
        for image in images:
            # Validate file size (UploadFile does not have size attribute directly, so read)
            contents = await image.read()
            if len(contents) > MAX_FILE_SIZE:
                logger.warning(f"File too large: {image.filename}")
                raise HTTPException(status_code=400, detail=f"File too large: {image.filename}")
            # Reset read pointer for save
            await image.seek(0)

            validate_upload_file(image)

            sanitized_filename = sanitize_filename(image.filename)
            image_path = os.path.join("uploaded_images", sanitized_filename)

            await save_upload_file(image, image_path)
            saved_image_paths.append(image_path)
            logger.info(f"Saved uploaded image: {sanitized_filename}")

    try:
        # Categorize input
        category = categorize_question(user_input, pipeline)
        logger.info(f"Categorized input: '{user_input}' as '{category}'")

        # Route to appropriate agent
        response = route_to_agent(
            category, user_input, pipeline, context, image_paths=saved_image_paths
        )
        logger.info(f"Agent response generated for category '{category}'")

        # Save Q&A to vector store
        doc = Document(page_content=f"Q: {user_input}\nA: {response}")
        if vector_store is None:
            vector_store = FAISS.from_documents([doc], embedder)
            logger.info("Initialized vector store with first document")
        else:
            vector_store.add_documents([doc])
            logger.debug("Added new document to vector store")

        persist_vector_store()

    except Exception as e:
        logger.error("Error during ask_endpoint processing", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return {
        "message": user_input,
        "category": category,
        "response": response,
    }
