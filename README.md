# RAG FastAPI Backend

Minimal Retrieval-Augmented Generation backend using FastAPI, LangChain-community, Wikipedia, and LlamaCpp.

## Setup

# 1. Go to your project folder
cd C:\Users\leodr\Desktop\ProvenanceAI

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment (PowerShell)
.\venv\Scripts\Activate

# 4. Install requirements & Sentence Transformers (if needed)
pip install -r requirements.txt
pip install sentence-transformers


# 5. Download NLTK sentence tokenizer
python -c "import nltk; nltk.download('punkt')"

# 6. Run the FastAPI server
uvicorn main:app --reload --port 8000

