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
pip install fastapi uvicorn
pip install clip
pip install opencv-python
pip install segment_anything
pip install diffusers
pip install torchvision
pip install python-multipart
pip install slowapi
pip install aiofiles
pip install pytest
pip install firebase-admin
pip install streamlit

# 5. Download NLTK sentence tokenizer
python -c "import nltk; nltk.download('punkt')"

# 6. Run the FastAPI server
uvicorn main:app --reload --port 8000


# 7. Create the React server (if it doesn't exist)
npx create-react-app frontend

# 8. Install react dependencies
npm install react-scripts
npm install react-dropzone


# 9. Run react server
cd frontend
npm start



package.json corrections
 rm -rf node_modules 
rm package-lock.json
npm install


