from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.llms import LlamaCpp
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

from agents.router import route_to_agent
from agents.utils import categorize_question  # Updated import

app = FastAPI()

class AskRequest(BaseModel):
    message: str
    context: str = ""

class AskResponse(BaseModel):
    message: str
    category: str
    response: str

pipeline = LlamaCpp(
    model_path="mistral-7b-instruct-v0.1.Q2_K.gguf",
    n_ctx=2048,
    verbose=False
)
embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = None
chat_history = []
category_history = []

@app.post("/ask", response_model=AskResponse)
def ask_endpoint(request: AskRequest):
    global vector_store

    user_input = request.message.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Empty input")

    # Step 1: Categorize using few-shot
    category = categorize_question(user_input, pipeline)
    category_history.append(category)

    # Step 2: Route to the appropriate agent
    response = route_to_agent(category, user_input, pipeline, request.context)

    # Step 3: Save to vector store
    combined_text = f"Q: {user_input}\nA: {response}"
    doc = Document(page_content=combined_text)

    if vector_store is None:
        vector_store = FAISS.from_documents([doc], embedder)
    else:
        vector_store.add_documents([doc])

    # Step 4: Record full chat log
    chat_history.append({
        "q": user_input,
        "a": response,
        "category": category
    })

    return AskResponse(
        message=user_input,
        category=category,
        response=response
    )
