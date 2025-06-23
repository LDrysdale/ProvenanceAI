from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware  # ✅ import CORS
from pydantic import BaseModel
from typing import List
from langchain_community.llms import LlamaCpp
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

from agents.router import route_to_agent
from agents.utils import categorize_question
import shutil
import os

# ✅ Initialize app
app = FastAPI()

# ✅ Add CORS middleware right after app creation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Or "*" for all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = LlamaCpp(model_path="mistral-7b-instruct-v0.1.Q2_K.gguf", n_ctx=2048, verbose=False)
embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = None
chat_history = []
category_history = []

@app.post("/ask")
async def ask_endpoint(
    message: str = Form(...),
    context: str = Form(""),
    images: List[UploadFile] = File([]),
):
    global vector_store

    user_input = message.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Empty input")

    # Save uploaded images to disk (optional, for image merging agent, etc.)
    saved_image_paths = []
    os.makedirs("uploaded_images", exist_ok=True)
    for image in images:
        image_path = os.path.join("uploaded_images", image.filename)
        with open(image_path, "wb") as f:
            shutil.copyfileobj(image.file, f)
        saved_image_paths.append(image_path)

    # Step 1: Categorize
    category = categorize_question(user_input, pipeline)
    category_history.append(category)

    # Step 2: Route to appropriate agent (pass image paths if needed)
    response = route_to_agent(category, user_input, pipeline, context, image_paths=saved_image_paths)

    # Step 3: Save Q&A to vector store
    combined_text = f"Q: {user_input}\nA: {response}"
    doc = Document(page_content=combined_text)

    if vector_store is None:
        vector_store = FAISS.from_documents([doc], embedder)
    else:
        vector_store.add_documents([doc])

    # Step 4: Record chat log
    chat_history.append({"q": user_input, "a": response, "category": category})

    return {
        "message": user_input,
        "category": category,
        "response": response,
    }
