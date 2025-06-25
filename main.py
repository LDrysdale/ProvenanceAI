import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from langchain_community.llms import LlamaCpp
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

from agents.router import route_to_agent
from agents.utils import categorize_question
import shutil
import os

# --- Setup logger ---
logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)

# Formatter with timestamp, level, filename, line no, and message
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Info+ to console
console_handler.setFormatter(formatter)

# File handler (all logs DEBUG+)
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# --- Initialize FastAPI ---
app = FastAPI()

# --- Enable CORS for frontend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust to match your frontend port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Load models ---
try:
    pipeline = LlamaCpp(
        model_path="mistral-7b-instruct-v0.1.Q2_K.gguf",
        n_ctx=4086,
        n_batch=64,
        n_gpu_layers=35,
        verbose=False,
    )
    logger.info("LlamaCpp model loaded successfully")
except Exception:
    logger.error("Failed to load LlamaCpp model", exc_info=True)
    raise

embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
logger.info("Embedder loaded successfully")

# --- State ---
vector_store = None
chat_history = []
category_history = []

@app.post("/ask")
async def ask_endpoint(
    message: str = Form(...),
    context: Optional[str] = Form(""),
    images: Optional[List[UploadFile]] = File(None),
):
    global vector_store

    user_input = message.strip()
    if not user_input:
        logger.warning("Empty input received at /ask endpoint")
        raise HTTPException(status_code=400, detail="Empty input")

    # Save uploaded images
    saved_image_paths = []
    if images:
        os.makedirs("uploaded_images", exist_ok=True)
        for image in images:
            try:
                image_path = os.path.join("uploaded_images", image.filename)
                with open(image_path, "wb") as f:
                    shutil.copyfileobj(image.file, f)
                saved_image_paths.append(image_path)
                logger.info(f"Saved uploaded image: {image.filename}")
            except Exception:
                logger.error(f"Error saving image {image.filename}", exc_info=True)

    try:
        # Step 1: Categorize the input
        category = categorize_question(user_input, pipeline)
        category_history.append(category)
        logger.info(f"Categorized input: '{user_input}' as '{category}'")

        # Step 2: Route to agent
        response = route_to_agent(
            category, user_input, pipeline, context, image_paths=saved_image_paths
        )
        logger.info(f"Agent response generated for category '{category}'")

        # Step 3: Save to vector store
        doc = Document(page_content=f"Q: {user_input}\nA: {response}")
        if vector_store is None:
            vector_store = FAISS.from_documents([doc], embedder)
            logger.info("Initialized vector store with first document")
        else:
            vector_store.add_documents([doc])
            logger.debug("Added new document to vector store")

        # Step 4: Record chat history
        chat_history.append({
            "user": user_input,
            "response": response,
            "category": category,
        })
        logger.debug("Chat history updated")

    except Exception:
        logger.error("Error during ask_endpoint processing", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return {
        "message": user_input,
        "category": category,
        "response": response,
        "chat_history": chat_history,
    }
