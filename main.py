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
pipeline = LlamaCpp(
    model_path="mistral-7b-instruct-v0.1.Q2_K.gguf",
    n_ctx=4086,
    n_batch=64,
    n_gpu_layers=35, 
    verbose=False,
)
embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# --- State ---
vector_store = None
chat_history = []
category_history = []

# --- Endpoint: Main Chat with Optional Images ---
@app.post("/ask")
async def ask_endpoint(
    message: str = Form(...),
    context: Optional[str] = Form(""),
    images: Optional[List[UploadFile]] = File(None),
):
    global vector_store

    user_input = message.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Empty input")

    # --- Save Uploaded Images ---
    saved_image_paths = []
    if images:
        os.makedirs("uploaded_images", exist_ok=True)
        for image in images:
            image_path = os.path.join("uploaded_images", image.filename)
            with open(image_path, "wb") as f:
                shutil.copyfileobj(image.file, f)
            saved_image_paths.append(image_path)

    # --- Step 1: Categorize the Input ---
    category = categorize_question(user_input, pipeline)
    category_history.append(category)

    # Debug prints here:
    print(f"Received message: {message}")
    print(f"Detected category: {category}")

    # --- Step 2: Route to Agent (with image paths if applicable) ---
    response = route_to_agent(
        category, user_input, pipeline, context, image_paths=saved_image_paths
    )

    # --- Step 3: Save to Vector Store ---
    doc = Document(page_content=f"Q: {user_input}\nA: {response}")
    if vector_store is None:
        vector_store = FAISS.from_documents([doc], embedder)
    else:
        vector_store.add_documents([doc])

    # --- Step 4: Record Chat History ---
    chat_history.append({
        "user": user_input,
        "response": response,
        "category": category
    })

    return {
        "message": user_input,
        "category": category,
        "response": response,
        "chat_history": chat_history  # sent to frontend
    }
